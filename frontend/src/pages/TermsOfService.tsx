import SEO from '../components/SEO'

const TermsOfService = () => {
  return (
    <>
      <SEO
        title="Terms of Service"
        description="Terms of Service for the Nutritional Psychiatry Database, operated by TMM Solutions, LLC."
        keywords={['terms of service', 'legal terms', 'user agreement', 'TMM Solutions']}
      />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        
        <div className="prose prose-gray max-w-none">
          <p className="text-muted-foreground mb-8">Last updated: {new Date().toLocaleDateString()}</p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Agreement to Terms</h2>
            <p>
              By accessing or using the Nutritional Psychiatry Database website, operated by TMM Solutions, LLC, 
              you agree to be bound by these Terms of Service. If you disagree with any part of these terms, 
              you may not access the website.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Intellectual Property</h2>
            <p>
              The website and its original content, features, and functionality are owned by TMM Solutions, LLC 
              and are protected by international copyright, trademark, patent, trade secret, and other intellectual 
              property laws.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. User Accounts</h2>
            <p>
              When you create an account with us, you must provide accurate and complete information. You are 
              responsible for maintaining the security of your account and password. We cannot and will not be 
              liable for any loss or damage from your failure to comply with this security obligation.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. User Content</h2>
            <p>
              Our website allows you to post, link, store, share and otherwise make available certain information, 
              text, or other material. You retain ownership of any intellectual property rights that you hold in 
              that content.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Prohibited Uses</h2>
            <p>You may use our website only for lawful purposes and in accordance with these Terms. You agree not to:</p>
            <ul className="list-disc pl-6 mb-4">
              <li>Use the website in any way that violates any applicable law or regulation</li>
              <li>Use the website for any purpose that is unlawful or prohibited by these Terms</li>
              <li>Attempt to gain unauthorized access to any portion of the website</li>
              <li>Interfere with or disrupt the website or servers or networks connected to the website</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Disclaimer of Warranties</h2>
            <p>
              The website is provided "as is" without any warranties, expressed or implied. We do not warrant that 
              the website will be uninterrupted or error-free.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Limitation of Liability</h2>
            <p>
              In no event shall TMM Solutions, LLC be liable for any indirect, incidental, special, consequential, 
              or punitive damages arising out of or relating to your use of the website.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of the state of [Your State], 
              without regard to its conflict of law provisions.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Changes to Terms</h2>
            <p>
              We reserve the right to modify or replace these Terms at any time. If a revision is material, we will 
              provide at least 30 days' notice prior to any new terms taking effect.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Contact Us</h2>
            <p>
              If you have any questions about these Terms, please contact us at:
              <br />
              <a href="mailto:contact@swellapp.co" className="text-primary hover:underline">
                contact@swellapp.co
              </a>
            </p>
          </section>
        </div>
      </div>
    </>
  )
}

export default TermsOfService 