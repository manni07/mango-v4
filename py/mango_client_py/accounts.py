
# mango_client_py/accounts.py

from typing import Optional, List
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction
from solana.keypair import Keypair
from spl.token.constants import NATIVE_MINT
from spl.token.async_client import AsyncToken
from spl.token.instructions import create_close_account_instruction

from .utils import unpack_account, create_account, to_native
from .types import Group, MangoAccount, TokenIndex, HealthCheckKind, MangoSignatureStatus
from .utils import create_associated_token_account_idempotent_instruction

class Accounts:
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

    # Weitere account-bezogene Methoden folgen hier...
