import { Navbar } from "@/components/credefi/navbar"
import { TransactionsPage } from "@/components/credefi/transactions"
import { WalletGate } from "@/components/credefi/wallet-gate"

export default function TransactionsRoute() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <WalletGate>
          <TransactionsPage />
        </WalletGate>
      </div>
    </>
  )
}
