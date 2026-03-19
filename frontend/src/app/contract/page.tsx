import { Navbar } from "@/components/credefi/navbar"
import { SmartContractPreview } from "@/components/credefi/smart-contract-preview"
import { WalletGate } from "@/components/credefi/wallet-gate"

export default function ContractPage() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <WalletGate>
          <SmartContractPreview />
        </WalletGate>
      </div>
    </>
  )
}
