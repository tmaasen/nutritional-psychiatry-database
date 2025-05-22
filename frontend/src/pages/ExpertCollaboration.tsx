import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Brain, TestTube, BookOpen, Database, Mail } from "lucide-react"
import SEO from '../components/SEO'
import { ContactForm } from '../components/ContactForm'

const collaborationAreas = [
  {
    title: "Research Contributions",
    description: "Share your research findings and contribute to our growing database of nutritional psychiatry evidence.",
    icon: TestTube,
    benefits: [
      "Increase the impact of your research",
      "Connect with other researchers",
      "Access our comprehensive database"
    ]
  },
  {
    title: "Data Validation",
    description: "Help validate and refine our AI-assisted nutrient predictions and mental health impact assessments.",
    icon: Brain,
    benefits: [
      "Shape the future of nutritional psychiatry",
      "Ensure data accuracy",
      "Influence methodology development"
    ]
  },
  {
    title: "Literature Review",
    description: "Contribute to our systematic reviews and meta-analyses of nutritional psychiatry research.",
    icon: BookOpen,
    benefits: [
      "Collaborate on systematic reviews",
      "Share your expertise",
      "Build your research network"
    ]
  },
  {
    title: "Database Development",
    description: "Help expand our database with new food items, nutrients, and mental health impact data.",
    icon: Database,
    benefits: [
      "Add your research data",
      "Suggest new features",
      "Shape database development"
    ]
  }
]

const ExpertCollaboration = () => {
  return (
    <>
      <SEO
        title="Expert Collaboration"
        description="Join our network of experts in nutritional psychiatry. Contribute to research, validate data, and help shape the future of nutritional psychiatry."
        keywords={[
          'nutritional psychiatry collaboration',
          'research partnership',
          'expert contribution',
          'data validation',
          'research network'
        ]}
        ogImage="/expert-collaboration-og.jpg"
      />

      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold mb-4">Expert Collaboration</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Join our network of experts in nutritional psychiatry and help advance the field through collaboration and knowledge sharing.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-16">
          {collaborationAreas.map((area) => (
            <Card key={area.title} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                  <area.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>{area.title}</CardTitle>
                <CardDescription>{area.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {area.benefits.map((benefit) => (
                    <li key={benefit} className="flex items-center text-sm">
                      <span className="mr-2">•</span>
                      {benefit}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>Get Started</CardTitle>
            <CardDescription>
              Ready to collaborate? Fill out our expert application form and we'll get back to you within 48 hours.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <p className="text-sm text-muted-foreground mb-4">
                  We're looking for experts in:
                </p>
                <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                  <li>Nutritional Psychiatry</li>
                  <li>Clinical Nutrition</li>
                  <li>Mental Health Research</li>
                  <li>Data Science</li>
                  <li>Food Science</li>
                </ul>
              </div>
              <ContactForm />
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  )
}

export default ExpertCollaboration 