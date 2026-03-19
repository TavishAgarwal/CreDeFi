// SPDX-License-Identifier: MIT
pragma solidity ^0.8.27;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface ICollateralVault {
    function lock(address user, address token, uint256 amount) external;
    function unlock(address user, address token, uint256 amount) external;
    function liquidate(address borrower, address liquidator, address token, uint256 seizeAmount) external;
    function collateral(address user, address token) external view returns (uint256 deposited, uint256 locked);
    function liquidationThresholdBps(address token) external view returns (uint256);
    function liquidationBonusBps() external view returns (uint256);
}

interface IInterestRateModel {
    function computeRate(uint256 totalSupply, uint256 totalBorrows, uint256 trustScore) external view returns (uint256);
}

interface ISoulboundReputationNFT {
    function trustScoreOf(address user) external view returns (uint256);
}

/**
 * @title  LoanContract
 * @notice Orchestrates the full DeFi lending lifecycle for CreDeFi:
 *         create → fund → repay → liquidate.
 *
 *         Integrates with:
 *         - CollateralVault   (collateral management)
 *         - InterestRateModel (dynamic rate computation)
 *         - SoulboundReputationNFT (trust-gated access & rate discounts)
 *
 *         Business rules:
 *         - Minimum trust score required to borrow
 *         - Collateral ratio enforced at creation
 *         - Interest accrues per-second (simple interest for clarity)
 *         - Liquidation allowed when collateral value < threshold * debt
 *         - Borrower can partially or fully repay at any time
 */
