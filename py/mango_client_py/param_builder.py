# mango_client_py/param_builder.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from solana.publickey import PublicKey
from decimal import Decimal

from .types import (
    OracleConfigParams,
    InterestRateParams,
)
from solana.rpc.commitment import Commitment

@dataclass
class TokenRegisterParams:
    oracle_config: OracleConfigParams
    group_insurance_fund: bool
    interest_rate_params: InterestRateParams
    loan_fee_rate: float
    loan_origination_fee_rate: float
    maint_asset_weight: float
    init_asset_weight: float
    maint_liab_weight: float
    init_liab_weight: float
    liquidation_fee: float
    stable_price_delay_interval_seconds: int
    stable_price_delay_growth_limit: float
    stable_price_growth_limit: float
    min_vault_to_deposits_ratio: float
    net_borrow_limit_per_window_quote: int
    net_borrow_limit_window_size_ts: int
    borrow_weight_scale_start_quote: int
    deposit_weight_scale_start_quote: int
    reduce_only: int
    token_conditional_swap_taker_fee_rate: float
    token_conditional_swap_maker_fee_rate: float
    flash_loan_swap_fee_rate: float
    interest_curve_scaling: float
    interest_target_utilization: float
    deposit_limit: int
    zero_util_rate: float
    platform_liquidation_fee: float
    disable_asset_liquidation: bool
    collateral_fee_per_day: float
    tier: str

@dataclass
class TokenEditParams:
    oracle: Optional[PublicKey] = None
    oracle_config: Optional[OracleConfigParams] = None
    group_insurance_fund: Optional[bool] = None
    interest_rate_params: Optional[InterestRateParams] = None
    loan_fee_rate: Optional[float] = None
    loan_origination_fee_rate: Optional[float] = None
    maint_asset_weight: Optional[float] = None
    init_asset_weight: Optional[float] = None
    maint_liab_weight: Optional[float] = None
    init_liab_weight: Optional[float] = None
    liquidation_fee: Optional[float] = None
    stable_price_delay_interval_seconds: Optional[int] = None
    stable_price_delay_growth_limit: Optional[float] = None
    stable_price_growth_limit: Optional[float] = None
    min_vault_to_deposits_ratio: Optional[float] = None
    net_borrow_limit_per_window_quote: Optional[int] = None
    net_borrow_limit_window_size_ts: Optional[int] = None
    borrow_weight_scale_start_quote: Optional[int] = None
    deposit_weight_scale_start_quote: Optional[int] = None
    reset_stable_price: Optional[bool] = None
    reset_net_borrow_limit: Optional[bool] = None
    reduce_only: Optional[int] = None
    name: Optional[str] = None
    force_close: Optional[bool] = None
    token_conditional_swap_taker_fee_rate: Optional[float] = None
    token_conditional_swap_maker_fee_rate: Optional[float] = None
    flash_loan_swap_fee_rate: Optional[float] = None
    interest_curve_scaling: Optional[float] = None
    interest_target_utilization: Optional[float] = None
    maint_weight_shift_start: Optional[int] = None
    maint_weight_shift_end: Optional[int] = None
    maint_weight_shift_asset_target: Optional[float] = None
    maint_weight_shift_liab_target: Optional[float] = None
    maint_weight_shift_abort: Optional[bool] = None
    fallback_oracle: Optional[PublicKey] = None
    deposit_limit: Optional[int] = None
    zero_util_rate: Optional[float] = None
    platform_liquidation_fee: Optional[float] = None
    disable_asset_liquidation: Optional[bool] = None
    collateral_fee_per_day: Optional[float] = None
    tier: Optional[str] = None
    force_withdraw: Optional[bool] = None

@dataclass
class PerpEditParams:
    oracle: Optional[PublicKey] = None
    oracle_config: Optional[OracleConfigParams] = None
    base_decimals: Optional[int] = None
    maint_base_asset_weight: Optional[float] = None
    init_base_asset_weight: Optional[float] = None
    maint_base_liab_weight: Optional[float] = None
    init_base_liab_weight: Optional[float] = None
    maint_overall_asset_weight: Optional[float] = None
    init_overall_asset_weight: Optional[float] = None
    base_liquidation_fee: Optional[float] = None
    maker_fee: Optional[float] = None
    taker_fee: Optional[float] = None
    fee_penalty: Optional[float] = None
    min_funding: Optional[float] = None
    max_funding: Optional[float] = None
    impact_quantity: Optional[float] = None
    group_insurance_fund: Optional[bool] = None
    settle_fee_flat: Optional[float] = None
    settle_fee_amount_threshold: Optional[float] = None
    settle_fee_fraction_low_health: Optional[float] = None
    stable_price_delay_interval_seconds: Optional[int] = None
    stable_price_delay_growth_limit: Optional[float] = None
    stable_price_growth_limit: Optional[float] = None
    settle_pnl_limit_factor: Optional[float] = None
    settle_pnl_limit_window_size: Optional[int] = None
    reduce_only: Optional[bool] = None
    reset_stable_price: Optional[bool] = None
    positive_pnl_liquidation_fee: Optional[float] = None
    name: Optional[str] = None
    force_close: Optional[bool] = None
    platform_liquidation_fee: Optional[float] = None

