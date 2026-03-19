import { Navbar } from "@/components/credefi/navbar"
import { TrustGraphPage } from "@/components/credefi/trust-graph"
import { WalletGate } from "@/components/credefi/wallet-gate"

export default function GraphRoute() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <WalletGate>
          <TrustGraphPage />
        </WalletGate>
      </div>
    </>
  )
}
