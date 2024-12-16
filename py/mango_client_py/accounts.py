# mango_client_py/accounts.py

from typing import Optional, List
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction
from solana.keypair import Keypair
from spl.token.constants import NATIVE_MINT
from spl.token.instructions import create_close_account_instruction

from .utils import unpack_account, create_account, to_native
from .types import Group, MangoAccount, TokenIndex, HealthCheckKind, MangoSignatureStatus
from .utils import create_associated_token_account_idempotent_instruction

class Accounts:
    def __init__(self, client):
        self.client = client

    # ... bestehende Methoden ...

    async def token_force_withdraw(
        self,
        group: Group,
        mango_account: MangoAccount,
        token_index: TokenIndex,
    ) -> MangoSignatureStatus:
        bank = group.get_first_bank_by_token_index(token_index)
        if not bank.force_withdraw:
            raise ValueError('Bank is not in force-withdraw mode')

        owner_ata_token_account = await get_associated_token_address(
            bank.mint,
            mango_account.owner,
            True,
        )
        alternate_owner_token_account = PublicKey("11111111111111111111111111111111")  # PublicKey.default in solana-py

        pre_instructions: List[TransactionInstruction] = []
        post_instructions: List[TransactionInstruction] = []

        ai = await self.client.connection.get_account_info(owner_ata_token_account)

        # ensure withdraws don't fail with missing ATAs
        if ai is None:
            pre_instructions.append(
                await create_associated_token_account_idempotent_instruction(
                    payer=self.client.wallet_pk,
                    owner=mango_account.owner,
                    mint=bank.mint,
                )
            )

            # wsol case
            if bank.mint == NATIVE_MINT:
                post_instructions.append(
                    create_close_account_instruction(
                        account=owner_ata_token_account,
                        destination=mango_account.owner,
                        authority=mango_account.owner,
                    )
                )
        else:
            account = await unpack_account(owner_ata_token_account, ai)
            # if owner is not same as mango account's owner on the ATA (for whatever reason)
            # then create another token account
            if not account['owner'].equals(mango_account.owner):
                kp = Keypair.generate()
                alternate_owner_token_account = kp.public_key
                await create_account(
                    conn=self.client.connection,
                    payer=self.client.program.provider.wallet,
                    mint=bank.mint,
                    owner=mango_account.owner,
                    keypair=kp,
                )

                # wsol case
                if bank.mint == NATIVE_MINT:
                    post_instructions.append(
                        create_close_account_instruction(
                            account=alternate_owner_token_account,
                            destination=mango_account.owner,
                            authority=mango_account.owner,
                        )
                    )

        ix = await self.client.program.methods.token_force_withdraw().accounts({
            'group': group.public_key,
            'account': mango_account.public_key,
            'bank': bank.public_key,
            'vault': bank.vault,
            'oracle': bank.oracle,
            'ownerAtaTokenAccount': owner_ata_token_account,
            'alternateOwnerTokenAccount': alternate_owner_token_account if alternate_owner_token_account != PublicKey("11111111111111111111111111111111") else owner_ata_token_account,
        }).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [
            *pre_instructions,
            ix,
            *post_instructions,
        ])

    async def token_deregister(
        self,
        group: Group,
        mint_pk: PublicKey,
    ) -> MangoSignatureStatus:
        bank = group.get_first_bank_by_mint(mint_pk)
        admin_pk = self.client.wallet_pk

        dust_vault_pk = await get_associated_token_address(bank.mint, admin_pk)
        ai = await self.client.connection.get_account_info(dust_vault_pk)
        pre_instructions: List[TransactionInstruction] = []
        if ai is None:
            pre_instructions.append(
                await create_associated_token_account_idempotent_instruction(
                    payer=admin_pk,
                    owner=admin_pk,
                    mint=bank.mint,
                )
            )

        ix = await self.client.program.methods.token_deregister().accounts({
            'group': group.public_key,
            'admin': admin_pk,
            'mint_info': group.mint_infos_map_by_token_index.get(bank.token_index).public_key if group.mint_infos_map_by_token_index.get(bank.token_index) else None,
            'dust_vault': dust_vault_pk,
            'sol_destination': admin_pk,
        }).remaining_accounts([
            AccountMeta(pubkey=bank.public_key, is_signer=False, is_writable=True),
            AccountMeta(pubkey=bank.vault, is_signer=False, is_writable=True),
        ]).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [
            *pre_instructions,
            ix,
        ])
