# mango_client_py/utils/account_creator.py

from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from spl.token.async_client import AsyncToken
from solana.transaction import Transaction
from spl.token.constants import TOKEN_PROGRAM_ID
from typing import Any
from .utils import unpack_account

async def create_account(
    conn: AsyncClient,
    payer: Any,  # Typ anpassen, z.B. AnchorProvider Wallet
    mint: PublicKey,
    owner: PublicKey,
    keypair: Keypair,
) -> None:
    token = AsyncToken(
        conn,
        mint,
        TOKEN_PROGRAM_ID,
        payer,
    )
    await token.create_account(owner, keypair=keypair)
