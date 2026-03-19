const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("InterestRateModel", function () {
  let model, owner, other;

  const BASE_RATE = 200n;        // 2 %
  const SLOPE_BEFORE = 1000n;    // 10 %
  const SLOPE_AFTER = 5000n;     // 50 %
  const KINK = 8000n;            // 80 %
  const MAX_DISCOUNT = 3000n;    // 30 %
  const BPS = 10000n;

  beforeEach(async function () {
    [owner, other] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("InterestRateModel");
    model = await Factory.deploy(BASE_RATE, SLOPE_BEFORE, SLOPE_AFTER, KINK, MAX_DISCOUNT);
  });

  describe("Constructor", function () {
    it("sets initial parameters correctly", async function () {
      expect(await model.baseRate()).to.equal(BASE_RATE);
      expect(await model.slopeBeforeKink()).to.equal(SLOPE_BEFORE);
      expect(await model.slopeAfterKink()).to.equal(SLOPE_AFTER);
      expect(await model.kinkUtilisation()).to.equal(KINK);
      expect(await model.maxTrustDiscount()).to.equal(MAX_DISCOUNT);
    });

    it("reverts if kink > 100 %", async function () {
      const F = await ethers.getContractFactory("InterestRateModel");
      await expect(F.deploy(200, 1000, 5000, 10001, 3000)).to.be.revertedWith("kink > 100%");
    });
  });

  describe("utilisationRate", function () {
    it("returns baseRate when supply is 0", async function () {
      expect(await model.utilisationRate(0, 0)).to.equal(BASE_RATE);
    });

    it("returns baseRate when no borrows", async function () {
      expect(await model.utilisationRate(ethers.parseEther("1000"), 0)).to.equal(BASE_RATE);
    });

    it("computes rate below kink correctly", async function () {
      // 50 % utilisation → baseRate + slopeBeforeKink * 5000 / 10000 = 200 + 500 = 700
      const rate = await model.utilisationRate(ethers.parseEther("1000"), ethers.parseEther("500"));
      expect(rate).to.equal(700n);
    });

    it("computes rate at kink correctly", async function () {
      // 80 % → 200 + 1000 * 8000 / 10000 = 200 + 800 = 1000
      const rate = await model.utilisationRate(ethers.parseEther("1000"), ethers.parseEther("800"));
      expect(rate).to.equal(1000n);
    });

    it("computes rate above kink correctly", async function () {
      // 90 % → rateAtKink + slopeAfter * excessUtil / BPS
      // rateAtKink = 200 + 800 = 1000
      // excess = 9000 - 8000 = 1000
      // rate = 1000 + 5000 * 1000 / 10000 = 1000 + 500 = 1500
      const rate = await model.utilisationRate(ethers.parseEther("1000"), ethers.parseEther("900"));
      expect(rate).to.equal(1500n);
    });

    it("handles 100 % utilisation", async function () {
      // excess = 10000 - 8000 = 2000; 1000 + 5000*2000/10000 = 1000 + 1000 = 2000
      const rate = await model.utilisationRate(ethers.parseEther("1000"), ethers.parseEther("1000"));
      expect(rate).to.equal(2000n);
    });
  });

  describe("applyTrustDiscount", function () {
    it("returns unchanged rate for score 0", async function () {
      expect(await model.applyTrustDiscount(1000, 0)).to.equal(1000n);
    });

    it("applies maximum discount for score 1000", async function () {
      // discountBps = 3000 * 1000 / 1000 = 3000
      // discountAmount = 1000 * 3000 / 10000 = 300
      // result = 1000 - 300 = 700
      expect(await model.applyTrustDiscount(1000, 1000)).to.equal(700n);
    });

    it("applies proportional discount for score 500", async function () {
      // discountBps = 3000 * 500 / 1000 = 1500
      // discountAmount = 1000 * 1500 / 10000 = 150
      // result = 850
      expect(await model.applyTrustDiscount(1000, 500)).to.equal(850n);
    });

    it("floors at 1 bp for extremely high discount", async function () {
      // Very low rate + high score → floors at 1
      expect(await model.applyTrustDiscount(1, 1000)).to.equal(1n);
    });

    it("caps trust score at 1000", async function () {
      // score 2000 is capped to 1000
      const a = await model.applyTrustDiscount(1000, 2000);
      const b = await model.applyTrustDiscount(1000, 1000);
      expect(a).to.equal(b);
    });
  });

  describe("computeRate (end-to-end)", function () {
    it("combines utilisation and trust discount", async function () {
      // 50% util → 700 bp, trust 1000 → 700 * 0.7 = 490
      const rate = await model.computeRate(ethers.parseEther("1000"), ethers.parseEther("500"), 1000);
      expect(rate).to.equal(490n);
    });
  });

  describe("Admin", function () {
    it("owner can update parameters", async function () {
      await expect(model.setParameters(100, 500, 2000, 7000, 2000))
        .to.emit(model, "ParametersUpdated");
      expect(await model.baseRate()).to.equal(100n);
    });

    it("non-owner cannot update", async function () {
      await expect(model.connect(other).setParameters(100, 500, 2000, 7000, 2000))
        .to.be.revertedWithCustomError(model, "OwnableUnauthorizedAccount");
    });
  });
});
