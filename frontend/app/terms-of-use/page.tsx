import Header from "@/components/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function TermsOfUsePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-center">Terms of Use</CardTitle>
            <p className="text-center text-gray-600">Last updated: August 5, 2025</p>
          </CardHeader>
          <CardContent className="prose max-w-none">
            <h2 className="text-2xl font-semibold mt-8 mb-4">1. Acceptance of Terms</h2>
            <p className="mb-4">
              By accessing and using FantasySnipe.ai ("the Service"), you accept and agree to be bound by the terms and
              provision of this agreement.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">2. Description of Service</h2>
            <p className="mb-4">
              FantasySnipe.ai provides AI-powered fantasy hockey tools, including but not limited to:
            </p>
            <ul className="list-disc pl-6 mb-4">
              <li>Player rankings and projections</li>
              <li>Draft assistance and recommendations</li>
              <li>Trade analysis and suggestions</li>
              <li>Injury tracking and updates</li>
              <li>League management tools</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">3. User Accounts</h2>
            <p className="mb-4">
              To access certain features of the Service, you may be required to create an account. You are responsible
              for:
            </p>
            <ul className="list-disc pl-6 mb-4">
              <li>Maintaining the confidentiality of your account credentials</li>
              <li>All activities that occur under your account</li>
              <li>Providing accurate and complete information</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">4. AI-Generated Content</h2>
            <p className="mb-4">
              Our Service uses artificial intelligence to generate recommendations and analysis. While we strive for
              accuracy:
            </p>
            <ul className="list-disc pl-6 mb-4">
              <li>AI predictions are not guaranteed to be accurate</li>
              <li>Fantasy sports involve inherent uncertainty</li>
              <li>Users should use their own judgment in making decisions</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">5. Prohibited Uses</h2>
            <p className="mb-4">You may not use the Service to:</p>
            <ul className="list-disc pl-6 mb-4">
              <li>Violate any applicable laws or regulations</li>
              <li>Transmit harmful or malicious code</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Use automated tools to scrape or harvest data</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">6. Intellectual Property</h2>
            <p className="mb-4">
              All content, features, and functionality of the Service are owned by FantasySnipe.ai and are protected by
              copyright, trademark, and other intellectual property laws.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">7. Disclaimer of Warranties</h2>
            <p className="mb-4">
              The Service is provided "as is" without warranties of any kind. We do not guarantee that the Service will
              be uninterrupted, secure, or error-free.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">8. Limitation of Liability</h2>
            <p className="mb-4">
              FantasySnipe.ai shall not be liable for any indirect, incidental, special, or consequential damages
              arising from your use of the Service.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">9. Changes to Terms</h2>
            <p className="mb-4">
              We reserve the right to modify these terms at any time. Changes will be effective immediately upon posting
              to the Service.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">10. Contact Information</h2>
            <p className="mb-4">If you have questions about these Terms of Use, please contact us at:</p>
            <p className="mb-4">
              Email: legal@fantasysnipe.ai
              <br />
              Address: 123 Hockey Lane, Fantasy City, FC 12345
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
