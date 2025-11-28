import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-center">Privacy Policy</CardTitle>
            <p className="text-center text-gray-600">Last updated: August 5, 2025</p>
          </CardHeader>
          <CardContent className="prose max-w-none">
            <h2 className="text-2xl font-semibold mt-8 mb-4">1. Information We Collect</h2>
            <p className="mb-4">We collect information you provide directly to us, such as:</p>
            <ul className="list-disc pl-6 mb-4">
              <li>Account registration information (name, email, password)</li>
              <li>Fantasy league data you choose to sync</li>
              <li>Preferences and settings</li>
              <li>Communications with our support team</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">2. How We Use Your Information</h2>
            <p className="mb-4">We use the information we collect to:</p>
            <ul className="list-disc pl-6 mb-4">
              <li>Provide and improve our AI-powered fantasy hockey tools</li>
              <li>Personalize your experience and recommendations</li>
              <li>Send you updates and notifications</li>
              <li>Analyze usage patterns to enhance our Service</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">3. AI and Machine Learning</h2>
            <p className="mb-4">
              Our AI systems process your fantasy data to provide personalized recommendations. This includes:
            </p>
            <ul className="list-disc pl-6 mb-4">
              <li>Analyzing your team composition and needs</li>
              <li>Learning from your draft and trade patterns</li>
              <li>Improving prediction accuracy over time</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">4. Information Sharing</h2>
            <p className="mb-4">We do not sell, trade, or rent your personal information. We may share information:</p>
            <ul className="list-disc pl-6 mb-4">
              <li>With your consent</li>
              <li>To comply with legal obligations</li>
              <li>With service providers who assist in our operations</li>
              <li>In connection with a business transfer</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">5. Data Security</h2>
            <p className="mb-4">We implement appropriate security measures to protect your information, including:</p>
            <ul className="list-disc pl-6 mb-4">
              <li>Encryption of sensitive data</li>
              <li>Regular security assessments</li>
              <li>Access controls and authentication</li>
              <li>Secure data storage and transmission</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">6. Cookies and Tracking</h2>
            <p className="mb-4">
              We use cookies and similar technologies to enhance your experience and analyze usage patterns. You can
              control cookie settings through your browser.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">7. Third-Party Services</h2>
            <p className="mb-4">
              Our Service may integrate with third-party fantasy platforms. Please review their privacy policies as we
              are not responsible for their practices.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">8. Your Rights</h2>
            <p className="mb-4">You have the right to:</p>
            <ul className="list-disc pl-6 mb-4">
              <li>Access and update your personal information</li>
              <li>Delete your account and associated data</li>
              <li>Opt out of marketing communications</li>
              <li>Request data portability</li>
            </ul>

            <h2 className="text-2xl font-semibold mt-8 mb-4">9. Children's Privacy</h2>
            <p className="mb-4">
              Our Service is not intended for children under 13. We do not knowingly collect personal information from
              children under 13.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">10. Changes to Privacy Policy</h2>
            <p className="mb-4">
              We may update this Privacy Policy periodically. We will notify you of significant changes via email or
              through the Service.
            </p>

            <h2 className="text-2xl font-semibold mt-8 mb-4">11. Contact Us</h2>
            <p className="mb-4">If you have questions about this Privacy Policy, please contact us at:</p>
            <p className="mb-4">
              Email: privacy@fantasysnipe.ai
              <br />
              Address: 123 Hockey Lane, Fantasy City, FC 12345
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
