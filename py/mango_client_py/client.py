# mango_client_py/client.py

from anchorpy import AnchorProvider, Program
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction
from typing import List, Optional, Dict, Any, Callable
import sys

from .accounts.mango_account import MangoAccounts
from .accounts.oracles import Oracles
from .accounts.perp import Perp
from .utils import unpack_account, create_account, to_native, uniq
from .types import Group, MangoAccount, TokenIndex, HealthCheckKind, MangoSignatureStatus, RecentPrioritizationFee, MangoSignatureStatus
from .utils.rpc import send_transaction


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
    MAX_RECENT_PRIORITY_FEE_ACCOUNTS = 64
    MAX_RECENT_PRIORITY_FEES = 20

    
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

        # Initialize sub-modules
        self.accounts = MangoAccounts(self)
        self.oracles = Oracles(self)

        # Beispiel für die Erhöhung des StackTrace-Limits in Python
        sys.setrecursionlimit(1000)  # Anpassen nach Bedarf

    @property
    def connection(self) -> Any:  # Typ anpassen, z.B. AsyncClient
        return self.program.provider.connection

    @property
    def wallet_pk(self) -> PublicKey:
        return self.program.provider.wallet.public_key

    async def send_and_confirm_transaction(
        self,
        ixs: List[Any],  # Typ anpassen, z.B. TransactionInstruction
        opts: Optional[Dict[str, Any]] = None
    ) -> MangoSignatureStatus:
        # Implementieren Sie die Logik zum Senden und Bestätigen der Transaktion
        opts = opts or {}
        prioritization_fee = opts.get('prioritization_fee', self.program.opts.prioritization_fee)

        if self.program.opts.estimate_fee or opts.get('estimate_fee', False):
            prioritization_fee = await self.estimate_prioritization_fee(ixs)
        else:
            prioritization_fee = self.program.opts.prioritization_fee

        # Senden und Bestätigen der Transaktion
        status = await send_transaction(
            self.program.provider,
            self.program.opts.prepended_global_additional_instructions + ixs,
            opts.get('alts', []),
            {
                'postSendTxCallback': self.program.opts.post_send_tx_callback,
                'postTxConfirmationCallback': self.program.opts.post_tx_confirmation_callback,
                'prioritizationFee': prioritization_fee,
                'txConfirmationCommitment': self.program.opts.tx_confirmation_commitment,
                'multipleConnections': self.program.opts.multiple_connections,
                **opts,
            },
        )
        return status

    async def send_and_confirm_transaction_for_group(
        self,
        group: Group,
        ixs: List[Any],  # Typ anpassen, z.B. TransactionInstruction
        opts: Optional[Dict[str, Any]] = None
    ) -> MangoSignatureStatus:
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

    # Weitere allgemeine Methoden können hier hinzugefügt werden
    async def estimate_prioritization_fee(
        self,
        ixs: List[TransactionInstruction],
    ) -> int:
        """
        Gibt eine Schätzung der Priorisierungsgebühr für eine Reihe von Anweisungen zurück.

        Die Schätzung basiert auf den medianen Gebühren der beschreibbaren Konten, die an der Transaktion beteiligt sind.

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
        priority_fees_response = await self.connection.get_recent_prioritization_fees(
            locked_writable_accounts=unique_writable_accounts
        )

        # Konvertiere die Antwort in eine Liste von RecentPrioritizationFee
        priority_fees: List[RecentPrioritizationFee] = [
            RecentPrioritizationFee(slot=fee["slot"], prioritization_fee=fee["prioritizationFee"])
            for fee in priority_fees_response
        ]

        if not priority_fees:
            return 1

        # Gruppiere die Gebühren nach Slot und behalte die maximale Gebühr pro Slot
        priority_fees.sort(key=lambda fee: fee.slot)
        grouped_fees = groupby(priority_fees, key=attrgetter('slot'))
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
    # Die restlichen Methoden werden in die entsprechenden Submodule (accounts/mango_account.py, accounts/oracles.py) ausgelagert.
