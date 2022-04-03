use anchor_lang::prelude::*;
use fixed::types::I80F48;

use crate::state::*;

#[derive(Accounts)]
pub struct SetStubOracle<'info> {
    #[account(
        has_one = admin,
    )]
    pub group: AccountLoader<'info, Group>,

    pub admin: Signer<'info>,

    #[account(
        mut,
        has_one = group
    )]
    pub oracle: AccountLoader<'info, StubOracle>,

    #[account(mut)]
    pub payer: Signer<'info>,
}

// TODO: add admin requirement for changing price
pub fn set_stub_oracle(ctx: Context<SetStubOracle>, price: I80F48) -> Result<()> {
    let mut oracle = ctx.accounts.oracle.load_mut()?;
    oracle.price = price;
    oracle.last_updated = Clock::get()?.unix_timestamp;

    Ok(())
}
