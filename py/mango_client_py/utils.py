# mango_client_py/utils.py

from typing import Any, Callable, Dict, List, Optional, Tuple
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID, CreateAccountParams, create_account
from solana.rpc.types import TxOpts
from decimal import Decimal
from itertools import groupby
from operator import attrgetter
from statistics import median
import math
import struct
import base64

from .types import (
    Group,
    Bank,
    RecentPrioritizationFee,
    Serum3Market,
    PerpMarket,
    TokenConditionalSwap,
)
from anchorpy import Program, Idl
from anchorpy.idl import IdlInstruction

# ----------------------------
# Hilfsfunktionen
# ----------------------------

def to_native(amount: Any, decimals: int) -> int:
    """
    Konvertiert einen Betrag in die native Darstellung basierend auf den Dezimalstellen.

    Args:
        amount (Any): Der Betrag als float oder Decimal.
        decimals (int): Die Anzahl der Dezimalstellen.

    Returns:
        int: Der konvertierte Betrag in nativer Darstellung.
    """
    return int(Decimal(amount) * (10 ** decimals))


def to_native_sell_per_buy_token_price(
    threshold_price: float,
    sell_bank: 'Bank',
    buy_bank: 'Bank',
) -> int:
    """
    Konvertiert den Schwellenpreis in die native Darstellung basierend auf den Dezimalstellen der Verkäufe und Käufe.

    Args:
        threshold_price (float): Der Schwellenpreis.
        sell_bank (Bank): Die Bank für den Verkauf.
        buy_bank (Bank): Die Bank für den Kauf.

    Returns:
        int: Der konvertierte Schwellenpreis in nativer Darstellung.
    """
    sell_decimals = sell_bank.mint_decimals
    buy_decimals = buy_bank.mint_decimals
    # Beispielhafte Berechnung: threshold_price * 10^(sell_decimals + buy_decimals)
    return int(Decimal(threshold_price) * (10 ** (sell_decimals + buy_decimals)))


def uniq(items: List[Any], key: Callable[[Any], Any]) -> List[Any]:
    """
    Gibt eine Liste von einzigartigen Elementen basierend auf einem Schlüssel zurück.

    Args:
        items (List[Any]): Die Eingabeliste.
        key (Callable[[Any], Any]): Eine Funktion, die den Schlüssel für jedes Element extrahiert.

    Returns:
        List[Any]: Eine Liste von einzigartigen Elementen.
    """
    seen = set()
    unique_items = []
    for item in items:
        k = key(item)
        if k not in seen:
            seen.add(k)
            unique_items.append(item)
    return unique_items


# ----------------------------
# Transaction Instructions
# ----------------------------

async def account_expand_v2_ix(
    group: Group,
    account: 'MangoAccount',
    tokens_length: int,
    serum3_length: int,
    perps_length: int,
    perp_open_orders_length: int,
    token_conditional_swaps_length: int,
) -> TransactionInstruction:
    """
    Erstellt eine TransactionInstruction zum Erweitern des Kontos (Account Expansion).

    Args:
        group (Group): Die Gruppe, zu der der Markt gehört.
        account (MangoAccount): Das Mango-Konto des Benutzers.
        tokens_length (int): Anzahl der Tokens.
        serum3_length (int): Anzahl der Serum3-Märkte.
        perps_length (int): Anzahl der Perps.
        perp_open_orders_length (int): Anzahl der Perp Open Orders.
        token_conditional_swaps_length (int): Anzahl der Token Conditional Swaps.

    Returns:
        TransactionInstruction: Die erstellte TransactionInstruction.
    """
    ix = await group.program.methods \
        .accountExpandV2(
            tokens_length,
            serum3_length,
            perps_length,
            perp_open_orders_length,
            token_conditional_swaps_length,
        ) \
        .accounts({
            'group': group.public_key,
            'account': account.public_key,
        }) \
        .instruction()
    return ix


