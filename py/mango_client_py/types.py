# mango_client_py/types.py

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
from solana.publickey import PublicKey
from solana.rpc.commitment import Commitment
from solana.rpc.types import TxOpts

# ----------------------------
# Enums
# ----------------------------

class Serum3Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class Serum3SelfTradeBehavior(Enum):
    DECREMENT_AND_CANCEL = "decrement_and_cancel"
    CANCEL_OLDEST = "cancel_oldest"
    CANCEL_NEWEST = "cancel_newest"

class Serum3OrderType(Enum):
    LIMIT = "limit"
    IOC = "ioc"
    POST_ONLY = "post_only"

class PerpOrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class PerpOrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"

class AuctionType(Enum):
    TAKE_PROFIT_ON_DEPOSIT = "TakeProfitOnDeposit"
    STOP_LOSS_ON_DEPOSIT = "StopLossOnDeposit"
    # Fügen Sie weitere Auktionstypen hinzu, falls erforderlich

# ----------------------------
# Data Classes
# ----------------------------

@dataclass
class RecentPrioritizationFee:
    slot: int
    prioritization_fee: int

@dataclass
class Bank:
    public_key: PublicKey
    mint_decimals: int
    oracle: PublicKey
    fallback_oracle: PublicKey

    def is_oracle_stale_or_unconfident(self, current_slot: int) -> bool:
        """
        Überprüft, ob der Oracle veraltet oder unzuverlässig ist.
        Implementieren Sie die tatsächliche Logik basierend auf Ihrem Projekt.
        """
        # Beispielhafte Implementierung
        # Dies sollte angepasst werden, um die tatsächlichen Bedingungen zu überprüfen
        return False

@dataclass
class Serum3Market:
    market_index: int
    public_key: PublicKey
    oracle: PublicKey
    external_market_pk: Optional[PublicKey] = None
    # Fügen Sie weitere Felder hinzu, die für Serum3Markets relevant sind

@dataclass
class PerpMarket:
    market_index: int
    public_key: PublicKey
    # Fügen Sie weitere Felder hinzu, die für PerpMarkets relevant sind

@dataclass
class TokenConditionalSwap:
    id: int
    buy_token_index: int
    sell_token_index: int
    is_configured: bool
    # Fügen Sie weitere Felder hinzu, die für TokenConditionalSwaps relevant sind

@dataclass
class MangoAccount:
    public_key: PublicKey
    owner: PublicKey
    sequence_number: int
    account_num: int
    delegate: PublicKey
    token_conditional_swaps: List[TokenConditionalSwap] = field(default_factory=list)
    tokens: List[Any] = field(default_factory=list)  # Passen Sie den Typ an, falls bekannt
    serum3: List[Any] = field(default_factory=list)  # Passen Sie den Typ an, falls bekannt
    perps: List[Any] = field(default_factory=list)  # Passen Sie den Typ an, falls bekannt
    perp_open_orders: List[Any] = field(default_factory=list)  # Passen Sie den Typ an, falls bekannt

@dataclass
class Group:
    public_key: PublicKey
    insurance_vault: PublicKey
    address_lookup_tables_list: List[Any] = field(default_factory=list)  # Passen Sie den Typ an, falls bekannt
    mint_infos_map_by_token_index: Dict[int, Any] = field(default_factory=dict)  # Passen Sie den Typ an, falls bekannt
    banks_map_by_token_index: Dict[int, List[Bank]] = field(default_factory=dict)
    serum3_markets_map_by_market_index: Dict[int, Serum3Market] = field(default_factory=dict)
    serum3_external_markets_map: Dict[Any, Any] = field(default_factory=dict)  # Passen Sie den Typ an, falls bekannt
    buyback_fees_swap_mango_account: PublicKey = field(default_factory=lambda: PublicKey(""))

    def get_perp_market_by_market_index(self, market_index: int) -> PerpMarket:
        """
        Gibt den PerpMarket basierend auf dem Marktindex zurück.
        """
        return self.perp_markets_map_by_market_index.get(market_index)

    def reload_bank_oracle_prices(self, *args, **kwargs):
        """
        Lädt die Oracle-Preise der Banken neu.
        Implementieren Sie die tatsächliche Logik basierend auf Ihrem Projekt.
        """
        pass

@dataclass
class HealthCheckKind(Enum):
    SOME_KIND = "SOME_KIND"
    ANOTHER_KIND = "ANOTHER_KIND"
    # Fügen Sie weitere Arten hinzu, falls erforderlich

@dataclass
class MangoSignatureStatus:
    signature: str
    status: str
    # Fügen Sie weitere Felder hinzu, die für den Status relevant sind

# ----------------------------
# Weitere Typen
# ----------------------------

# Falls weitere Typen benötigt werden, können diese hier hinzugefügt werden.
# Beispielsweise könnten Sie Typen für verschiedene Konto-Layouts, RPC-Antworten usw. definieren.

# Beispiel:
@dataclass
class TokenInfo:
    token_index: int
    # Fügen Sie weitere relevante Felder hinzu

# Weitere Enums, wenn erforderlich
class FallbackOracleConfig(Enum):
    NEVER = "never"
    ALL = "all"
    DYNAMIC = "dynamic"
    FIXED = "fixed"

# Beispiel für eine HealthCheck
@dataclass
class HealthCheck:
    kind: HealthCheckKind
    details: Dict[str, Any] = field(default_factory=dict)

# Beispiel für weitere Datenstrukturen
@dataclass
class Serum3Order:
    order_id: int
    side: Serum3Side
    price: float
    size: float
    # Weitere Felder je nach Bedarf

@dataclass
class PerpOrder:
    order_id: int
    side: PerpOrderSide
    price: float
    quantity: float
    # Weitere Felder je nach Bedarf
