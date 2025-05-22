import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, LineChart, Search, Shield, Sparkles, TestTube } from "lucide-react"

const features = [
  {
    title: "Comprehensive Brain Nutrient Profiles",
    description: "Detailed analysis of nutrients that impact brain function and mental health.",
    icon: Brain,
    details: [
      "200+ brain-specific nutrients tracked",
      "Mechanism of action explained",
      "Research-backed evidence levels",
      "Clinical relevance indicators"
    ]
  },
  {
    title: "Mental Health Impact Analysis",
    description: "Understand how different foods affect various aspects of mental wellness.",
    icon: LineChart,
    details: [
      "Mood and cognitive effects",
      "Time to impact analysis",
      "Dosage recommendations",
      "Interaction warnings"
    ]
  },
  {
    title: "Food Comparison Tools",
    description: "Compare nutritional profiles and mental health impacts across different foods.",
    icon: Search,
    details: [
      "Side-by-side comparisons",
      "Nutrient density analysis",
      "Mental health impact scoring",
      "Personalized recommendations"
    ]
  },
  {
    title: "Scientific Evidence Ratings",
    description: "Clear indicators of research quality and confidence levels.",
    icon: TestTube,
    details: [
      "Evidence strength ratings",
      "Source citations",
      "Expert validation status",
      "Research context provided"
    ]
  },
  {
    title: "AI-Enhanced Insights",
    description: "Advanced analysis of nutrient-mental health relationships.",
    icon: Sparkles,
    details: [
      "Pattern recognition",
      "Predictive modeling",
      "Confidence scoring",
      "Continuous learning"
    ]
  },
  {
    title: "Expert-Validated Data",
    description: "All information is reviewed by nutritional psychiatry experts.",
    icon: Shield,
    details: [
      "Peer-reviewed content",
      "Clinical validation",
      "Regular updates",
      "Quality assurance"
    ]
  }
]

const Features = () => {
  return (
    <section className="py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Powerful Features for Understanding Food-Brain Connections
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Our database provides comprehensive tools and insights to help you understand how nutrition affects mental health.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title} className="flex flex-col">
              <CardHeader>
                <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {feature.details.map((detail) => (
                    <li key={detail} className="flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                      <span className="text-sm text-muted-foreground">{detail}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-16 text-center">
          <Button size="lg" asChild>
            <Link to="/database">Explore the Database</Link>
          </Button>
          <p className="mt-4 text-sm text-muted-foreground">
            Start exploring our comprehensive database of food-brain connections today.
          </p>
        </div>
      </div>
    </section>
  )
}

export default Features 