async def token_conditional_swap_create_premium_auction_ix(
    program: Program,
    group: Group,
    account: 'MangoAccount',
    sell_bank: Bank,
    buy_bank: Bank,
    lower_limit: int,
    upper_limit: int,
    max_buy_native: int,
    max_sell_native: int,
    auction_type: str,
    price_premium_native: int,
    some_flag1: bool,
    some_flag2: bool,
    expiry_timestamp: int,
    threshold_price_in_sell_per_buy_token: bool,
    param1: int,
    param2: int,
    param3: int,
) -> List[TransactionInstruction]:
    """
    Erstellt die TransactionInstructions für Conditional Swaps mit Premium Auktionen.

    Args:
        program (Program): Das Anchor Program.
        group (Group): Die Gruppe, zu der der Markt gehört.
        account (MangoAccount): Das Mango-Konto des Benutzers.
        sell_bank (Bank): Die Bank, von der verkauft wird.
        buy_bank (Bank): Die Bank, von der gekauft wird.
        lower_limit (int): Unteres Limit für den Swap.
        upper_limit (int): Oberes Limit für den Swap.
        max_buy_native (int): Maximale Kaufmenge in nativer Darstellung.
        max_sell_native (int): Maximale Verkaufmenge in nativer Darstellung.
        auction_type (str): Typ der Auktion ('TakeProfitOnDeposit', 'StopLossOnDeposit', etc.).
        price_premium_native (int): Preisaufschlag in nativer Darstellung.
        some_flag1 (bool): Ein Flag, das eine bestimmte Funktionalität steuert.
        some_flag2 (bool): Ein weiteres Flag, das eine bestimmte Funktionalität steuert.
        expiry_timestamp (int): Ablaufzeitpunkt der Auktion.
        threshold_price_in_sell_per_buy_token (bool): Ob der Schwellenpreis in Verkäufe pro Kauf Token berechnet wird.
        param1 (int): Weitere Parameter nach Bedarf.
        param2 (int): Weitere Parameter nach Bedarf.
        param3 (int): Weitere Parameter nach Bedarf.

    Returns:
        List[TransactionInstruction]: Liste der erstellten TransactionInstructions.
    """
    ix = await program.methods \
        .tokenConditionalSwapCreatePremiumAuction(
            lower_limit,
            upper_limit,
            max_buy_native,
            max_sell_native,
            auction_type,
            price_premium_native,
            some_flag1,
            some_flag2,
            expiry_timestamp,
            threshold_price_in_sell_per_buy_token,
            param1,
            param2,
            param3,
        ) \
        .accounts({
            'group': group.public_key,
            'account': account.public_key,
            'sellBank': sell_bank.public_key,
            'buyBank': buy_bank.public_key,
            'owner': account.owner,
            # Fügen Sie weitere notwendige Accounts hinzu
        }) \
        .instruction()

    return [ix]


# ----------------------------
# Premium Berechnung
# ----------------------------

