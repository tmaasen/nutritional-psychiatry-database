import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { ContactForm } from "../components/ContactForm"
import SEO from '../components/SEO'

const Contact = () => {
  return (
    <>
      <SEO
        title="Contact Us"
        description="Get in touch with the Nutritional Psychiatry Database team. We're here to help with your questions and feedback."
        keywords={['contact', 'support', 'help', 'feedback', 'TMM Solutions']}
      />

      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Contact Us</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Have questions or feedback? We'd love to hear from you. Fill out the form below and we'll get back to you as soon as possible.
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Send us a Message</CardTitle>
              <CardDescription>
                Fill out the form and we'll get back to you within 48 hours.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ContactForm />
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  )
}

export default Contact 