import { Navbar } from "@/components/credefi/navbar"
import { LoanRequestPage } from "@/components/credefi/loan-request"
import { WalletGate } from "@/components/credefi/wallet-gate"

export default function LoanPage() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <WalletGate>
          <LoanRequestPage />
        </WalletGate>
      </div>
    </>
  )
}
