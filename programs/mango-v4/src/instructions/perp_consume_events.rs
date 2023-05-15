use anchor_lang::prelude::*;
use bytemuck::cast_ref;

use crate::error::MangoError;
use crate::state::*;

use crate::accounts_ix::*;
use crate::logs::{emit_perp_balances, FillLogV2};

/// Load a mango account by key from the list of account infos.
///
/// Message and return Ok() if it's missing, to lock in successful processing
/// of previous events.
///
/// Special handling for testing groups, where events for accounts with bad
/// owners (most likely due to force closure of the account) are being skipped.
macro_rules! load_mango_account {
    ($name:ident, $key:expr, $ais:expr, $group:expr) => {
        let loader = match $ais.iter().find(|ai| ai.key == &$key) {
            None => {
                msg!(
                    "Unable to find {} account {}",
                    stringify!($name),
                    $key.to_string()
                );
                return Ok(false);
            }

            Some(ai) => {
                if $group.is_testing() && ai.owner != &crate::id() {
                    msg!(
                        "Mango account ({}) not owned by mango program",
                        stringify!($name)
                    );
                    return Ok(true);
                }

                let mal: AccountLoader<MangoAccountFixed> = AccountLoader::try_from(ai)?;
                mal
            }
        };
        let mut $name = loader.load_full_mut()?;
    };
}

fn process_event(
    event: &AnyEvent,
    group: &Group,
    group_key: Pubkey,
    perp_market: &mut PerpMarket,
    mango_account_ais: &[AccountInfo],
) -> Result<bool> {
    let perp_market_index = perp_market.perp_market_index;

    match EventType::try_from(event.event_type).map_err(|_| error!(MangoError::SomeError))? {
        EventType::Fill => {
            let fill: &FillEvent = cast_ref(event);

            // handle self trade separately because of rust borrow checker
            if fill.maker == fill.taker {
                load_mango_account!(maker_taker, fill.maker, mango_account_ais, group);
                maker_taker.execute_perp_maker(perp_market_index, perp_market, fill)?;
                maker_taker.execute_perp_taker(perp_market_index, perp_market, fill)?;
                emit_perp_balances(
                    group_key,
                    fill.maker,
                    maker_taker.perp_position(perp_market_index).unwrap(),
                    &perp_market,
                );
            } else {
                load_mango_account!(maker, fill.maker, mango_account_ais, group);
                load_mango_account!(taker, fill.taker, mango_account_ais, group);

                maker.execute_perp_maker(perp_market_index, perp_market, fill)?;
                taker.execute_perp_taker(perp_market_index, perp_market, fill)?;
                emit_perp_balances(
                    group_key,
                    fill.maker,
                    maker.perp_position(perp_market_index).unwrap(),
                    &perp_market,
                );
                emit_perp_balances(
                    group_key,
                    fill.taker,
                    taker.perp_position(perp_market_index).unwrap(),
                    &perp_market,
                );
            }
            emit!(FillLogV2 {
                mango_group: group_key,
                market_index: perp_market_index,
                taker_side: fill.taker_side as u8,
                maker_slot: fill.maker_slot,
                maker_out: fill.maker_out(),
                timestamp: fill.timestamp,
                seq_num: fill.seq_num,
                maker: fill.maker,
                maker_client_order_id: fill.maker_client_order_id,
                maker_fee: fill.maker_fee,
                maker_timestamp: fill.maker_timestamp,
                taker: fill.taker,
                taker_client_order_id: fill.taker_client_order_id,
                taker_fee: fill.taker_fee,
                price: fill.price,
                quantity: fill.quantity,
            });
        }
        EventType::Out => {
            let out: &OutEvent = cast_ref(event);
            load_mango_account!(owner, out.owner, mango_account_ais, group);
            owner.remove_perp_order(out.owner_slot as usize, out.quantity)?;
        }
        EventType::Liquidate => {
            // This is purely for record keeping. Can be removed if program logs are superior
        }
        EventType::AlreadyProcessed => {
            assert!(false); // not valid, must be filtered out before!
        }
    }

    Ok(true)
}

pub fn perp_consume_events(ctx: Context<PerpConsumeEvents>, limit: usize) -> Result<()> {
    let group = ctx.accounts.group.load()?;
    let group_key = ctx.accounts.group.key();

    let limit = std::cmp::min(limit, 8);

    let mut perp_market = ctx.accounts.perp_market.load_mut()?;
    let mut event_queue = ctx.accounts.event_queue.load_mut()?;
    let mango_account_ais = ctx.remaining_accounts;

    let mut processed = 0;

    // Try consuming the top events
    while processed < limit {
        let event = match event_queue.peek_front() {
            None => break,
            Some(e) => e,
        };

        if event.event_type != EventType::AlreadyProcessed as u8 {
            let success = process_event(
                event,
                &group,
                group_key,
                &mut perp_market,
                mango_account_ais,
            )?;
            if !success {
                break;
            }
            processed += 1;
        }

        // consume this event
        event_queue.pop_front()?;
    }

    // Try out-of-order processing the OutEvents for the first passed account
    let first_account_key = mango_account_ais[0].key;
    let first_account_key_bytes: &[u8] = first_account_key.as_ref();
    let mal: AccountLoader<MangoAccountFixed> = AccountLoader::try_from(&mango_account_ais[0])?;
    let mut first_account = mal.load_full_mut()?;

    // NOTE: Iterating all 488 events with this takes around 14k CU
    // when all events are OutEvents but only two have a matching pubkey
    for event in event_queue.iter_mut() {
        if processed >= limit {
            break;
        }
        if event.event_type != EventType::Out as u8 {
            continue;
        }
        let out_event: &mut OutEvent = bytemuck::cast_mut(event);
        let owner_bytes: &[u8] = out_event.owner.as_ref();

        // Two-stage comparison is for performance
        if owner_bytes[0..8] != first_account_key_bytes[0..8]
            || owner_bytes != first_account_key_bytes
        {
            continue;
        }

        // TODO: Function for out event processing (even if tiny)
        first_account.remove_perp_order(out_event.owner_slot as usize, out_event.quantity)?;

        out_event.event_type = EventType::AlreadyProcessed as u8;
        processed += 1;
    }

    Ok(())
}
