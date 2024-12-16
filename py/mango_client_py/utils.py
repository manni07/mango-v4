# mango_client_py/utils.py

from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from spl.token.async_client import AsyncToken
from spl.token.instructions import create_close_account_instruction, create_associated_token_account_idempotent_instruction
from typing import Any, Dict, Optional
from decimal import Decimal

def unpack_account(pubkey: PublicKey, account_info: Any) -> Dict[str, Any]:
    """
    Implementieren Sie die Logik zum Dekodieren der Account-Daten.
    Dies hängt von der spezifischen Struktur der Account-Daten ab.
    """
    # Beispielhafte Implementierung (anpassen nach Bedarf)
    return {
        'owner': PublicKey(account_info.owner),
        'data': account_info.data,  # Weitere Dekodierung je nach Bedarf
    }

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

def to_native(amount: Any, decimals: int) -> int:
    """
    Konvertiert einen Betrag in die native Darstellung basierend auf den Dezimalstellen.
    """
    return int(Decimal(amount) * (10 ** decimals))

# Weitere Hilfsfunktionen können hier hinzugefügt werden
