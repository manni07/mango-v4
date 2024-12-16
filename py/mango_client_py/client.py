# mango_client_py/client.py

import asyncio
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass

from anchorpy import Program, Provider, Wallet, Idl
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.transaction import Transaction, TransactionInstruction
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.rpc.types import TxOpts

from .types import (
    Group,
    MangoAccount,
    HealthCheckKind,
    MangoSignatureStatus,
    RecentPrioritizationFee,
    FallbackOracleConfig,
)
from .utils import (
    unpack_account,
    create_new_account,
    to_native,
    get_recent_prioritization_fees,
    to_native_sell_per_buy_token_price,
    uniq,
)
from .accounts.mango_account import MangoAccounts
from .accounts.oracles import Oracles
from .accounts.serum3 import Serum3
from .accounts.perp import Perp

# ----------------------------
# Optionen für den MangoClient
# ----------------------------

@dataclass
class MangoClientOptions:
    ids_source: str = 'get-program-accounts'  # 'api', 'static', 'get-program-accounts'
    post_send_tx_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    post_tx_confirmation_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    prioritization_fee: int = 0
    estimate_fee: bool = False
    tx_confirmation_commitment: Commitment = Commitment('processed')
    openbook_fees_to_dao: bool = True
    prepended_global_additional_instructions: Optional[List[TransactionInstruction]] = None
    multiple_connections: Optional[List[AsyncClient]] = None
    fallback_oracle_config: FallbackOracleConfig = FallbackOracleConfig.NEVER  # 'never', 'all', 'dynamic', List[PublicKey]
    turn_off_price_impact_loading: bool = False

    def __post_init__(self):
        if self.prepended_global_additional_instructions is None:
            self.prepended_global_additional_instructions = []
        if self.multiple_connections is None:
            self.multiple_connections = []

# ----------------------------
# MangoClient Klasse
# ----------------------------

