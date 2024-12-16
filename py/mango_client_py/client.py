# mango_client_py/client.py

from anchorpy import Program, Provider
from solana.publickey import PublicKey
from typing import List, Optional, Dict, Any, Callable

from .accounts.mango_account import MangoAccounts
from .accounts.oracles import Oracles
from .accounts.serum3 import Serum3  # Falls Serum3 in einem separaten Modul ist
from .accounts.perp import Perp  # Import des Perp Moduls
from .utils import (
    unpack_account,
    create_new_account,  # Import der neuen create_account Methode
    to_native,
    get_recent_prioritization_fees,
    to_native_sell_per_buy_token_price,
    uniq,
    # Weitere Hilfsfunktionen...
)
from .types import Group, MangoAccount, TokenIndex, HealthCheckKind, MangoSignatureStatus, SYSVAR_INSTRUCTIONS_PUBKEY, RecentPrioritizationFee, U64_MAX_BN, MAX_SAFE_INTEGER
from .utils import send_transaction

class MangoClientOptions:
    def __init__(
        self,
        ids_source: str = 'get-program-accounts',  # 'api', 'static', 'get-program-accounts'
        post_send_tx_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        post_tx_confirmation_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        prioritization_fee: int = 0,
        estimate_fee: bool = False,
        tx_confirmation_commitment: str = 'processed',
        openbook_fees_to_dao: bool = True,
        prepended_global_additional_instructions: Optional[List[Any]] = None,
        multiple_connections: Optional[List[Any]] = None,
        fallback_oracle_config: Any = 'never',  # 'never', 'all', 'dynamic', List[PublicKey]
        turn_off_price_impact_loading: bool = False,
    ):
        self.ids_source = ids_source
        self.post_send_tx_callback = post_send_tx_callback
        self.post_tx_confirmation_callback = post_tx_confirmation_callback
        self.prioritization_fee = prioritization_fee
        self.estimate_fee = estimate_fee
        self.tx_confirmation_commitment = tx_confirmation_commitment
        self.openbook_fees_to_dao = openbook_fees_to_dao
        self.prepended_global_additional_instructions = prepended_global_additional_instructions or []
        self.multiple_connections = multiple_connections or []
        self.fallback_oracle_config = fallback_oracle_config
        self.turn_off_price_impact_loading = turn_off_price_impact_loading

