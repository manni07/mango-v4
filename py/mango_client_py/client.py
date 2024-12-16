# mango_client_py/client.py

from anchorpy import AnchorProvider, Program
from solana.publickey import PublicKey
from typing import List, Optional, Dict, Any, Callable
import sys

from .accounts.mango_account import MangoAccounts
from .accounts.oracles import Oracles
from .utils import unpack_account, create_account, to_native
from .types import Group, MangoAccount, TokenIndex, HealthCheckKind, MangoSignatureStatus
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

    # Die restlichen Methoden werden in die entsprechenden Submodule (accounts/mango_account.py, accounts/oracles.py) ausgelagert.
