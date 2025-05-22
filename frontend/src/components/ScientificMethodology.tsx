import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, Database, FileSearch, Shield, Sparkles } from "lucide-react"

const methodologySteps = [
  {
    title: "Data Collection",
    description: "We gather data from multiple authoritative sources including USDA FoodData Central, scientific literature, and clinical studies.",
    icon: Database,
    details: [
      "USDA FoodData Central for standard nutrients",
      "Peer-reviewed research for brain-specific nutrients",
      "Clinical studies for mental health impacts",
      "Expert-validated connections"
    ]
  },
  {
    title: "AI Analysis",
    description: "Our AI models analyze patterns and predict potential nutrient-mental health relationships with confidence ratings.",
    icon: Sparkles,
    details: [
      "Pattern recognition across studies",
      "Confidence scoring for predictions",
      "Cross-validation with existing research",
      "Continuous learning from new data"
    ]
  },
  {
    title: "Expert Validation",
    description: "All predictions and connections are reviewed by our network of nutritional psychiatry experts.",
    icon: Brain,
    details: [
      "Peer review process",
      "Expert consensus building",
      "Clinical relevance assessment",
      "Regular validation updates"
    ]
  },
  {
    title: "Quality Assurance",
    description: "Rigorous quality checks ensure data accuracy and reliability.",
    icon: Shield,
    details: [
      "Source verification",
      "Data consistency checks",
      "Regular accuracy audits",
      "Transparent methodology"
    ]
  }
]

const ScientificMethodology = () => {
  return (
    <section className="py-20 bg-muted/50">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Scientific Methodology
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Our database combines traditional nutritional data with AI-assisted analysis and expert validation to provide comprehensive insights into food-brain relationships.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2">
          {methodologySteps.map((step) => (
            <Card key={step.title} className="flex flex-col">
              <CardHeader>
                <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                  <step.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{step.title}</CardTitle>
                <CardDescription>{step.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {step.details.map((detail) => (
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

        <div className="mt-16 rounded-lg bg-primary/5 p-8">
          <div className="grid gap-8 lg:grid-cols-2 lg:gap-12">
            <div>
              <h3 className="text-2xl font-bold">Transparent & Reliable</h3>
              <p className="mt-4 text-muted-foreground">
                Every data point in our database includes:
              </p>
              <ul className="mt-4 space-y-2">
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>Source citations and references</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>Confidence ratings for predictions</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>Expert validation status</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>Last update timestamp</span>
                </li>
              </ul>
            </div>
            <div className="flex flex-col justify-center space-y-4">
              <Button size="lg" asChild>
                <Link to="/methodology">Read Full Methodology</Link>
              </Button>
              <p className="text-sm text-muted-foreground">
                Or explore our{" "}
                <Link to="/data-dictionary" className="text-primary hover:underline">
                  data dictionary
                </Link>{" "}
                for detailed field descriptions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default ScientificMethodology 