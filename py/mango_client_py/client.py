# mango_client_py/client.py

from anchorpy import AnchorProvider, Program
from solana.publickey import PublicKey
from typing import List, Optional, Dict, Any
import sys

from .accounts import Accounts
from .oracles import Oracles
from .utils import unpack_account, create_account, to_native
from .types import Group, MangoAccount, TokenIndex, HealthCheckKind, MangoSignatureStatus

class MangoClient:
    def __init__(
        self,
        program: Program,
        program_id: PublicKey,
        cluster: str,
        opts: Any = None,
    ):
        self.program = program
        self.program_id = program_id
        self.cluster = cluster

        # Initialize sub-modules
        self.accounts = Accounts(self)
        self.oracles = Oracles(self)

        # Beispiel für die Erhöhung des StackTrace-Limits in Python
        sys.setrecursionlimit(1000)  # Anpassen nach Bedarf

    @property
    def connection(self):
        return self.program.provider.connection

    @property
    def wallet_pk(self):
        return self.program.provider.wallet.public_key

    async def send_and_confirm_transaction(self, ixs: List[Any], opts: Optional[Dict[str, Any]] = None) -> MangoSignatureStatus:
        # Implementieren Sie die Logik zum Senden und Bestätigen der Transaktion
        pass

    async def send_and_confirm_transaction_for_group(self, group: Group, ixs: List[Any], opts: Optional[Dict[str, Any]] = None) -> MangoSignatureStatus:
        # Implementieren Sie die spezifische Logik für Gruppen-Transaktionen
        pass

    # Weitere allgemeine Methoden können hier hinzugefügt werden