class MangoClient:
    DEFAULT_TOKEN_CONDITIONAL_SWAP_COUNT = 8
    PERP_SETTLE_PNL_CU_LIMIT = 400000
    PERP_SETTLE_FEES_CU_LIMIT = 20000
    SERUM_SETTLE_FUNDS_CU_LIMIT = 65000

    class AccountRetriever:
        Scanning = 0
        Fixed = 1

    def __init__(
        self,
        program: Program,  # Typ anpassen, ggf. aus anchorpy
        program_id: PublicKey,
        cluster: str,  # Entspricht dem Typ `Cluster` in TypeScript
        opts: MangoClientOptions = MangoClientOptions(),
    ):
        self.program = program
        self.program_id = program_id
        self.cluster = cluster
        self.opts = opts

        # Initialize sub-modules
        self.accounts = MangoAccounts(self)
        self.oracles = Oracles(self)
        self.serum3 = Serum3(self)  # Falls Serum3 in einem separaten Modul ist
        self.perp = Perp(self)  # Initialisierung des Perp Moduls

        # Beispiel für die Erhöhung des StackTrace-Limits in Python
        import sys
        sys.setrecursionlimit(1000)  # Anpassen nach Bedarf

    @property
    def connection(self) -> AsyncClient:
        return self.program.provider.connection

    @property
    def wallet_pk(self) -> PublicKey:
        return self.program.provider.wallet.public_key

    async def send_and_confirm_transaction(
        self,
        ixs: List[TransactionInstruction],
        opts: Optional[Dict[str, Any]] = None
    ) -> MangoSignatureStatus:
        """
        Implementiert die Logik zum Senden und Bestätigen der Transaktion.
        """
        opts = opts or {}
        prioritization_fee = opts.get('prioritization_fee', self.opts.prioritization_fee)

        if self.opts.estimate_fee or opts.get('estimate_fee', False):
            prioritization_fee = await self.estimate_prioritization_fee(ixs)
        else:
            prioritization_fee = self.opts.prioritization_fee

        # Senden und Bestätigen der Transaktion
        status = await send_transaction(
            self.program.provider,
            self.opts.prepended_global_additional_instructions + ixs,
            opts.get('alts', []),
            {
                'postSendTxCallback': self.opts.post_send_tx_callback,
                'postTxConfirmationCallback': self.opts.post_tx_confirmation_callback,
                'prioritizationFee': prioritization_fee,
                'txConfirmationCommitment': self.opts.tx_confirmation_commitment,
                'multipleConnections': self.opts.multiple_connections,
            },
        )
        return status

    async def send_and_confirm_transaction_for_group(
        self,
        group: Group,
        ixs: List[TransactionInstruction],
        opts: Optional[Dict[str, Any]] = None
    ) -> MangoSignatureStatus:
        """
        Sendet und bestätigt eine Transaktion für eine bestimmte Gruppe.
        """
        opts = opts or {}
        alts = opts.get('alts') or group.address_lookup_tables_list

        unique_accounts = set(
            [pk.to_base58() for ix in ixs for pk in ix.keys] +
            [ix.program_id.to_base58() for ix in ixs] +
            [x.key.to_base58() for x in alts]
        )
        unique_accounts_count = len(unique_accounts)

        if unique_accounts_count > 64:
            raise ValueError("Max accounts limit exceeded")

        return await self.send_and_confirm_transaction(ixs, {**opts, 'alts': alts })

    async def estimate_prioritization_fee(self, ixs: List[TransactionInstruction]) -> int:
        """
        Implementiert die Logik zur Schätzung der Priorisierungsgebühr.
        """
        # Sammle alle beschreibbaren Konten aus den Anweisungen
        writable_accounts = [
            key.pubkey for ix in ixs for key in ix.keys if key.is_writable
        ]
        unique_writable_accounts = uniq(
            writable_accounts, key=lambda pk: pk.to_base58()
        )[:self.MAX_RECENT_PRIORITY_FEE_ACCOUNTS]

        # Hole die aktuellen Priorisierungsgebühren von der Verbindung
        priority_fees_response = await get_recent_prioritization_fees(
            connection=self.connection,
            locked_writable_accounts=unique_writable_accounts
        )

        if not priority_fees_response:
            return 1

        # Gruppiere die Gebühren nach Slot und behalte die maximale Gebühr pro Slot
        priority_fees_response.sort(key=lambda fee: fee.slot)
        grouped_fees = groupby(priority_fees_response, key=attrgetter('slot'))
        max_fee_by_slot = [
            max(group, key=lambda fee: fee.prioritization_fee)
            for slot, group in grouped_fees
        ]

        # Sortiere die maximalen Gebühren nach Slot von alt zu neu
        max_fee_by_slot.sort(key=lambda fee: fee.slot)

        # Nehme die letzten 20 Gebühren
        recent_fees = max_fee_by_slot[-self.MAX_RECENT_PRIORITY_FEES:]

        # Berechne den Median der letzten 20 Gebühren
        recent_prioritization_fees = [fee.prioritization_fee for fee in recent_fees]
        median_fee = int(math.ceil(median(recent_prioritization_fees)))

        return max(1, median_fee)

    @staticmethod
    def connect(
        provider: Provider,
        cluster: str,  # Entspricht dem Typ `Cluster` in TypeScript
        program_id: PublicKey,
        opts: Optional[MangoClientOptions] = None,
    ) -> 'MangoClient':
        """
        Statische Methode zur Verbindung mit einem bestehenden MangoClient.

        Args:
            provider (Provider): Der Anchor Provider.
            cluster (str): Der Cluster, z.B. 'mainnet-beta'.
            program_id (PublicKey): Die PublicKey des Programms.
            opts (Optional[MangoClientOptions]): Optionale Konfigurationsoptionen.

        Returns:
            MangoClient: Der verbundene MangoClient.
        """
        if opts is None:
            opts = MangoClientOptions()

        client = MangoClient(
            program=Program(idl as MangoV4, program_id, provider),
            program_id=program_id,
            cluster=cluster,
            opts=opts,
        )
        return client

    @staticmethod
    def connect_default(cluster_url: str) -> 'MangoClient':
        """
        Statische Methode zur Verbindung mit einem MangoClient mit Standardparametern.

        Args:
            cluster_url (str): Die URL des Clusters, z.B. 'https://api.mainnet-beta.solana.com'.

        Returns:
            MangoClient: Der verbundene MangoClient.
        """
        idl = Idl.from_json(...)  # Laden Sie Ihr IDL hier korrekt

        options = Provider.default_options()
        connection = AsyncClient(cluster_url, options)
        wallet = Keypair()  # Verwenden Sie ein Wallet mit einem Keypair

        provider = Provider(connection, wallet, options)

        client = MangoClient(
            program=Program(idl, PublicKey("MANGO_PROGRAM_ID"), provider),
            program_id=PublicKey("MANGO_PROGRAM_ID"),
            cluster='mainnet-beta',
            opts=MangoClientOptions(
                ids_source='get-program-accounts',
            ),
        )
        return client

    @staticmethod
    def connect_for_group_name(
        provider: Provider,
        group_name: str,
    ) -> 'MangoClient':
        """
        Statische Methode zur Verbindung mit einem MangoClient basierend auf dem Gruppennamen.

        Args:
            provider (Provider): Der Anchor Provider.
            group_name (str): Der Name der Gruppe.

        Returns:
            MangoClient: Der verbundene MangoClient.
        """
        idl = Idl.from_json(...)  # Laden Sie Ihr IDL hier korrekt

        # Hier müssen Sie die entsprechende PublicKey für die Gruppe basierend auf dem Namen finden
        # Dies könnte eine Mapping-Tabelle sein oder eine API-Abfrage
        group_public_key = PublicKey("GROUP_PUBLIC_KEY_FOR_" + group_name.upper())

        client = MangoClient(
            program=Program(idl, PublicKey("MANGO_PROGRAM_ID"), provider),
            program_id=PublicKey("MANGO_PROGRAM_ID"),
            cluster='mainnet-beta',
            opts=MangoClientOptions(),
        )
        return client
