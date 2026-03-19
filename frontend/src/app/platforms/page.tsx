import { Navbar } from "@/components/credefi/navbar"
import { PlatformConnectionPage } from "@/components/credefi/platform-connection"
import { WalletGate } from "@/components/credefi/wallet-gate"

export default function PlatformsPage() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <WalletGate>
          <PlatformConnectionPage />
        </WalletGate>
      </div>
    </>
  )
}
