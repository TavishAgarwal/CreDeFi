const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("SoulboundReputationNFT", function () {
  let nft, owner, updater, userA, userB;

  beforeEach(async function () {
    [owner, updater, userA, userB] = await ethers.getSigners();

    const Factory = await ethers.getContractFactory("SoulboundReputationNFT");
    nft = await Factory.deploy();

    const UPDATER_ROLE = await nft.SCORE_UPDATER_ROLE();
    await nft.grantRole(UPDATER_ROLE, updater.address);
  });

  describe("Minting", function () {
    it("mints a reputation NFT with correct data", async function () {
      await expect(nft.connect(updater).mintReputation(userA.address, 750, "GOOD"))
        .to.emit(nft, "ReputationMinted")
        .withArgs(userA.address, 1);

      expect(await nft.balanceOf(userA.address)).to.equal(1n);
      expect(await nft.ownerOf(1)).to.equal(userA.address);

      const [score, updatedAt, tier] = await nft.reputationOf(userA.address);
      expect(score).to.equal(750n);
      expect(tier).to.equal("GOOD");
      expect(updatedAt).to.be.gt(0);
    });

    it("assigns incrementing token IDs", async function () {
      await nft.connect(updater).mintReputation(userA.address, 500, "FAIR");
      await nft.connect(updater).mintReputation(userB.address, 800, "EXCELLENT");

      expect(await nft.tokenOfOwner(userA.address)).to.equal(1n);
      expect(await nft.tokenOfOwner(userB.address)).to.equal(2n);
    });

    it("reverts on second mint for same address", async function () {
      await nft.connect(updater).mintReputation(userA.address, 500, "FAIR");
      await expect(nft.connect(updater).mintReputation(userA.address, 600, "GOOD"))
        .to.be.revertedWith("SBT: already minted");
    });

    it("reverts if score > 1000", async function () {
      await expect(nft.connect(updater).mintReputation(userA.address, 1001, "EXCELLENT"))
        .to.be.revertedWith("SBT: score out of range");
    });

    it("reverts when called by non-updater", async function () {
      await expect(nft.connect(userA).mintReputation(userA.address, 500, "FAIR"))
        .to.be.revertedWithCustomError(nft, "AccessControlUnauthorizedAccount");
    });
  });

  describe("Score updates", function () {
    beforeEach(async function () {
      await nft.connect(updater).mintReputation(userA.address, 500, "FAIR");
    });

    it("updates score and risk tier", async function () {
      await expect(nft.connect(updater).updateScore(userA.address, 850, "EXCELLENT"))
        .to.emit(nft, "ScoreUpdated")
        .withArgs(userA.address, 1, 850, "EXCELLENT");

      const [score, , tier] = await nft.reputationOf(userA.address);
      expect(score).to.equal(850n);
      expect(tier).to.equal("EXCELLENT");
    });

    it("reverts update for user without token", async function () {
      await expect(nft.connect(updater).updateScore(userB.address, 700, "GOOD"))
        .to.be.revertedWith("SBT: no token");
    });

    it("reverts if new score > 1000", async function () {
      await expect(nft.connect(updater).updateScore(userA.address, 1500, "EXCELLENT"))
        .to.be.revertedWith("SBT: score out of range");
    });
  });

  describe("trustScoreOf", function () {
    it("returns 0 for user with no token", async function () {
      expect(await nft.trustScoreOf(userB.address)).to.equal(0n);
    });

    it("returns correct score", async function () {
      await nft.connect(updater).mintReputation(userA.address, 720, "GOOD");
      expect(await nft.trustScoreOf(userA.address)).to.equal(720n);
    });
  });

  describe("Soulbound enforcement", function () {
    beforeEach(async function () {
      await nft.connect(updater).mintReputation(userA.address, 500, "FAIR");
    });

    it("reverts on transferFrom", async function () {
      await expect(
        nft.connect(userA).transferFrom(userA.address, userB.address, 1)
      ).to.be.revertedWith("Soulbound: non-transferable");
    });

    it("reverts on safeTransferFrom", async function () {
      await expect(
        nft.connect(userA)["safeTransferFrom(address,address,uint256)"](userA.address, userB.address, 1)
      ).to.be.revertedWith("Soulbound: non-transferable");
    });

    it("reverts on approve", async function () {
      await expect(nft.connect(userA).approve(userB.address, 1))
        .to.be.revertedWith("Soulbound: approval disabled");
    });

    it("reverts on setApprovalForAll", async function () {
      await expect(nft.connect(userA).setApprovalForAll(userB.address, true))
        .to.be.revertedWith("Soulbound: approval disabled");
    });
  });

  describe("ERC-165", function () {
    it("supports ERC721 interface", async function () {
      expect(await nft.supportsInterface("0x80ac58cd")).to.be.true;
    });

    it("supports AccessControl interface", async function () {
      expect(await nft.supportsInterface("0x7965db0b")).to.be.true;
    });
  });

  describe("Score Explainability", function () {
    it("mintReputationExplained emits ScoreExplained event", async function () {
      await expect(
        nft.connect(updater).mintReputationExplained(
          userA.address, 750, "GOOD", 600, 150, 0, "heuristic=60%,ml=15%,penalties=0"
        )
      )
        .to.emit(nft, "ScoreExplained")
        .withArgs(userA.address, 750, 600, 150, 0, "heuristic=60%,ml=15%,penalties=0");

      const [score, , tier] = await nft.reputationOf(userA.address);
      expect(score).to.equal(750n);
      expect(tier).to.equal("GOOD");
    });

    it("updateScoreExplained emits ScoreExplained event", async function () {
      await nft.connect(updater).mintReputation(userA.address, 500, "FAIR");

      await expect(
        nft.connect(updater).updateScoreExplained(
          userA.address, 850, "EXCELLENT", 700, 200, 50, "heuristic=70%,ml=20%,penalties=-50"
        )
      )
        .to.emit(nft, "ScoreExplained")
        .withArgs(userA.address, 850, 700, 200, 50, "heuristic=70%,ml=20%,penalties=-50");

      const [score, , tier] = await nft.reputationOf(userA.address);
      expect(score).to.equal(850n);
      expect(tier).to.equal("EXCELLENT");
    });

    it("mintReputationExplained also emits ReputationMinted and ScoreUpdated", async function () {
      const tx = nft.connect(updater).mintReputationExplained(
        userB.address, 600, "GOOD", 400, 200, 0, "test"
      );
      await expect(tx).to.emit(nft, "ReputationMinted").withArgs(userB.address, 1);
      await expect(tx).to.emit(nft, "ScoreUpdated").withArgs(userB.address, 1, 600, "GOOD");
    });
  });
});