contract LoanContract is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    // ── External dependencies ────────────────────────────────────
    ICollateralVault public vault;
    IInterestRateModel public rateModel;
    ISoulboundReputationNFT public reputationNFT;

    // ── Configuration ────────────────────────────────────────────
    uint256 public minTrustScore;                // e.g. 450
    uint256 public constant BPS = 10_000;
    uint256 public constant SECONDS_PER_YEAR = 365 days;
    uint256 public totalPoolSupply;              // total lendable assets
    uint256 public totalPoolBorrows;             // total outstanding borrows

    // ── Loan data ────────────────────────────────────────────────
    enum LoanStatus { OPEN, FUNDED, REPAID, LIQUIDATED, CANCELLED }

    struct Loan {
        uint256 id;
        address borrower;
        address lender;
        address borrowToken;       // token being borrowed
        address collateralToken;   // token used as collateral
        uint256 principal;
        uint256 collateralAmount;
        uint256 interestRateBps;   // annual rate locked at funding
        uint256 accruedInterest;
        uint256 repaidAmount;
        uint256 fundedAt;          // timestamp
        uint256 durationSeconds;
        uint256 deadline;          // fundedAt + durationSeconds
        LoanStatus status;
    }

    uint256 public nextLoanId;
    mapping(uint256 => Loan) public loans;

    // Track active loans per borrower
    mapping(address => uint256) public activeLoanCount;
    uint256 public maxActiveLoansPerUser;

    // ── Price oracle (simplified: owner-set prices in USD-cents) ─
    // token → price in 1e18 units (e.g. 1 USDC = 1e18)
    mapping(address => uint256) public tokenPrice;

    // ── Events ───────────────────────────────────────────────────
    event LoanCreated(uint256 indexed loanId, address indexed borrower, uint256 principal);
    event LoanFunded(uint256 indexed loanId, address indexed lender, uint256 rateBps);
    event LoanRepaid(uint256 indexed loanId, uint256 amount, uint256 remaining);
    event LoanFullyRepaid(uint256 indexed loanId);
    event LoanLiquidated(uint256 indexed loanId, address indexed liquidator);
    event LoanCancelled(uint256 indexed loanId);
    event PriceUpdated(address indexed token, uint256 price);

    event LoanDefaulted(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 principalOwed,
        uint256 interestOwed,
        uint256 daysOverdue,
        string severity
    );
    event ReputationSlashed(
        address indexed user,
        uint256 penaltyPoints,
        uint256 newScore,
        string reason
    );
    event GuarantorSlashed(
        address indexed guarantor,
        address indexed borrower,
        uint256 indexed loanId,
        uint256 penaltyPoints
    );

    constructor(
        address _vault,
        address _rateModel,
        address _reputationNFT,
        uint256 _minTrustScore,
        uint256 _maxActiveLoansPerUser
    ) Ownable(msg.sender) {
        vault = ICollateralVault(_vault);
        rateModel = IInterestRateModel(_rateModel);
        reputationNFT = ISoulboundReputationNFT(_reputationNFT);
        minTrustScore = _minTrustScore;
        maxActiveLoansPerUser = _maxActiveLoansPerUser;
        nextLoanId = 1;
    }

    // ── Borrower: Create ─────────────────────────────────────────

    /**
     * @notice Create a loan request. Collateral is locked immediately.
     * @dev    Borrower must have deposited sufficient collateral in the Vault
     *         and must meet the minimum trust score.
     */
    function createLoan(
        address borrowToken,
        address collateralToken,
        uint256 principal,
        uint256 collateralAmount,
        uint256 durationSeconds
    ) external nonReentrant returns (uint256 loanId) {
        require(principal > 0, "Loan: zero principal");
        require(durationSeconds >= 1 days, "Loan: duration too short");
        require(durationSeconds <= 365 days, "Loan: duration too long");

        uint256 trustScore = reputationNFT.trustScoreOf(msg.sender);
        require(trustScore >= minTrustScore, "Loan: trust score too low");
        require(activeLoanCount[msg.sender] < maxActiveLoansPerUser, "Loan: too many active loans");

        uint256 ratioBps = getCollateralRatioBps(trustScore);
        _requireSufficientCollateral(borrowToken, collateralToken, principal, collateralAmount, ratioBps);

        vault.lock(msg.sender, collateralToken, collateralAmount);

        loanId = nextLoanId++;
        loans[loanId] = Loan({
            id: loanId,
            borrower: msg.sender,
            lender: address(0),
            borrowToken: borrowToken,
            collateralToken: collateralToken,
            principal: principal,
            collateralAmount: collateralAmount,
            interestRateBps: 0,
            accruedInterest: 0,
            repaidAmount: 0,
            fundedAt: 0,
            durationSeconds: durationSeconds,
            deadline: 0,
            status: LoanStatus.OPEN
        });

        activeLoanCount[msg.sender]++;

        emit LoanCreated(loanId, msg.sender, principal);
    }

    /**
     * @notice Borrower cancels an unfunded loan and unlocks collateral.
     */
    function cancelLoan(uint256 loanId) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.borrower == msg.sender, "Loan: not borrower");
        require(loan.status == LoanStatus.OPEN, "Loan: not open");

        loan.status = LoanStatus.CANCELLED;
        activeLoanCount[msg.sender]--;

        vault.unlock(msg.sender, loan.collateralToken, loan.collateralAmount);

        emit LoanCancelled(loanId);
    }

    // ── Lender: Fund ─────────────────────────────────────────────

    /**
     * @notice Fund an open loan request. Transfers principal to borrower.
     *         Interest rate is locked at this moment based on pool state
     *         and the borrower's trust score.
     */
    function fundLoan(uint256 loanId) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.status == LoanStatus.OPEN, "Loan: not open");
        require(msg.sender != loan.borrower, "Loan: self-fund");

        uint256 trustScore = reputationNFT.trustScoreOf(loan.borrower);
        uint256 rate = rateModel.computeRate(totalPoolSupply, totalPoolBorrows, trustScore);

        loan.lender = msg.sender;
        loan.interestRateBps = rate;
        loan.fundedAt = block.timestamp;
        loan.deadline = block.timestamp + loan.durationSeconds;
        loan.status = LoanStatus.FUNDED;

        totalPoolBorrows += loan.principal;

        IERC20(loan.borrowToken).safeTransferFrom(msg.sender, loan.borrower, loan.principal);

        emit LoanFunded(loanId, msg.sender, rate);
    }

    // ── Borrower: Repay ──────────────────────────────────────────

    /**
     * @notice Repay part or all of the loan.
     *         Interest is calculated up to now. Payment covers interest first,
     *         then principal.  On full repayment, collateral is unlocked.
     */
    function repay(uint256 loanId, uint256 amount) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.status == LoanStatus.FUNDED, "Loan: not funded");
        require(amount > 0, "Loan: zero repay");

        _accrueInterest(loan);

        uint256 totalOwed = loan.principal + loan.accruedInterest - loan.repaidAmount;
        if (amount > totalOwed) amount = totalOwed;

        IERC20(loan.borrowToken).safeTransferFrom(msg.sender, loan.lender, amount);
        loan.repaidAmount += amount;

        uint256 remaining = totalOwed - amount;
        emit LoanRepaid(loanId, amount, remaining);

        if (remaining == 0) {
            loan.status = LoanStatus.REPAID;
            activeLoanCount[loan.borrower]--;
            totalPoolBorrows -= loan.principal;
            vault.unlock(loan.borrower, loan.collateralToken, loan.collateralAmount);
            emit LoanFullyRepaid(loanId);
        }
    }

    // ── Liquidation ──────────────────────────────────────────────

    /**
     * @notice Liquidate an under-collateralised or overdue loan.
     *         Anyone can call this.
     *
     *         Conditions (either triggers liquidation):
     *         1. Collateral value < threshold % of outstanding debt
     *         2. Loan is past deadline and not fully repaid
     */
    function liquidate(uint256 loanId) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.status == LoanStatus.FUNDED, "Loan: not funded");

        _accrueInterest(loan);
        uint256 totalOwed = loan.principal + loan.accruedInterest - loan.repaidAmount;

        bool pastDeadline = block.timestamp > loan.deadline;
        bool underCollateralised = _isUnderCollateralised(loan, totalOwed);

        require(pastDeadline || underCollateralised, "Loan: not liquidatable");

        loan.status = LoanStatus.LIQUIDATED;
        activeLoanCount[loan.borrower]--;
        totalPoolBorrows -= loan.principal;

        // Compute collateral to seize: enough to cover debt at current prices
        uint256 debtValue = _tokenValue(loan.borrowToken, totalOwed);
        uint256 collateralPrice = tokenPrice[loan.collateralToken];
        uint256 seizeAmount = collateralPrice > 0
            ? (debtValue * 1e18) / collateralPrice
            : loan.collateralAmount;

        if (seizeAmount > loan.collateralAmount) seizeAmount = loan.collateralAmount;

        // Mirror the vault's seizure math (seize + bonus) to compute the true leftover
        uint256 bonusBps = vault.liquidationBonusBps();
        uint256 bonus = (seizeAmount * bonusBps) / BPS;
        uint256 totalSeized = seizeAmount + bonus;
        if (totalSeized > loan.collateralAmount) totalSeized = loan.collateralAmount;

        vault.liquidate(loan.borrower, msg.sender, loan.collateralToken, seizeAmount);

        // Unlock any remaining collateral back to borrower
        uint256 leftover = loan.collateralAmount - totalSeized;
        if (leftover > 0) {
            vault.unlock(loan.borrower, loan.collateralToken, leftover);
        }

        emit LoanLiquidated(loanId, msg.sender);
    }

    // ── View helpers ─────────────────────────────────────────────

    /**
     * @notice Current total owed on a loan (principal + accrued − repaid).
     */
    function outstandingDebt(uint256 loanId) external view returns (uint256) {
        Loan storage loan = loans[loanId];
        if (loan.status != LoanStatus.FUNDED) return 0;

        uint256 elapsed = block.timestamp - loan.fundedAt;
        uint256 interest = (loan.principal * loan.interestRateBps * elapsed)
            / (BPS * SECONDS_PER_YEAR);
        uint256 total = loan.principal + loan.accruedInterest + interest;
        if (total <= loan.repaidAmount) return 0;
        return total - loan.repaidAmount;
    }

    function getLoan(uint256 loanId) external view returns (Loan memory) {
        return loans[loanId];
    }

    function isLiquidatable(uint256 loanId) external view returns (bool) {
        Loan storage loan = loans[loanId];
        if (loan.status != LoanStatus.FUNDED) return false;

        uint256 elapsed = block.timestamp - loan.fundedAt;
        uint256 interest = (loan.principal * loan.interestRateBps * elapsed)
            / (BPS * SECONDS_PER_YEAR);
        uint256 totalOwed = loan.principal + loan.accruedInterest + interest - loan.repaidAmount;

        return block.timestamp > loan.deadline || _isUnderCollateralised(loan, totalOwed);
    }

    // ── Default handling ────────────────────────────────────────

    /**
     * @notice Mark a funded loan as defaulted. Can be called by anyone
     *         if the loan is past deadline, or by the owner for manual default.
     *         Emits LoanDefaulted event for backend indexing.
     */
    function markDefault(uint256 loanId) external nonReentrant {
        Loan storage loan = loans[loanId];
        require(loan.status == LoanStatus.FUNDED, "Loan: not funded");

        bool pastDeadline = block.timestamp > loan.deadline;
        bool isOwnerCall = msg.sender == owner();
        require(pastDeadline || isOwnerCall, "Loan: not yet defaultable");

        _accrueInterest(loan);
        uint256 totalOwed = loan.principal + loan.accruedInterest - loan.repaidAmount;

        loan.status = LoanStatus.LIQUIDATED;
        activeLoanCount[loan.borrower]--;
        totalPoolBorrows -= loan.principal;

        uint256 daysOverdue = 0;
        if (block.timestamp > loan.deadline) {
            daysOverdue = (block.timestamp - loan.deadline) / 1 days;
        }

        string memory severity;
        if (daysOverdue > 120 || totalOwed > 5000e18) {
            severity = "critical";
        } else if (daysOverdue > 60) {
            severity = "severe";
        } else if (daysOverdue > 14) {
            severity = "standard";
        } else {
            severity = "minor";
        }

        emit LoanDefaulted(
            loanId,
            loan.borrower,
            loan.principal - loan.repaidAmount,
            loan.accruedInterest,
            daysOverdue,
            severity
        );
    }

    // ── Admin ────────────────────────────────────────────────────

    function setPrice(address token, uint256 price) external onlyOwner {
        tokenPrice[token] = price;
        emit PriceUpdated(token, price);
    }

    function setMinTrustScore(uint256 _score) external onlyOwner {
        minTrustScore = _score;
    }

    function setMaxActiveLoans(uint256 _max) external onlyOwner {
        maxActiveLoansPerUser = _max;
    }

    function setPoolSupply(uint256 _supply) external onlyOwner {
        totalPoolSupply = _supply;
    }

    // ── Dynamic collateral ratio ──────────────────────────────────

    /**
     * @notice Returns the required collateral ratio (in BPS) for a given trust score.
     *         Reverts if the score is below the eligibility threshold (450).
     *
     *         Score range → Collateral
     *         < 450       → NOT ELIGIBLE (revert)
     *         450 – 599   → 120 % (12000 bps)
     *         600 – 749   →  80 % ( 8000 bps)
     *         750 – 849   →  60 % ( 6000 bps)
     *         850 – 949   →  40 % ( 4000 bps)
     *         950 – 1000  →  20 % ( 2000 bps)
     */
    function getCollateralRatioBps(uint256 trustScore) public pure returns (uint256) {
        require(trustScore >= 450, "Loan: score not eligible");
        if (trustScore < 600) return 12_000;
        if (trustScore < 750) return  8_000;
        if (trustScore < 850) return  6_000;
        if (trustScore < 950) return  4_000;
        return 2_000; // 950 – 1000
    }

    // ── Internal ─────────────────────────────────────────────────

    function _accrueInterest(Loan storage loan) internal {
        uint256 elapsed = block.timestamp - loan.fundedAt;
        uint256 totalInterest = (loan.principal * loan.interestRateBps * elapsed)
            / (BPS * SECONDS_PER_YEAR);
        loan.accruedInterest = totalInterest;
    }

    function _requireSufficientCollateral(
        address borrowToken,
        address collateralToken,
        uint256 principal,
        uint256 collateralAmount,
        uint256 ratioBps
    ) internal view {
        uint256 borrowValue = _tokenValue(borrowToken, principal);
        uint256 collateralValue = _tokenValue(collateralToken, collateralAmount);

        uint256 requiredCollateral = (borrowValue * ratioBps) / BPS;
        require(collateralValue >= requiredCollateral, "Loan: insufficient collateral value");
    }

    function _tokenValue(address token, uint256 amount) internal view returns (uint256) {
        uint256 price = tokenPrice[token];
        require(price > 0, "Loan: no price for token");
        return (amount * price) / 1e18;
    }

    function _isUnderCollateralised(
        Loan storage loan,
        uint256 totalOwed
    ) internal view returns (bool) {
        uint256 threshold = vault.liquidationThresholdBps(loan.collateralToken);
        if (threshold == 0) return false;

        uint256 debtValue = _tokenValue(loan.borrowToken, totalOwed);
        uint256 collateralValue = _tokenValue(loan.collateralToken, loan.collateralAmount);

        return collateralValue < (debtValue * threshold) / BPS;
    }
}
