# mango_client_py/client.py

from .accounts import Accounts
from .oracles import Oracles

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

    # ... bestehende Methoden ...
