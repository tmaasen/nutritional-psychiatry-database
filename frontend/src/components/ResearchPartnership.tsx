import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, FileSearch, Users, Award } from "lucide-react"

const benefits = [
  {
    title: "Contribute Research",
    description: "Share your research findings and help expand our understanding of nutrition's role in mental health.",
    icon: FileSearch
  },
  {
    title: "Validate Data",
    description: "Join our expert network to validate and enhance the accuracy of our nutrient-mental health connections.",
    icon: Brain
  },
  {
    title: "Collaborate",
    description: "Work with other researchers and healthcare providers to advance nutritional psychiatry research.",
    icon: Users
  },
  {
    title: "Get Recognition",
    description: "Your contributions will be acknowledged in our database and research publications.",
    icon: Award
  }
]

const ResearchPartnership = () => {
  return (
    <section className="py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Advancing Nutritional Psychiatry Research Together
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Join our collaborative network of researchers and healthcare providers to advance the field of nutritional psychiatry.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {benefits.map((benefit) => (
            <Card key={benefit.title} className="flex flex-col">
              <CardHeader>
                <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                  <benefit.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{benefit.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{benefit.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-16 rounded-lg bg-primary/5 p-8">
          <div className="grid gap-8 lg:grid-cols-2 lg:gap-12">
            <div>
              <h3 className="text-2xl font-bold">Join Our Research Network</h3>
              <p className="mt-4 text-muted-foreground">
                As a research partner, you'll have access to:
              </p>
              <ul className="mt-4 space-y-2">
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>Early access to new features and data</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>Collaboration opportunities with other experts</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>API access for research integration</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>Recognition in publications and presentations</span>
                </li>
              </ul>
            </div>
            <div className="flex flex-col justify-center space-y-4">
              <Button size="lg" asChild>
                <Link to="/contact">Become a Research Partner</Link>
              </Button>
              <p className="text-sm text-muted-foreground">
                Or email us at{" "}
                <a href="mailto:research@nutritionalpsychiatry.org" className="text-primary hover:underline">
                  research@nutritionalpsychiatry.org
                </a>
              </p>
            </div>
          </div>
        </div>

        <div className="mt-16 text-center">
          <p className="text-muted-foreground">
            Learn more about our{" "}
            <Link to="/methodology" className="text-primary hover:underline">
              research methodology
            </Link>{" "}
            and{" "}
            <Link to="/data-sources" className="text-primary hover:underline">
              data sources
            </Link>
            .
          </p>
        </div>
      </div>
    </section>
  )
}

export default ResearchPartnership 