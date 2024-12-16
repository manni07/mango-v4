# mango_client_py/utils/account_unpacker.py

from solana.publickey import PublicKey
from solana.rpc.types import AccountInfo
from typing import Any, Dict

def unpack_account(pubkey: PublicKey, account_info: AccountInfo) -> Dict[str, Any]:
    # Implementieren Sie die Logik zum Dekodieren der Account-Daten
    # Dies hängt von der spezifischen Struktur der Account-Daten ab
    # Beispielhafte Implementierung:
    return {
        'owner': PublicKey(account_info.owner),
        'data': account_info.data,  # Weitere Dekodierung je nach Bedarf
    }
