import enum


class RiskTier(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LoanStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    REPAID = "repaid"
    DEFAULTED = "defaulted"
    LIQUIDATED = "liquidated"
    CANCELLED = "cancelled"


class RepaymentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PAID = "paid"
    OVERDUE = "overdue"
    MISSED = "missed"


class TransactionType(str, enum.Enum):
    DISBURSEMENT = "disbursement"
    REPAYMENT = "repayment"
    COLLATERAL_LOCK = "collateral_lock"
    COLLATERAL_RELEASE = "collateral_release"
    LIQUIDATION = "liquidation"
    FEE = "fee"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class AccountProvider(str, enum.Enum):
    BANK = "bank"
    MPESA = "mpesa"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    METAMASK = "metamask"
    PHANTOM = "phantom"


class IncomeFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    IRREGULAR = "irregular"


class SybilVerdict(str, enum.Enum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    SYBIL = "sybil"


class Currency(str, enum.Enum):
    USD = "USD"
    KES = "KES"
    ETH = "ETH"
    SOL = "SOL"
    USDC = "USDC"
    USDT = "USDT"
