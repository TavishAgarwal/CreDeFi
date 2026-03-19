import { Navbar } from "@/components/credefi/navbar"
import { UserDashboard } from "@/components/credefi/user-dashboard"
import { WalletGate } from "@/components/credefi/wallet-gate"

export default function DashboardPage() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <WalletGate>
          <UserDashboard />
        </WalletGate>
      </div>
    </>
  )
}
