/**
 * Export contract ABIs from Hardhat artifacts to backend and frontend.
 *
 * Usage: npx hardhat run scripts/export-abis.js
 */

const fs = require("fs");
const path = require("path");

const CONTRACTS = [
  "LoanContract",
  "CollateralVault",
  "InterestRateModel",
  "SoulboundReputationNFT",
  "MockERC20",
];

const TARGETS = [
  path.join(__dirname, "..", "..", "backend", "app", "contracts", "abis"),
  path.join(__dirname, "..", "..", "frontend", "src", "contracts", "abis"),
];

async function main() {
  for (const dir of TARGETS) {
    fs.mkdirSync(dir, { recursive: true });
  }

  for (const name of CONTRACTS) {
    let artifactPath;
    if (name === "MockERC20") {
      artifactPath = path.join(
        __dirname,
        "..",
        "artifacts",
        "contracts",
        "mocks",
        `${name}.sol`,
        `${name}.json`
      );
    } else {
      artifactPath = path.join(
        __dirname,
        "..",
        "artifacts",
        "contracts",
        `${name}.sol`,
        `${name}.json`
      );
    }

    if (!fs.existsSync(artifactPath)) {
      console.warn(`  SKIP ${name} — artifact not found at ${artifactPath}`);
      continue;
    }

    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
    const abiOnly = { contractName: name, abi: artifact.abi };

    for (const dir of TARGETS) {
      const out = path.join(dir, `${name}.json`);
      fs.writeFileSync(out, JSON.stringify(abiOnly, null, 2));
    }
    console.log(`  ✓ ${name} (${artifact.abi.length} ABI entries)`);
  }

  console.log("\nABIs exported to:");
  TARGETS.forEach((t) => console.log("  ", t));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
