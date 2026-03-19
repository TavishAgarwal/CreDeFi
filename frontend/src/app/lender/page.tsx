import { Navbar } from "@/components/credefi/navbar"
import { LenderDashboard } from "@/components/credefi/lender-dashboard"
import { WalletGate } from "@/components/credefi/wallet-gate"

export default function LenderPage() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <WalletGate>
          <LenderDashboard />
        </WalletGate>
      </div>
    </>
  )
}
