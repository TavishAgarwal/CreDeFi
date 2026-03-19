const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  console.log(
    "Balance:",
    hre.ethers.formatEther(
      await hre.ethers.provider.getBalance(deployer.address)
    )
  );

  // ── 0. Mock ERC-20 tokens (for local / test networks) ──────────
  const MockERC20 = await hre.ethers.getContractFactory("MockERC20");

  const usdc = await MockERC20.deploy("USD Coin", "USDC", 18);
  await usdc.waitForDeployment();
  const usdcAddr = await usdc.getAddress();
  console.log("MockUSDC:         ", usdcAddr);

  const weth = await MockERC20.deploy("Wrapped Ether", "WETH", 18);
  await weth.waitForDeployment();
  const wethAddr = await weth.getAddress();
  console.log("MockWETH:         ", wethAddr);

  // ── 1. InterestRateModel ───────────────────────────────────────
  const InterestRateModel =
    await hre.ethers.getContractFactory("InterestRateModel");
  const rateModel = await InterestRateModel.deploy(
    200, // baseRate: 2 %
    1000, // slopeBeforeKink: 10 %
    5000, // slopeAfterKink: 50 %
    8000, // kinkUtilisation: 80 %
    3000 // maxTrustDiscount: 30 %
  );
  await rateModel.waitForDeployment();
  const rateModelAddr = await rateModel.getAddress();
  console.log("InterestRateModel:", rateModelAddr);

  // ── 2. CollateralVault ─────────────────────────────────────────
  const CollateralVault =
    await hre.ethers.getContractFactory("CollateralVault");
  const vault = await CollateralVault.deploy(500); // 5 % liquidation bonus
  await vault.waitForDeployment();
  const vaultAddr = await vault.getAddress();
  console.log("CollateralVault:  ", vaultAddr);

  // ── 3. SoulboundReputationNFT ──────────────────────────────────
  const SoulboundReputationNFT = await hre.ethers.getContractFactory(
    "SoulboundReputationNFT"
  );
  const nft = await SoulboundReputationNFT.deploy();
  await nft.waitForDeployment();
  const nftAddr = await nft.getAddress();
  console.log("SoulboundRepNFT:  ", nftAddr);

  // ── 4. LoanContract ────────────────────────────────────────────
  const LoanContract = await hre.ethers.getContractFactory("LoanContract");
  const loan = await LoanContract.deploy(
    vaultAddr,
    rateModelAddr,
    nftAddr,
    450, // minTrustScore (aligns with dynamic collateral eligibility)
    3 // maxActiveLoansPerUser
  );
  await loan.waitForDeployment();
  const loanAddr = await loan.getAddress();
  console.log("LoanContract:     ", loanAddr);

  // ── 5. Wire up contracts ───────────────────────────────────────
  await vault.setLoanContract(loanAddr);
  console.log("Vault authorised LoanContract");

  // Configure WETH as collateral token (80 % liquidation threshold)
  await vault.configureToken(wethAddr, 8000);
  console.log("Vault configured WETH as collateral");

  // Set initial prices: 1 USDC = $1, 1 WETH = $2000
  const USDC_PRICE = hre.ethers.parseEther("1");
  const WETH_PRICE = hre.ethers.parseEther("2000");
  await loan.setPrice(usdcAddr, USDC_PRICE);
  await loan.setPrice(wethAddr, WETH_PRICE);
  console.log("Prices set: USDC=$1, WETH=$2000");

  // Set pool supply for interest rate calculation
  await loan.setPoolSupply(hre.ethers.parseEther("100000"));
  console.log("Pool supply set to 100,000");

  // ── 6. Write deployment addresses ──────────────────────────────
  const addresses = {
    deployer: deployer.address,
    MockUSDC: usdcAddr,
    MockWETH: wethAddr,
    InterestRateModel: rateModelAddr,
    CollateralVault: vaultAddr,
    SoulboundReputationNFT: nftAddr,
    LoanContract: loanAddr,
    chainId: 31337,
    rpcUrl: "http://127.0.0.1:8545",
  };

  const outPath = path.join(__dirname, "..", "deployed_addresses.json");
  fs.writeFileSync(outPath, JSON.stringify(addresses, null, 2));
  console.log("\nAddresses written to:", outPath);

  console.log("\n--- Deployment complete ---");
  console.log(addresses);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
