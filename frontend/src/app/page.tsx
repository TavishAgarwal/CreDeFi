import { Navbar } from "@/components/credefi/navbar"
import { LandingPage } from "@/components/credefi/landing-page"

export default function Home() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <LandingPage />
      </div>
    </>
  )
}