def compute_premium(
    group: Group,
    buy_bank: Bank,
    sell_bank: Bank,
    max_buy_native: int,
    max_sell_native: int,
    max_buy: float,
    max_sell: float,
) -> float:
    """
    Berechnet den Preisaufschlag für den Conditional Swap.

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
    # Implementieren Sie die tatsächliche Logik entsprechend Ihrer TypeScript-Implementierung
    # Beispielhafte Logik:
    premium = (max_buy_native / (10 ** buy_bank.mint_decimals)) * 0.01 + \
              (max_sell_native / (10 ** sell_bank.mint_decimals)) * 0.02
    return premium


# ----------------------------
# Fallback Oracle Kontext
# ----------------------------

async def derive_fallback_oracle_contexts(
    group: Group,
    fallback_oracle_config: Any,
    connection: AsyncClient,
) -> Dict[str, List[PublicKey]]:
    """
    Leitet die Fallback-Oracle-Kontexte basierend auf der Konfiguration ab.

    Args:
        group (Group): Die Gruppe, zu der der Markt gehört.
        fallback_oracle_config (Any): Die Fallback-Oracle-Konfiguration.
        connection (AsyncClient): Die Solana-Verbindung.

    Returns:
        Dict[str, List[PublicKey]]: Eine Map von Oracle PublicKeys zu ihren Fallbacks.
    """
    if isinstance(fallback_oracle_config, list):
        # Fixed Fallbacks
        oracles = []
        fallbacks = []
        for banks in group.banks_map_by_token_index.values():
            for bank in banks:
                if bank.oracle in fallback_oracle_config:
                    oracles.append(bank.oracle)
                    fallbacks.append(bank.fallback_oracle)
        return await create_fallback_oracle_map(connection, oracles, fallbacks)
    elif fallback_oracle_config == 'never':
        return {}
    elif fallback_oracle_config == 'dynamic':
        now_slot = await connection.get_slot()
        oracles = []
        fallbacks = []
        await group.reload_bank_oracle_prices()  # Passen Sie ggf. die Parameter an
        for banks in group.banks_map_by_token_index.values():
            for bank in banks:
                if bank.is_oracle_stale_or_unconfident(now_slot):
                    oracles.append(bank.oracle)
                    fallbacks.append(bank.fallback_oracle)
        return await create_fallback_oracle_map(connection, oracles, fallbacks)
    elif fallback_oracle_config == 'all':
        oracles = []
        fallbacks = []
        for banks in group.banks_map_by_token_index.values():
            for bank in banks:
                oracles.append(bank.oracle)
                fallbacks.append(bank.fallback_oracle)
        return await create_fallback_oracle_map(connection, oracles, fallbacks)
    else:
        return {}


async def create_fallback_oracle_map(
    connection: AsyncClient,
    oracles: List[PublicKey],
    fallbacks: List[PublicKey],
) -> Dict[str, List[PublicKey]]:
    """
    Erstellt eine Map von Oracle PublicKeys zu ihren Fallbacks.

    Args:
        connection (AsyncClient): Die Solana-Verbindung.
        oracles (List[PublicKey]): Liste der Oracle PublicKeys.
        fallbacks (List[PublicKey]): Liste der Fallback PublicKeys.

    Returns:
        Dict[str, List[PublicKey]]: Eine Map von Oracle PublicKeys zu ihren Fallbacks.
    """
    fallback_map: Dict[str, List[PublicKey]] = {}
    for oracle, fallback in zip(oracles, fallbacks):
        oracle_key = oracle.to_base58()
        if oracle_key not in fallback_map:
            fallback_map[oracle_key] = []
        fallback_map[oracle_key].append(fallback)
    return fallback_map


# ----------------------------
# Prioritization Fee Schätzung
# ----------------------------

async def get_recent_prioritization_fees(
    connection: AsyncClient,
    locked_writable_accounts: List[PublicKey],
) -> List[RecentPrioritizationFee]:
    """
    Ruft die aktuellen Priorisierungsgebühren für eine Liste von beschreibbaren Konten ab.

    Args:
        connection (AsyncClient): Die Solana-Verbindung.
        locked_writable_accounts (List[PublicKey]): Liste der beschreibbaren PublicKeys.

    Returns:
        List[RecentPrioritizationFee]: Liste der Gebühreninformationen.
    """
    # Implementieren Sie die tatsächliche Logik, um die Gebühren von der Solana-API abzurufen.
    # Dies ist ein Platzhalter und muss an die spezifische API angepasst werden.
    # Beispiel:
    response = await connection.request(
        "getRecentPrioritizationFees",
        [account.to_base58() for account in locked_writable_accounts]
    )
    if 'result' in response and isinstance(response['result'], list):
        return [
            RecentPrioritizationFee(
                slot=fee["slot"],
                prioritization_fee=fee["prioritizationFee"]
            )
            for fee in response['result']
            if "slot" in fee and "prioritizationFee" in fee
        ]
    return []


# ----------------------------
# Weitere Hilfsfunktionen
# ----------------------------

# Hier können Sie weitere Hilfsfunktionen hinzufügen, die für Ihren Client benötigt werden.
# Zum Beispiel Funktionen zur Verarbeitung von Transaktionen, Fehlermanagement, etc.


# ----------------------------
# Unpack Account
# ----------------------------

def unpack_account(data: bytes, fmt: str) -> Tuple[Any, ...]:
    """
    Entpackt die Rohdaten eines Solana-Kontos basierend auf dem gegebenen Format.

    Args:
        data (bytes): Die Rohdaten des Kontos.
        fmt (str): Das Format der Daten (z.B. Struct-Formatzeichenfolge).

    Returns:
        Tuple[Any, ...]: Die entpackten Daten.
    """
    return struct.unpack(fmt, data)


# ----------------------------
# Create Account
# ----------------------------

async def create_new_account(
    connection: AsyncClient,
    payer: Keypair,
    program_id: PublicKey,
    space: int,
    lamports: int,
    new_account_keypair: Optional[Keypair] = None,
) -> Keypair:
    """
    Erstellt ein neues Solana-Konto.

    Args:
        connection (AsyncClient): Die Solana-Verbindung.
        payer (Keypair): Das Keypair, das die Lamports zur Finanzierung des neuen Kontos bereitstellt.
        program_id (PublicKey): Die PublicKey des Programms, das das neue Konto besitzt.
        space (int): Der Speicherplatz, der dem Konto zugewiesen werden soll (in Bytes).
        lamports (int): Die Menge an Lamports, die dem Konto zugewiesen werden sollen.
        new_account_keypair (Optional[Keypair]): Optionales Keypair für das neue Konto. Wenn None, wird ein neues generiert.

    Returns:
        Keypair: Das Keypair des erstellten Kontos.
    """
    if new_account_keypair is None:
        new_account_keypair = Keypair.generate()

    params = CreateAccountParams(
        from_pubkey=payer.public_key,
        new_account_pubkey=new_account_keypair.public_key,
        lamports=lamports,
        space=space,
        program_id=program_id,
    )

    instruction = create_account(params)

    # Erstellen Sie eine Transaktion und senden Sie sie
    transaction = TransactionInstruction(
        keys=[
            {"pubkey": payer.public_key, "is_signer": True, "is_writable": True},
            {"pubkey": new_account_keypair.public_key, "is_signer": True, "is_writable": True},
        ],
        program_id=SYS_PROGRAM_ID,
        data=instruction.data,
    )

    # Senden und bestätigen Sie die Transaktion
    response = await connection.send_transaction(
        transaction, payer, new_account_keypair,
        opts=TxOpts(skip_confirmation=False)
    )

    return new_account_keypair
