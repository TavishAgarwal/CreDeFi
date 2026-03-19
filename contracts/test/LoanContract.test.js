const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("LoanContract", function () {
  let loanC, vault, rateModel, nft;
  let borrowToken, collateralToken;
  let owner, borrower, lender, liquidator;

  const BPS = 10000n;
  const ONE = ethers.parseEther("1");
  const PRICE = ethers.parseEther("1"); // 1 token = $1 (1e18)
  const DAY = 86400;

  async function deployFixture() {
    [owner, borrower, lender, liquidator] = await ethers.getSigners();

    // Deploy mock tokens
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    borrowToken = await MockERC20.deploy("USDC", "USDC", 18);
    collateralToken = await MockERC20.deploy("WETH", "WETH", 18);

    // Deploy InterestRateModel
    const RateModel = await ethers.getContractFactory("InterestRateModel");
    rateModel = await RateModel.deploy(200, 1000, 5000, 8000, 3000);

    // Deploy CollateralVault
    const Vault = await ethers.getContractFactory("CollateralVault");
    vault = await Vault.deploy(500);

    // Deploy SoulboundReputationNFT
    const NFT = await ethers.getContractFactory("SoulboundReputationNFT");
    nft = await NFT.deploy();

    // Deploy LoanContract (no more collateralRatioBps param)
    const Loan = await ethers.getContractFactory("LoanContract");
    loanC = await Loan.deploy(
      await vault.getAddress(),
      await rateModel.getAddress(),
      await nft.getAddress(),
      450,   // minTrustScore (aligned with dynamic collateral)
      3      // max active loans
    );

    // Wire up
    await vault.setLoanContract(await loanC.getAddress());
    await vault.configureToken(await collateralToken.getAddress(), 8000); // 80 % liquidation threshold

    // Set prices
    await loanC.setPrice(await borrowToken.getAddress(), PRICE);
    await loanC.setPrice(await collateralToken.getAddress(), PRICE);

    // Set pool supply for rate calculation
    await loanC.setPoolSupply(ethers.parseEther("100000"));

    // Mint reputation for borrower (score 700 → 80% collateral tier)
    await nft.mintReputation(borrower.address, 700, "GOOD");

    // Fund accounts
    await borrowToken.mint(lender.address, ethers.parseEther("100000"));
    await collateralToken.mint(borrower.address, ethers.parseEther("10000"));

    // Approvals
    await borrowToken.connect(lender).approve(await loanC.getAddress(), ethers.MaxUint256);
    await collateralToken.connect(borrower).approve(await vault.getAddress(), ethers.MaxUint256);

    // Borrower deposits collateral
    await vault.connect(borrower).deposit(
      await collateralToken.getAddress(),
      ethers.parseEther("5000")
    );
  }

  beforeEach(async function () {
    await deployFixture();
  });

  // ═══════════════════════════════════════════════════════════════
  // Dynamic Collateral Ratio  (NEW)
  // ═══════════════════════════════════════════════════════════════

  describe("getCollateralRatioBps", function () {
    it("reverts for score < 450", async function () {
      await expect(loanC.getCollateralRatioBps(0))
        .to.be.revertedWith("Loan: score not eligible");
      await expect(loanC.getCollateralRatioBps(449))
        .to.be.revertedWith("Loan: score not eligible");
    });

    it("returns 12000 bps (120%) for score 450–599", async function () {
      expect(await loanC.getCollateralRatioBps(450)).to.equal(12000n);
      expect(await loanC.getCollateralRatioBps(500)).to.equal(12000n);
      expect(await loanC.getCollateralRatioBps(599)).to.equal(12000n);
    });

    it("returns 8000 bps (80%) for score 600–749", async function () {
      expect(await loanC.getCollateralRatioBps(600)).to.equal(8000n);
      expect(await loanC.getCollateralRatioBps(700)).to.equal(8000n);
      expect(await loanC.getCollateralRatioBps(749)).to.equal(8000n);
    });

    it("returns 6000 bps (60%) for score 750–849", async function () {
      expect(await loanC.getCollateralRatioBps(750)).to.equal(6000n);
      expect(await loanC.getCollateralRatioBps(800)).to.equal(6000n);
      expect(await loanC.getCollateralRatioBps(849)).to.equal(6000n);
    });

    it("returns 4000 bps (40%) for score 850–949", async function () {
      expect(await loanC.getCollateralRatioBps(850)).to.equal(4000n);
      expect(await loanC.getCollateralRatioBps(900)).to.equal(4000n);
      expect(await loanC.getCollateralRatioBps(949)).to.equal(4000n);
    });

    it("returns 2000 bps (20%) for score 950–1000", async function () {
      expect(await loanC.getCollateralRatioBps(950)).to.equal(2000n);
      expect(await loanC.getCollateralRatioBps(1000)).to.equal(2000n);
    });

    it("handles exact boundary values correctly", async function () {
      // Each boundary transitions to the next tier
      expect(await loanC.getCollateralRatioBps(450)).to.equal(12000n);  // first eligible
      expect(await loanC.getCollateralRatioBps(600)).to.equal(8000n);   // tier jump
      expect(await loanC.getCollateralRatioBps(750)).to.equal(6000n);   // tier jump
      expect(await loanC.getCollateralRatioBps(850)).to.equal(4000n);   // tier jump
      expect(await loanC.getCollateralRatioBps(950)).to.equal(2000n);   // best tier
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Create Loan  (UPDATED for dynamic collateral)
  // ═══════════════════════════════════════════════════════════════

  describe("Create Loan", function () {
    it("creates a loan with score 700 → 80% collateral", async function () {
      // Score 700 → 80% ratio → 1000 principal needs 800 collateral
      const tx = await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("800"), // exactly 80%
        30 * DAY
      );

      await expect(tx).to.emit(loanC, "LoanCreated").withArgs(1, borrower.address, ethers.parseEther("1000"));

      const loan = await loanC.getLoan(1);
      expect(loan.borrower).to.equal(borrower.address);
      expect(loan.principal).to.equal(ethers.parseEther("1000"));
      expect(loan.collateralAmount).to.equal(ethers.parseEther("800"));
      expect(loan.status).to.equal(0); // OPEN
    });

    it("accepts over-collateralised loan", async function () {
      // Score 700 → 80%. Providing 120% should still pass
      await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("1200"),
        30 * DAY
      );
      const loan = await loanC.getLoan(1);
      expect(loan.collateralAmount).to.equal(ethers.parseEther("1200"));
    });

    it("reverts if trust score too low (< 450)", async function () {
      // Mint a low-score reputation for lender as a new borrower
      await nft.mintReputation(lender.address, 100, "VERY_POOR");
      await collateralToken.mint(lender.address, ethers.parseEther("5000"));
      await collateralToken.connect(lender).approve(await vault.getAddress(), ethers.MaxUint256);
      await vault.connect(lender).deposit(await collateralToken.getAddress(), ethers.parseEther("5000"));

      await expect(
        loanC.connect(lender).createLoan(
          await borrowToken.getAddress(),
          await collateralToken.getAddress(),
          ethers.parseEther("100"),
          ethers.parseEther("200"),
          30 * DAY
        )
      ).to.be.revertedWith("Loan: trust score too low");
    });

    it("reverts if collateral insufficient for dynamic ratio", async function () {
      // Score 700 → 80% required. 1000 principal needs ≥ 800.  Supply only 700.
      await expect(
        loanC.connect(borrower).createLoan(
          await borrowToken.getAddress(),
          await collateralToken.getAddress(),
          ethers.parseEther("1000"),
          ethers.parseEther("700"),
          30 * DAY
        )
      ).to.be.revertedWith("Loan: insufficient collateral value");
    });

    it("respects higher collateral for lower trust scores", async function () {
      // Create a user with score 500 → 120% collateral required
      await nft.mintReputation(liquidator.address, 500, "FAIR");
      await collateralToken.mint(liquidator.address, ethers.parseEther("5000"));
      await collateralToken.connect(liquidator).approve(await vault.getAddress(), ethers.MaxUint256);
      await vault.connect(liquidator).deposit(await collateralToken.getAddress(), ethers.parseEther("5000"));
      await borrowToken.connect(lender).approve(await loanC.getAddress(), ethers.MaxUint256);

      // 1000 principal, 120% → needs 1200.  1100 should fail.
      await expect(
        loanC.connect(liquidator).createLoan(
          await borrowToken.getAddress(),
          await collateralToken.getAddress(),
          ethers.parseEther("1000"),
          ethers.parseEther("1100"),
          30 * DAY
        )
      ).to.be.revertedWith("Loan: insufficient collateral value");

      // 1200 should pass
      await loanC.connect(liquidator).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("1200"),
        30 * DAY
      );
    });

    it("reverts for zero principal", async function () {
      await expect(
        loanC.connect(borrower).createLoan(
          await borrowToken.getAddress(),
          await collateralToken.getAddress(),
          0,
          ethers.parseEther("1500"),
          30 * DAY
        )
      ).to.be.revertedWith("Loan: zero principal");
    });

    it("reverts for too short duration", async function () {
      await expect(
        loanC.connect(borrower).createLoan(
          await borrowToken.getAddress(),
          await collateralToken.getAddress(),
          ethers.parseEther("100"),
          ethers.parseEther("200"),
          3600 // 1 hour (< 1 day)
        )
      ).to.be.revertedWith("Loan: duration too short");
    });

    it("enforces max active loans", async function () {
      for (let i = 0; i < 3; i++) {
        await loanC.connect(borrower).createLoan(
          await borrowToken.getAddress(),
          await collateralToken.getAddress(),
          ethers.parseEther("100"),
          ethers.parseEther("80"), // 80% of 100
          30 * DAY
        );
      }

      await expect(
        loanC.connect(borrower).createLoan(
          await borrowToken.getAddress(),
          await collateralToken.getAddress(),
          ethers.parseEther("100"),
          ethers.parseEther("80"),
          30 * DAY
        )
      ).to.be.revertedWith("Loan: too many active loans");
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Cancel Loan
  // ═══════════════════════════════════════════════════════════════

  describe("Cancel Loan", function () {
    beforeEach(async function () {
      await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("800"), // 80% for score 700
        30 * DAY
      );
    });

    it("cancels and unlocks collateral", async function () {
      await expect(loanC.connect(borrower).cancelLoan(1))
        .to.emit(loanC, "LoanCancelled").withArgs(1);

      const loan = await loanC.getLoan(1);
      expect(loan.status).to.equal(4); // CANCELLED

      const free = await vault.freeCollateral(borrower.address, await collateralToken.getAddress());
      expect(free).to.equal(ethers.parseEther("5000")); // all collateral free again
    });

    it("reverts if not borrower", async function () {
      await expect(loanC.connect(lender).cancelLoan(1))
        .to.be.revertedWith("Loan: not borrower");
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Fund Loan
  // ═══════════════════════════════════════════════════════════════

  describe("Fund Loan", function () {
    beforeEach(async function () {
      await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("800"),
        30 * DAY
      );
    });

    it("funds a loan, transfers principal to borrower", async function () {
      const borrowerBalBefore = await borrowToken.balanceOf(borrower.address);

      await expect(loanC.connect(lender).fundLoan(1))
        .to.emit(loanC, "LoanFunded");

      const loan = await loanC.getLoan(1);
      expect(loan.lender).to.equal(lender.address);
      expect(loan.status).to.equal(1); // FUNDED
      expect(loan.interestRateBps).to.be.gt(0);

      const borrowerBalAfter = await borrowToken.balanceOf(borrower.address);
      expect(borrowerBalAfter - borrowerBalBefore).to.equal(ethers.parseEther("1000"));
    });

    it("reverts self-funding", async function () {
      await borrowToken.mint(borrower.address, ethers.parseEther("10000"));
      await borrowToken.connect(borrower).approve(await loanC.getAddress(), ethers.MaxUint256);

      await expect(loanC.connect(borrower).fundLoan(1))
        .to.be.revertedWith("Loan: self-fund");
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Repay
  // ═══════════════════════════════════════════════════════════════

  describe("Repay", function () {
    beforeEach(async function () {
      await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("800"),
        30 * DAY
      );
      await loanC.connect(lender).fundLoan(1);

      // Give borrower tokens to repay
      await borrowToken.mint(borrower.address, ethers.parseEther("2000"));
      await borrowToken.connect(borrower).approve(await loanC.getAddress(), ethers.MaxUint256);
    });

    it("partial repay reduces outstanding debt", async function () {
      await time.increase(15 * DAY);

      await expect(loanC.connect(borrower).repay(1, ethers.parseEther("500")))
        .to.emit(loanC, "LoanRepaid");

      const loan = await loanC.getLoan(1);
      expect(loan.status).to.equal(1); // still FUNDED
      expect(loan.repaidAmount).to.equal(ethers.parseEther("500"));
    });

    it("full repay marks loan REPAID and unlocks collateral", async function () {
      await time.increase(1 * DAY);

      await expect(loanC.connect(borrower).repay(1, ethers.parseEther("2000")))
        .to.emit(loanC, "LoanFullyRepaid").withArgs(1);

      const loan = await loanC.getLoan(1);
      expect(loan.status).to.equal(2); // REPAID

      const free = await vault.freeCollateral(borrower.address, await collateralToken.getAddress());
      expect(free).to.equal(ethers.parseEther("5000")); // all free
    });

    it("reverts repay on non-funded loan", async function () {
      await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("100"),
        ethers.parseEther("80"),
        30 * DAY
      );
      await loanC.connect(borrower).cancelLoan(2);

      await expect(loanC.connect(borrower).repay(2, ethers.parseEther("50")))
        .to.be.revertedWith("Loan: not funded");
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Liquidation
  // ═══════════════════════════════════════════════════════════════

  describe("Liquidation", function () {
    beforeEach(async function () {
      // Over-collateralise (1200 > 80% minimum of 800) so loan starts healthy
      await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("1200"),
        30 * DAY
      );
      await loanC.connect(lender).fundLoan(1);
    });

    it("liquidates overdue loan", async function () {
      await time.increase(31 * DAY);

      await expect(loanC.connect(liquidator).liquidate(1))
        .to.emit(loanC, "LoanLiquidated")
        .withArgs(1, liquidator.address);

      const loan = await loanC.getLoan(1);
      expect(loan.status).to.equal(3); // LIQUIDATED

      expect(await collateralToken.balanceOf(liquidator.address)).to.be.gt(0);
    });

    it("liquidates under-collateralised loan", async function () {
      // 1200 collateral at $1 = $1200, debt ~ $1000
      // Liquidation threshold 80%: liquidatable when collateral < 80% of debt
      // Drop collateral price to $0.60 → value = 720 < 800 → liquidatable
      await loanC.setPrice(await collateralToken.getAddress(), ethers.parseEther("0.6"));

      await expect(loanC.connect(liquidator).liquidate(1))
        .to.emit(loanC, "LoanLiquidated");
    });

    it("reverts if not liquidatable", async function () {
      // Loan is over-collateralised (1200 >> 800 threshold) and not overdue
      await expect(loanC.connect(liquidator).liquidate(1))
        .to.be.revertedWith("Loan: not liquidatable");
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // View functions
  // ═══════════════════════════════════════════════════════════════

  describe("View functions", function () {
    beforeEach(async function () {
      await loanC.connect(borrower).createLoan(
        await borrowToken.getAddress(),
        await collateralToken.getAddress(),
        ethers.parseEther("1000"),
        ethers.parseEther("800"),
        30 * DAY
      );
      await loanC.connect(lender).fundLoan(1);
    });

    it("outstandingDebt accrues over time", async function () {
      const debt0 = await loanC.outstandingDebt(1);
      await time.increase(30 * DAY);
      const debt30 = await loanC.outstandingDebt(1);

      expect(debt30).to.be.gt(debt0);
      expect(debt30).to.be.gt(ethers.parseEther("1000"));
    });

    it("isLiquidatable returns false for healthy loan", async function () {
      expect(await loanC.isLiquidatable(1)).to.be.false;
    });

    it("isLiquidatable returns true for overdue loan", async function () {
      await time.increase(31 * DAY);
      expect(await loanC.isLiquidatable(1)).to.be.true;
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Admin
  // ═══════════════════════════════════════════════════════════════

  describe("Admin", function () {
    it("owner sets min trust score", async function () {
      await loanC.setMinTrustScore(500);
      expect(await loanC.minTrustScore()).to.equal(500n);
    });

    it("non-owner cannot set prices", async function () {
      await expect(loanC.connect(borrower).setPrice(await borrowToken.getAddress(), PRICE))
        .to.be.revertedWithCustomError(loanC, "OwnableUnauthorizedAccount");
    });
  });
});
