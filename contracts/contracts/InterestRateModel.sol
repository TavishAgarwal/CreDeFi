// SPDX-License-Identifier: MIT
pragma solidity ^0.8.27;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title  InterestRateModel
 * @notice Computes annualised borrow rates from two dimensions:
 *         1. Pool utilisation  (borrowed / total_supply)
 *         2. Borrower trust score  (0–1000, from SoulboundReputationNFT)
 *
 *         The model uses a kinked utilisation curve (like Compound/Aave)
 *         and then applies a trust-based discount on the resulting rate.
 *
 *         All rates are expressed in basis points (1 bp = 0.01 %).
 */
contract InterestRateModel is Ownable {
    // ── Utilisation curve parameters (basis points) ──────────────
    uint256 public baseRate;          // rate at 0 % utilisation
    uint256 public slopeBeforeKink;   // slope below the kink
    uint256 public slopeAfterKink;    // steep slope above the kink
    uint256 public kinkUtilisation;   // kink point  (in bp, e.g. 8000 = 80 %)

    // ── Trust discount parameters ────────────────────────────────
    uint256 public maxTrustDiscount;  // max discount for score = 1000 (bp)
    uint256 public constant MAX_TRUST_SCORE = 1000;

    // ── Precision ────────────────────────────────────────────────
    uint256 public constant BPS = 10_000;

    event ParametersUpdated(
        uint256 baseRate,
        uint256 slopeBeforeKink,
        uint256 slopeAfterKink,
        uint256 kinkUtilisation,
        uint256 maxTrustDiscount
    );

    constructor(
        uint256 _baseRate,
        uint256 _slopeBeforeKink,
        uint256 _slopeAfterKink,
        uint256 _kinkUtilisation,
        uint256 _maxTrustDiscount
    ) Ownable(msg.sender) {
        _setParams(_baseRate, _slopeBeforeKink, _slopeAfterKink, _kinkUtilisation, _maxTrustDiscount);
    }

    // ── Views ────────────────────────────────────────────────────

    /**
     * @notice Compute the utilisation-based rate (before trust discount).
     * @param  totalSupply  Total assets in the pool.
     * @param  totalBorrows Total currently borrowed.
     * @return rateBps      Annual rate in basis points.
     */
    function utilisationRate(
        uint256 totalSupply,
        uint256 totalBorrows
    ) public view returns (uint256 rateBps) {
        if (totalSupply == 0) return baseRate;

        uint256 util = (totalBorrows * BPS) / totalSupply; // in bp
        if (util <= kinkUtilisation) {
            rateBps = baseRate + (slopeBeforeKink * util) / BPS;
        } else {
            uint256 rateAtKink = baseRate + (slopeBeforeKink * kinkUtilisation) / BPS;
            uint256 excessUtil = util - kinkUtilisation;
            rateBps = rateAtKink + (slopeAfterKink * excessUtil) / BPS;
        }
    }

    /**
     * @notice Apply a trust-score discount to a base rate.
     * @dev    Discount scales linearly: score 0 → 0 %, score 1000 → maxTrustDiscount.
     * @param  rateBps     The pre-discount rate.
     * @param  trustScore  Borrower's on-chain trust score (0–1000).
     * @return discounted  The final rate after discount (floored at 1 bp).
     */
    function applyTrustDiscount(
        uint256 rateBps,
        uint256 trustScore
    ) public view returns (uint256 discounted) {
        if (trustScore > MAX_TRUST_SCORE) trustScore = MAX_TRUST_SCORE;

        uint256 discountBps = (maxTrustDiscount * trustScore) / MAX_TRUST_SCORE;
        uint256 discountAmount = (rateBps * discountBps) / BPS;

        discounted = rateBps > discountAmount ? rateBps - discountAmount : 1;
    }

    /**
     * @notice Full rate computation: utilisation curve + trust discount.
     */
    function computeRate(
        uint256 totalSupply,
        uint256 totalBorrows,
        uint256 trustScore
    ) external view returns (uint256) {
        uint256 utilRate = utilisationRate(totalSupply, totalBorrows);
        return applyTrustDiscount(utilRate, trustScore);
    }

    // ── Admin ────────────────────────────────────────────────────

    function setParameters(
        uint256 _baseRate,
        uint256 _slopeBeforeKink,
        uint256 _slopeAfterKink,
        uint256 _kinkUtilisation,
        uint256 _maxTrustDiscount
    ) external onlyOwner {
        _setParams(_baseRate, _slopeBeforeKink, _slopeAfterKink, _kinkUtilisation, _maxTrustDiscount);
    }

    function _setParams(
        uint256 _baseRate,
        uint256 _slopeBeforeKink,
        uint256 _slopeAfterKink,
        uint256 _kinkUtilisation,
        uint256 _maxTrustDiscount
    ) internal {
        require(_kinkUtilisation <= BPS, "kink > 100%");
        require(_maxTrustDiscount <= BPS, "discount > 100%");

        baseRate = _baseRate;
        slopeBeforeKink = _slopeBeforeKink;
        slopeAfterKink = _slopeAfterKink;
        kinkUtilisation = _kinkUtilisation;
        maxTrustDiscount = _maxTrustDiscount;

        emit ParametersUpdated(_baseRate, _slopeBeforeKink, _slopeAfterKink, _kinkUtilisation, _maxTrustDiscount);
    }
}
