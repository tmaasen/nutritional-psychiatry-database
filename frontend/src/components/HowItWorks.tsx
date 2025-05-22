import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, Search, LineChart, ArrowRight } from "lucide-react"

const steps = [
  {
    title: "Search Foods",
    description: "Start by searching for specific foods or browse by categories to find what you're looking for.",
    icon: Search,
    details: [
      "Search by food name or category",
      "Filter by dietary preferences",
      "Browse popular searches",
      "Save favorites for quick access"
    ],
    image: "/images/search-interface.png",
    alt: "Database search interface showing food search functionality"
  },
  {
    title: "Explore Brain Nutrients",
    description: "Review detailed nutrient profiles and their specific impacts on brain function and mental health.",
    icon: Brain,
    details: [
      "View nutrient composition",
      "Understand mechanisms of action",
      "Check research evidence levels",
      "Review expert validations"
    ],
    image: "/images/nutrient-panel.png",
    alt: "Brain nutrient analysis panel showing detailed nutrient information"
  },
  {
    title: "Understand Mental Health Connections",
    description: "Learn how specific nutrients affect various aspects of mental wellness and cognitive function.",
    icon: LineChart,
    details: [
      "Review mental health impacts",
      "Check time to effect",
      "Understand dosage effects",
      "Explore research context"
    ],
    image: "/images/impact-analysis.png",
    alt: "Mental health impact analysis showing nutrient-mental health relationships"
  }
]

const HowItWorks = () => {
  return (
    <section className="py-20 bg-muted/50">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How It Works
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Follow these simple steps to explore the connection between food and mental health in our database.
          </p>
        </div>

        <div className="mt-16 space-y-16">
          {steps.map((step, index) => (
            <div key={step.title} className="relative">
              {/* Step Number */}
              <div className="absolute -left-4 -top-4 flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
                {index + 1}
              </div>

              <div className="grid gap-8 lg:grid-cols-2 lg:gap-12">
                <div className="flex flex-col justify-center">
                  <Card>
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
                </div>

                <div className="relative">
                  <div className="aspect-video overflow-hidden rounded-lg border bg-muted">
                    <img
                      src={step.image}
                      alt={step.alt}
                      className="h-full w-full object-cover"
                    />
                  </div>
                </div>
              </div>

              {/* Arrow between steps */}
              {index < steps.length - 1 && (
                <div className="absolute -bottom-8 left-1/2 -translate-x-1/2">
                  <ArrowRight className="h-6 w-6 text-muted-foreground rotate-90" />
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <Button size="lg" asChild>
            <Link to="/database">Start Exploring</Link>
          </Button>
          <p className="mt-4 text-sm text-muted-foreground">
            Ready to discover how food affects your mental health? Start exploring our database now.
          </p>
        </div>
      </div>
    </section>
  )
}

export default HowItWorks 