class MangoClient:
    DEFAULT_TOKEN_CONDITIONAL_SWAP_COUNT = 8
    PERP_SETTLE_PNL_CU_LIMIT = 400000
    PERP_SETTLE_FEES_CU_LIMIT = 20000
    SERUM_SETTLE_FUNDS_CU_LIMIT = 65000

    MAX_RECENT_PRIORITY_FEE_ACCOUNTS = 64
    MAX_RECENT_PRIORITY_FEES = 20

    class AccountRetriever:
        Scanning = 0
        Fixed = 1

    def __init__(
        self,
        program: Program,
        program_id: PublicKey,
        cluster: str,
        opts: MangoClientOptions = MangoClientOptions(),
    ):
        self.program = program
        self.program_id = program_id
        self.cluster = cluster
        self.opts = opts

        # Initialize Submodule
        self.accounts = MangoAccounts(self)
        self.oracles = Oracles(self)
        self.serum3 = Serum3(self)
        self.perp = Perp(self)

        # Beispielhafte Erhöhung des StackTrace-Limits in Python
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
        Sendet eine Transaktion und bestätigt sie.

        Args:
            ixs (List[TransactionInstruction]): Die Anweisungen, die die Transaktion ausmachen.
            opts (Optional[Dict[str, Any]]): Zusätzliche Optionen.

        Returns:
            MangoSignatureStatus: Der Status der Transaktionssignatur.
        """
        opts = opts or {}
        prioritization_fee = opts.get('prioritization_fee', self.opts.prioritization_fee)

        if self.opts.estimate_fee or opts.get('estimate_fee', False):
            prioritization_fee = await self.estimate_prioritization_fee(ixs)
        else:
            prioritization_fee = self.opts.prioritization_fee

        # Erstellen der Transaktion
        transaction = Transaction()
        transaction.instructions = self.opts.prepended_global_additional_instructions + ixs

        # Hinzufügen Priorisierungsgebühr als zusätzliche Anweisung, falls erforderlich
        if prioritization_fee > 0:
            # Beispielhafte Hinzufügung einer Priorisierungsgebühr-Anweisung
            # Dies muss entsprechend Ihrer Anwendung implementiert werden
            pass

        # Senden und Bestätigen der Transaktion
        try:
            signature = await self.program.provider.send(transaction, opts=TxOpts(skip_preflight=False, preflight_commitment=self.opts.tx_confirmation_commitment))
            status = MangoSignatureStatus(signature=signature, status="success")
        except Exception as e:
            status = MangoSignatureStatus(signature="", status=str(e))

        # Callback nach dem Senden der Transaktion
        if self.opts.post_send_tx_callback:
            self.opts.post_send_tx_callback(status)

        # Bestätigen der Transaktion
        try:
            await self.program.provider.connection.confirm_transaction(signature, self.opts.tx_confirmation_commitment)
            if self.opts.post_tx_confirmation_callback:
                self.opts.post_tx_confirmation_callback(status)
        except Exception as e:
            status.status = f"confirmation_failed: {str(e)}"

        return status

    async def send_and_confirm_transaction_for_group(
        self,
        group: Group,
        ixs: List[TransactionInstruction],
        opts: Optional[Dict[str, Any]] = None
    ) -> MangoSignatureStatus:
        """
        Sendet und bestätigt eine Transaktion für eine bestimmte Gruppe.

        Args:
            group (Group): Die Gruppe, zu der die Transaktion gehört.
            ixs (List[TransactionInstruction]): Die Anweisungen, die die Transaktion ausmachen.
            opts (Optional[Dict[str, Any]]): Zusätzliche Optionen.

        Returns:
            MangoSignatureStatus: Der Status der Transaktionssignatur.
        """
        opts = opts or {}
        alts = opts.get('alts') or group.address_lookup_tables_list

        unique_accounts = set(
            [pk.to_base58() for ix in ixs for pk in ix.keys] +
            [ix.program_id.to_base58() for ix in ixs] +
            [x.to_base58() for x in alts]
        )
        unique_accounts_count = len(unique_accounts)

        if unique_accounts_count > self.MAX_RECENT_PRIORITY_FEE_ACCOUNTS:
            raise ValueError("Max accounts limit exceeded")

        # Optional: Handhaben von Address Lookup Tables (ALTs)
        # Dies hängt von Ihrer Implementierung ab und muss ggf. angepasst werden

        return await self.send_and_confirm_transaction(ixs, {**opts, 'alts': alts })

    async def estimate_prioritization_fee(self, ixs: List[TransactionInstruction]) -> int:
        """
        Schätzt die Priorisierungsgebühr basierend auf den Transaktionsanweisungen.

        Args:
            ixs (List[TransactionInstruction]): Die Anweisungen, die die Transaktion ausmachen.

        Returns:
            int: Geschätzte Priorisierungsgebühr in MikroLamports.
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
        grouped_fees = groupby(priority_fees_response, key=lambda fee: fee.slot)
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

    # ----------------------------
    # Statische Methoden zur Verbindung
    # ----------------------------

    @staticmethod
    def connect(
        provider: Provider,
        cluster: str,
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
            program=provider.program,  # Annahme: provider.program gibt ein Program-Objekt zurück
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
        # Laden Sie das IDL (Interface Definition Language) korrekt
        # Dies muss an Ihre spezifische Implementierung angepasst werden
        # Beispiel: Laden aus einer JSON-Datei
        import json
        import os

        idl_path = os.path.join(os.path.dirname(__file__), 'idl.json')
        with open(idl_path, 'r') as f:
            idl_json = json.load(f)
        idl = Idl.from_json(idl_json)

        # Erstellen Sie das Keypair für das Wallet (hier als Platzhalter ein generiertes Keypair)
        # In der Praxis sollten Sie das Keypair sicher laden
        wallet_keypair = Keypair.generate()
        wallet = Wallet(wallet_keypair)

        # Erstellen Sie den AsyncClient und den Provider
        connection = AsyncClient(cluster_url)
        provider = Provider(connection, wallet, Provider.default_options())

        # Initialisieren Sie das Program-Objekt
        program_id = PublicKey("MANGO_PROGRAM_ID_HIER_EINFÜGEN")  # Ersetzen Sie dies durch Ihre Program ID
        program = Program(idl, program_id, provider)

        # Initialisieren Sie den MangoClient
        client = MangoClient(
            program=program,
            program_id=program_id,
            cluster='mainnet-beta',  # Anpassen nach Bedarf
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
        # Laden Sie das IDL korrekt
        import json
        import os

        idl_path = os.path.join(os.path.dirname(__file__), 'idl.json')
        with open(idl_path, 'r') as f:
            idl_json = json.load(f)
        idl = Idl.from_json(idl_json)

        # Finden Sie die entsprechende Group PublicKey basierend auf dem Namen
        # Dies könnte eine Mapping-Tabelle sein oder eine API-Abfrage
        # Hier als Beispiel eine statische Zuordnung
        group_mapping = {
            "MAINNET": PublicKey("GROUP_PUBLIC_KEY_MAINNET"),
            "DEVNET": PublicKey("GROUP_PUBLIC_KEY_DEVNET"),
            # Fügen Sie weitere Gruppenzuordnungen hinzu
        }

        if group_name.upper() not in group_mapping:
            raise ValueError(f"Unbekannter Gruppenname: {group_name}")

        group_public_key = group_mapping[group_name.upper()]

        # Erstellen Sie das Keypair für das Wallet (hier als Platzhalter ein generiertes Keypair)
        wallet_keypair = Keypair.generate()
        wallet = Wallet(wallet_keypair)

        # Erstellen Sie den AsyncClient und den Provider
        connection = AsyncClient("https://api.mainnet-beta.solana.com")  # Anpassen nach Bedarf
        provider = Provider(connection, wallet, Provider.default_options())

        # Initialisieren Sie das Program-Objekt
        program_id = PublicKey("MANGO_PROGRAM_ID_HIER_EINFÜGEN")  # Ersetzen Sie dies durch Ihre Program ID
        program = Program(idl, program_id, provider)

        # Initialisieren Sie den MangoClient
        client = MangoClient(
            program=program,
            program_id=program_id,
            cluster='mainnet-beta',  # Anpassen nach Bedarf
            opts=MangoClientOptions(
                ids_source='get-program-accounts',
            ),
        )
        return client

    # ----------------------------
    # Weitere Methoden
    # ----------------------------

    # Hier können Sie weitere Methoden hinzufügen, die spezifische Funktionalitäten Ihres Clients implementieren
    # Beispielsweise Methoden zur Verwaltung von Gruppen, Konten, Orders, etc.

    # Beispiel: Methode zum Erstellen eines neuen Kontos
    async def create_account(
        self,
        payer: Keypair,
        program_id: PublicKey,
        space: int,
        lamports: int,
        new_account_keypair: Optional[Keypair] = None,
    ) -> Keypair:
        """
        Erstellt ein neues Solana-Konto.

        Args:
            payer (Keypair): Das Keypair, das die Lamports zur Finanzierung des neuen Kontos bereitstellt.
            program_id (PublicKey): Die PublicKey des Programms, das das neue Konto besitzt.
            space (int): Der Speicherplatz, der dem Konto zugewiesen werden soll (in Bytes).
            lamports (int): Die Menge an Lamports, die dem Konto zugewiesen werden sollen.
            new_account_keypair (Optional[Keypair]): Optionales Keypair für das neue Konto. Wenn None, wird ein neues generiert.

        Returns:
            Keypair: Das Keypair des erstellten Kontos.
        """
        new_account = await create_new_account(
            connection=self.connection,
            payer=payer,
            program_id=program_id,
            space=space,
            lamports=lamports,
            new_account_keypair=new_account_keypair
        )
        return new_account

    # Beispiel: Methode zum Unpacken von Kontodaten
    def unpack_account_data(self, data: bytes, fmt: str) -> Tuple[Any, ...]:
        """
        Entpackt die Rohdaten eines Solana-Kontos basierend auf dem gegebenen Format.

        Args:
            data (bytes): Die Rohdaten des Kontos.
            fmt (str): Das Format der Daten (z.B. Struct-Formatzeichenfolge).

        Returns:
            Tuple[Any, ...]: Die entpackten Daten.
        """
        return unpack_account(data, fmt)

    # Beispiel: Methode zur Berechnung eines Premiums
    def calculate_premium(
        self,
        group: Group,
        buy_bank: Bank,
        sell_bank: Bank,
        max_buy_native: int,
        max_sell_native: int,
        max_buy: float,
        max_sell: float,
    ) -> float:
        """
        Berechnet den Preisaufschlag für einen Conditional Swap.

        Args:
            group (Group): Die Gruppe, zu der der Markt gehört.
            buy_bank (Bank): Die Bank für den Kauf.
            sell_bank (Bank): Die Bank für den Verkauf.
            max_buy_native (int): Maximale Kaufmenge in nativer Darstellung.
            max_sell_native (int): Maximale Verkaufmenge in nativer Darstellung.
            max_buy (float): Maximale Kaufmenge.
            max_sell (float): Maximale Verkaufmenge.

        Returns:
            float: Der berechnete Preisaufschlag.
        """
        from .utils import compute_premium
        return compute_premium(
            group=group,
            buy_bank=buy_bank,
            sell_bank=sell_bank,
            max_buy_native=max_buy_native,
            max_sell_native=max_sell_native,
            max_buy=max_buy,
            max_sell=max_sell
        )

# ----------------------------
# Beispielhafte Nutzung des MangoClient
# ----------------------------

# Dieses Beispiel zeigt, wie der MangoClient verwendet werden kann, um eine Verbindung herzustellen und eine Transaktion zu senden.

async def main():
    # Verbindung herstellen
    cluster_url = "https://api.mainnet-beta.solana.com"
    client = MangoClient.connect_default(cluster_url)

    # Beispielhafte Erstellung eines neuen Kontos
    payer = client.program.provider.wallet.payer  # Annahme: Provider enthält das payer Keypair
    program_id = client.program_id
    space = 1000  # Speicherplatz in Bytes
    lamports = 1000000  # Anzahl der Lamports

    new_account = await client.create_account(
        payer=payer,
        program_id=program_id,
        space=space,
        lamports=lamports
    )

    print(f"Neues Konto erstellt: {new_account.public_key}")

    # Beispielhafte Unpackung von Kontodaten
    account_pubkey = new_account.public_key
    account_info = await client.connection.get_account_info(account_pubkey)
    if account_info['result']['value'] is not None:
        data = base64.b64decode(account_info['result']['value']['data'][0])
        fmt = 'I32s'  # Beispielhafte Formatzeichenfolge
        unpacked_data = client.unpack_account_data(data, fmt)
        field1, field2 = unpacked_data
        field2 = field2.decode('utf-8').rstrip('\x00')
        print(f"Unpacked Data: field1={field1}, field2={field2}")
    else:
        print("Account nicht gefunden")

    # Beispielhafte Transaktionsanweisungen erstellen
    # Dies hängt von Ihrer spezifischen Anwendung ab
    # Hier als Platzhalter eine leere Liste
    instructions = []

    # Transaktion senden und bestätigen
    status = await client.send_and_confirm_transaction(ixs=instructions)
    print(f"Transaktion Status: {status.status}, Signature: {status.signature}")

if __name__ == "__main__":
    asyncio.run(main())