@dataclass
class IxGateParams:
    AccountClose: bool = True
    AccountCreate: bool = True
    AccountEdit: bool = True
    AccountExpand: bool = True
    AccountToggleFreeze: bool = True
    AltExtend: bool = True
    AltSet: bool = True
    FlashLoan: bool = True
    GroupClose: bool = True
    GroupCreate: bool = True
    GroupToggleHalt: bool = True
    HealthRegion: bool = True
    PerpCancelAllOrders: bool = True
    PerpCancelAllOrdersBySide: bool = True
    PerpCancelOrder: bool = True
    PerpCancelOrderByClientOrderId: bool = True
    PerpCloseMarket: bool = True
    PerpConsumeEvents: bool = True
    PerpCreateMarket: bool = True
    PerpDeactivatePosition: bool = True
    PerpEditMarket: bool = True
    PerpLiqBaseOrPositivePnl: bool = True
    PerpLiqForceCancelOrders: bool = True
    PerpLiqNegativePnlOrBankruptcy: bool = True
    PerpPlaceOrder: bool = True
    PerpSettleFees: bool = True
    PerpSettlePnl: bool = True
    PerpUpdateFunding: bool = True
    Serum3CancelAllOrders: bool = True
    Serum3CancelOrder: bool = True
    Serum3CloseOpenOrders: bool = True
    Serum3CreateOpenOrders: bool = True
    Serum3DeregisterMarket: bool = True
    Serum3EditMarket: bool = True
    Serum3LiqForceCancelOrders: bool = True
    Serum3PlaceOrder: bool = True
    Serum3RegisterMarket: bool = True
    Serum3SettleFunds: bool = True
    StubOracleClose: bool = True
    StubOracleCreate: bool = True
    StubOracleSet: bool = True
    TokenAddBank: bool = True
    TokenDeposit: bool = True
    TokenDeregister: bool = True
    TokenEdit: bool = True
    TokenLiqBankruptcy: bool = True
    TokenLiqWithToken: bool = True
    TokenRegister: bool = True
    TokenRegisterTrustless: bool = True
    TokenUpdateIndexAndRate: bool = True
    TokenWithdraw: bool = True
    AccountBuybackFeesWithMngo: bool = True
    TokenForceCloseBorrowsWithToken: bool = True
    PerpForceClosePosition: bool = True
    GroupWithdrawInsuranceFund: bool = True
    TokenConditionalSwapCreate: bool = True
    TokenConditionalSwapTrigger: bool = True
    TokenConditionalSwapCancel: bool = True
    OpenbookV2CancelOrder: bool = True
    OpenbookV2CloseOpenOrders: bool = True
    OpenbookV2CreateOpenOrders: bool = True
    OpenbookV2DeregisterMarket: bool = True
    OpenbookV2EditMarket: bool = True
    OpenbookV2LiqForceCancelOrders: bool = True
    OpenbookV2PlaceOrder: bool = True
    OpenbookV2PlaceTakeOrder: bool = True
    OpenbookV2RegisterMarket: bool = True
    OpenbookV2SettleFunds: bool = True
    AdminTokenWithdrawFees: bool = True
    AdminPerpWithdrawFees: bool = True
    AccountSizeMigration: bool = True
    TokenConditionalSwapStart: bool = True
    TokenConditionalSwapCreatePremiumAuction: bool = True
    TokenConditionalSwapCreateLinearAuction: bool = True
    Serum3PlaceOrderV2: bool = True
    TokenForceWithdraw: bool = True
    SequenceCheck: bool = True
    HealthCheck: bool = True
    GroupChangeInsuranceFund: bool = True

@dataclass
class InterestRateParams:
    util0: float
    rate0: float
    util1: float
    rate1: float
    max_rate: float
    adjustment_factor: float

@dataclass
class OracleConfigParams:
    conf_filter: float
    max_staleness_slots: Optional[int] = None

# Default TokenRegisterParams
DefaultTokenRegisterParams = TokenRegisterParams(
    oracle_config=OracleConfigParams(
        conf_filter=0.3,
        max_staleness_slots=None,
    ),
    group_insurance_fund=False,
    interest_rate_params=InterestRateParams(
        util0=0.5,
        rate0=0.018,
        util1=0.8,
        rate1=0.05,
        max_rate=0.5,
        adjustment_factor=0.004,
    ),
    loan_fee_rate=0.0005,
    loan_origination_fee_rate=0.0075,
    maint_asset_weight=0.0,
    init_asset_weight=0.0,
    maint_liab_weight=1.4,
    init_liab_weight=1.8,
    liquidation_fee=0.2,
    stable_price_delay_interval_seconds=60 * 60,
    stable_price_delay_growth_limit=0.06,
    stable_price_growth_limit=0.0003,
    min_vault_to_deposits_ratio=0.2,
    net_borrow_limit_per_window_quote=5_000_000_000,
    net_borrow_limit_window_size_ts=86_400,
    borrow_weight_scale_start_quote=5_000_000_000,
    deposit_weight_scale_start_quote=5_000_000_000,
    reduce_only=0,
    token_conditional_swap_taker_fee_rate=0.0005,
    token_conditional_swap_maker_fee_rate=0.0005,
    flash_loan_swap_fee_rate=0.0005,
    interest_curve_scaling=4.0,
    interest_target_utilization=0.5,
    deposit_limit=0,
    zero_util_rate=0.0,
    platform_liquidation_fee=0.0,
    disable_asset_liquidation=False,
    collateral_fee_per_day=0.0,
    tier='',
)

