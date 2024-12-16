# mango_client_py/accounts/mango_account.py

from typing import Optional, List
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction
from solana.keypair import Keypair
from spl.token.constants import NATIVE_MINT
from spl.token.instructions import create_close_account_instruction

from ..utils import unpack_account, create_account, to_native
from ..types import Group, MangoAccount, TokenIndex, HealthCheckKind, MangoSignatureStatus
from ..utils import create_associated_token_account_idempotent_instruction

class MangoAccounts:
    def __init__(self, client):
        self.client = client

    async def create_mango_account(
        self,
        group: Group,
        account_number: Optional[int] = 0,
        name: Optional[str] = '',
        token_count: Optional[int] = 8,
        serum3_count: Optional[int] = 4,
        perp_count: Optional[int] = 4,
        perp_oo_count: Optional[int] = 32,
    ) -> MangoSignatureStatus:
        ix = await self.client.program.methods.account_create(
            account_number,
            token_count,
            serum3_count,
            perp_count,
            perp_oo_count,
            name,
        ).accounts({
            'group': group.public_key,
            'owner': self.client.wallet_pk,
            'payer': self.client.wallet_pk,
        }).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [ix])

    async def expand_mango_account(
        self,
        group: Group,
        account: MangoAccount,
        token_count: int,
        serum3_count: int,
        perp_count: int,
        perp_oo_count: int,
    ) -> MangoSignatureStatus:
        ix = await self.client.program.methods.account_expand(token_count, serum3_count, perp_count, perp_oo_count).accounts({
            'group': group.public_key,
            'account': account.public_key,
            'owner': self.client.wallet_pk,
            'payer': self.client.wallet_pk,
        }).instruction()
        return await self.client.send_and_confirm_transaction_for_group(group, [ix])

    async def account_expand_v2(
        self,
        group: Group,
        account: MangoAccount,
        token_count: int,
        serum3_count: int,
        perp_count: int,
        perp_oo_count: int,
        token_conditional_swap_count: int,
    ) -> MangoSignatureStatus:
        ix = await self.account_expand_v2_ix(
            group,
            account,
            token_count,
            serum3_count,
            perp_count,
            perp_oo_count,
            token_conditional_swap_count,
        )
        return await self.client.send_and_confirm_transaction_for_group(group, [ix])

    async def account_expand_v2_ix(
        self,
        group: Group,
        account: MangoAccount,
        token_count: int,
        serum3_count: int,
        perp_count: int,
        perp_oo_count: int,
        token_conditional_swap_count: int,
    ) -> TransactionInstruction:
        return await self.client.program.methods.account_expand_v2(
            token_count,
            serum3_count,
            perp_count,
            perp_oo_count,
            token_conditional_swap_count,
        ).accounts({
            'group': group.public_key,
            'account': account.public_key,
            'owner': self.client.wallet_pk,
            'payer': self.client.wallet_pk,
        }).instruction()

    async def edit_mango_account(
        self,
        group: Group,
        mango_account: MangoAccount,
        name: Optional[str] = None,
        delegate: Optional[PublicKey] = None,
        temporary_delegate: Optional[PublicKey] = None,
        delegate_expiry: Optional[int] = None,
    ) -> MangoSignatureStatus:
        ix = await self.client.program.methods.account_edit(
            name,
            delegate,
            temporary_delegate,
            delegate_expiry,
        ).accounts({
            'group': group.public_key,
            'account': mango_account.public_key,
            'owner': self.client.wallet_pk,
        }).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [ix])

    async def toggle_mango_account_freeze(
        self,
        group: Group,
        mango_account: MangoAccount,
        freeze: bool,
    ) -> MangoSignatureStatus:
        ix = await self.client.program.methods.account_toggle_freeze(freeze).accounts({
            'group': group.public_key,
            'account': mango_account.public_key,
            'admin': self.client.wallet_pk,
        }).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [ix])

    async def sequence_check_ix(
        self,
        group: Group,
        mango_account: MangoAccount,
    ) -> TransactionInstruction:
        return await self.client.program.methods.sequence_check(mango_account.sequence_number).accounts({
            'group': group.public_key,
            'account': mango_account.public_key,
            'owner': self.client.wallet_pk,
        }).instruction()

    async def health_check_ix(
        self,
        group: Group,
        mango_account: MangoAccount,
        min_health_value: float,
        check_kind: HealthCheckKind,
    ) -> TransactionInstruction:
        health_remaining_accounts: List[PublicKey] = await self.client.accounts.build_health_remaining_accounts(
            group,
            [mango_account],
            [],
            [],
            [],
        )

        return await self.client.program.methods.health_check(min_health_value, check_kind).accounts({
            'group': group.public_key,
            'account': mango_account.public_key,
        }).remaining_accounts([
            {"pubkey": pk, "is_signer": False, "is_writable": False} for pk in health_remaining_accounts
        ]).instruction()

    async def get_mango_account(
        self,
        mango_account_pk: PublicKey,
        load_serum3_oo: bool = False,
    ) -> MangoAccount:
        mango_account = await self.get_mango_account_from_pk(mango_account_pk)
        if load_serum3_oo:
            await mango_account.reload_serum3_open_orders(self.client)
        return mango_account

    async def get_mango_account_from_pk(
        self,
        mango_account_pk: PublicKey,
    ) -> MangoAccount:
        account_info = await self.client.connection.get_account_info(mango_account_pk)
        if account_info is None:
            raise ValueError("MangoAccount not found")
        return self.get_mango_account_from_ai(mango_account_pk, account_info)

    def get_mango_account_from_ai(
        self,
        mango_account_pk: PublicKey,
        account_info: Any,
    ) -> MangoAccount:
        decoded_mango_account = self.client.program.coder.accounts.decode('mangoAccount', account_info.data)
        return MangoAccount.from_account(mango_account_pk, decoded_mango_account)

    async def get_mango_account_with_slot(
        self,
        mango_account_pk: PublicKey,
        load_serum3_oo: bool = False,
    ) -> Optional[Dict[str, Any]]:
        resp = await self.client.program.provider.connection.get_account_info_and_context(mango_account_pk)
        if not resp or not resp.value:
            return None
        mango_account = self.get_mango_account_from_ai(mango_account_pk, resp.value)
        if load_serum3_oo:
            await mango_account.reload_serum3_open_orders(self.client)
        return {'slot': resp.context.slot, 'value': mango_account}

    # Weitere account-bezogene Methoden können hier hinzugefügt werden
