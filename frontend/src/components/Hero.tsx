import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Brain, Search, BookOpen, Shield } from "lucide-react"

const Hero = () => {
  return (
    <section className="relative overflow-hidden bg-background py-20 md:py-28">
      <div className="container">
        <div className="grid gap-12 lg:grid-cols-2 lg:gap-8">
          <div className="flex flex-col justify-center space-y-8">
            <div className="space-y-4">
              <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl">
                Connecting Food, Brain Health, and Mental Wellness
              </h1>
              <p className="max-w-[600px] text-muted-foreground md:text-xl">
                Explore evidence-based connections between nutrition and mental health through our comprehensive database of brain nutrients and their impacts.
              </p>
            </div>
            <div className="flex flex-col gap-4 sm:flex-row">
              <Button size="lg" asChild>
                <Link to="/food-data">Explore the Database</Link>
              </Button>
              <Button variant="outline" size="lg" asChild>
                <Link to="/methodology">Learn More</Link>
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Card>
                <CardContent className="flex flex-col items-center justify-center p-4 text-center">
                  <div className="mb-2 rounded-full bg-primary/10 p-2">
                    <Search className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold">5000+</div>
                  <div className="text-sm text-muted-foreground">Foods</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="flex flex-col items-center justify-center p-4 text-center">
                  <div className="mb-2 rounded-full bg-primary/10 p-2">
                    <Brain className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold">200+</div>
                  <div className="text-sm text-muted-foreground">Brain Nutrients</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="flex flex-col items-center justify-center p-4 text-center">
                  <div className="mb-2 rounded-full bg-primary/10 p-2">
                    <BookOpen className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold">1000+</div>
                  <div className="text-sm text-muted-foreground">Research Papers</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="flex flex-col items-center justify-center p-4 text-center">
                  <div className="mb-2 rounded-full bg-primary/10 p-2">
                    <Shield className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold">Expert</div>
                  <div className="text-sm text-muted-foreground">Validated</div>
                </CardContent>
              </Card>
            </div>
          </div>
          <div className="relative hidden lg:block">
            <div className="relative aspect-square rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 p-8">
              <div className="absolute inset-0 flex items-center justify-center">
                <Brain className="h-64 w-64 text-primary/40" />
              </div>
              <div className="relative h-full w-full rounded-lg border bg-background/50 backdrop-blur">
                {/* Placeholder for future interactive visualization */}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Hero 