# NullTokenEditParams
NullTokenEditParams = TokenEditParams()

# NullPerpEditParams
NullPerpEditParams = PerpEditParams()

# TrueIxGateParams
TrueIxGateParams = IxGateParams()

def build_ix_gate(params: IxGateParams) -> int:
    """
    Baut die IxGate Bitmask basierend auf den gegebenen Parametern.
    
    Args:
        params (IxGateParams): Die IxGate Parameter.
    
    Returns:
        int: Die IxGate Bitmask als Integer.
    """
    ix_gate = 0

    # Mapping der IxGateParams Attribute zu Bitpositionen
    ix_map = {
        'AccountClose': 0,
        'AccountCreate': 1,
        'AccountEdit': 2,
        'AccountExpand': 3,
        'AccountToggleFreeze': 4,
        'AltExtend': 5,
        'AltSet': 6,
        'FlashLoan': 7,
        'GroupClose': 8,
        'GroupCreate': 9,
        'HealthRegion': 10,
        'PerpCancelAllOrders': 11,
        'PerpCancelAllOrdersBySide': 12,
        'PerpCancelOrder': 13,
        'PerpCancelOrderByClientOrderId': 14,
        'PerpCloseMarket': 15,
        'PerpConsumeEvents': 16,
        'PerpCreateMarket': 17,
        'PerpDeactivatePosition': 18,
        'PerpLiqBaseOrPositivePnl': 19,
        'PerpLiqForceCancelOrders': 20,
        'PerpLiqNegativePnlOrBankruptcy': 21,
        'PerpPlaceOrder': 22,
        'PerpSettleFees': 23,
        'PerpSettlePnl': 24,
        'PerpUpdateFunding': 25,
        'Serum3CancelAllOrders': 26,
        'Serum3CancelOrder': 27,
        'Serum3CloseOpenOrders': 28,
        'Serum3CreateOpenOrders': 29,
        'Serum3DeregisterMarket': 30,
        'Serum3EditMarket': 31,
        'Serum3LiqForceCancelOrders': 32,
        'Serum3PlaceOrder': 33,
        'Serum3RegisterMarket': 34,
        'Serum3SettleFunds': 35,
        'StubOracleClose': 36,
        'StubOracleCreate': 37,
        'StubOracleSet': 38,
        'TokenAddBank': 39,
        'TokenDeposit': 40,
        'TokenDeregister': 41,
        'TokenLiqBankruptcy': 42,
        'TokenLiqWithToken': 43,
        'TokenRegister': 44,
        'TokenRegisterTrustless': 45,
        'TokenUpdateIndexAndRate': 46,
        'TokenWithdraw': 47,
        'AccountBuybackFeesWithMngo': 48,
        'TokenForceCloseBorrowsWithToken': 49,
        'PerpForceClosePosition': 50,
        'GroupWithdrawInsuranceFund': 51,
        'TokenConditionalSwapCreate': 52,
        'TokenConditionalSwapTrigger': 53,
        'TokenConditionalSwapCancel': 54,
        'OpenbookV2CancelOrder': 55,
        'OpenbookV2CloseOpenOrders': 56,
        'OpenbookV2CreateOpenOrders': 57,
        'OpenbookV2DeregisterMarket': 58,
        'OpenbookV2EditMarket': 59,
        'OpenbookV2LiqForceCancelOrders': 60,
        'OpenbookV2PlaceOrder': 61,
        'OpenbookV2PlaceTakeOrder': 62,
        'OpenbookV2RegisterMarket': 63,
        'OpenbookV2SettleFunds': 64,
        'AdminTokenWithdrawFees': 65,
        'AdminPerpWithdrawFees': 66,
        'AccountSizeMigration': 67,
        'TokenConditionalSwapStart': 68,
        'TokenConditionalSwapCreatePremiumAuction': 69,
        'TokenConditionalSwapCreateLinearAuction': 70,
        'Serum3PlaceOrderV2': 71,
        'TokenForceWithdraw': 72,
        'SequenceCheck': 73,
        'HealthCheck': 74,
        'GroupChangeInsuranceFund': 75,
    }

    for attr, bit_position in ix_map.items():
        attr_value = getattr(params, attr)
        if not attr_value:
            ix_gate |= (1 << bit_position)

    return ix_gate
