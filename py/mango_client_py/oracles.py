# mango_client_py/accounts/oracles.py

from typing import List, Optional
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction
from solana.keypair import Keypair
from spl.token.constants import NATIVE_MINT
from spl.token.instructions import create_close_account_instruction

from ..utils import unpack_account, create_account, to_native
from ..types import Group, StubOracle, MangoSignatureStatus, I80F48
from ..utils import create_associated_token_account_idempotent_instruction

class Oracles:
    def __init__(self, client):
        self.client = client

    async def stub_oracle_set(
        self,
        group: Group,
        oracle_pk: PublicKey,
        price: float,
    ) -> MangoSignatureStatus:
        ix = await self.client.program.methods.stub_oracle_set({'val': I80F48.from_number(price).get_data()}).accounts({
            'group': group.public_key,
            'admin': self.client.wallet_pk,
            'oracle': oracle_pk,
        }).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [ix])

    async def get_stub_oracle(
        self,
        group: Group,
        mint_pk: Optional[PublicKey] = None,
    ) -> List[StubOracle]:
        filters = [
            {
                'memcmp': {
                    'bytes': group.public_key.to_base58(),
                    'offset': 8,
                },
            },
        ]

        if mint_pk:
            filters.append({
                'memcmp': {
                    'bytes': mint_pk.to_base58(),
                    'offset': 40,
                },
            })

        accounts = await self.client.program.account.stub_oracle.all(filters)
        return [StubOracle.from_account(pa.public_key, pa.account) for pa in accounts]

    async def stub_oracle_create(
        self,
        group: Group,
        mint_pk: PublicKey,
        price: float,
    ) -> MangoSignatureStatus:
        stub_oracle = Keypair.generate()
        ix = await self.client.program.methods.stub_oracle_create({'val': I80F48.from_number(price).get_data()}).accounts({
            'group': group.public_key,
            'admin': self.client.wallet_pk,
            'oracle': stub_oracle.public_key,
            'mint': mint_pk,
            'payer': self.client.wallet_pk,
        }).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [ix], {
            'additional_signers': [stub_oracle],
        })

    async def stub_oracle_close(
        self,
        group: Group,
        oracle: PublicKey,
    ) -> MangoSignatureStatus:
        ix = await self.client.program.methods.stub_oracle_close().accounts({
            'group': group.public_key,
            'oracle': oracle,
            'sol_destination': self.client.wallet_pk,
        }).instruction()

        return await self.client.send_and_confirm_transaction_for_group(group, [ix])

    # Weitere oracle-bezogene Methoden können hier hinzugefügt werden
