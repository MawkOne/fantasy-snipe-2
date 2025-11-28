import HeroSection from "@/components/hero-section"
import HomeHeroMockCard from "@/components/home-hero-mock-card"
import LatestArticles from "@/components/latest-articles"
import FeaturedLinks from "@/components/featured-links"
import WhoShouldIDraftCard from "@/components/who-should-i-draft-card"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Dismissible sync banner */}
      <HeroSection />

      <main className="w-full">
        <div className="container mx-auto px-4 py-6 xl:py-8">
          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_360px] gap-6 xl:gap-8">
            {/* Left column */}
            <div className="space-y-6">
              <HomeHeroMockCard />
              <LatestArticles />
            </div>

            {/* Right column */}
            <div className="space-y-6">
              <WhoShouldIDraftCard />
              <FeaturedLinks />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
