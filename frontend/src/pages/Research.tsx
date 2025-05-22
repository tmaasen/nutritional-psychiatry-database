import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Brain, TestTube, BookOpen, Database } from "lucide-react"

const researchAreas = [
  {
    title: "Brain Nutrient Analysis",
    description: "Explore how different nutrients affect brain function and mental health",
    icon: Brain,
    link: "/food-data"
  },
  {
    title: "Clinical Studies",
    description: "Review clinical trials and research studies on nutritional psychiatry",
    icon: TestTube,
    link: "/literature"
  },
  {
    title: "Literature Review",
    description: "Access our comprehensive review of nutritional psychiatry research",
    icon: BookOpen,
    link: "/docs/literature-review.md"
  },
  {
    title: "Data Methodology",
    description: "Learn about our AI-assisted approach to nutritional data analysis",
    icon: Database,
    link: "/methodology"
  }
]

const Research = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Research & Analysis</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Explore our comprehensive research on the connections between nutrition and mental health
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-12">
        {researchAreas.map((area) => (
          <Card key={area.title} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                <area.icon className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>{area.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="mb-4">{area.description}</CardDescription>
              <Button variant="outline" className="w-full" asChild>
                <Link to={area.link}>Explore →</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Research Highlights</CardTitle>
            <CardDescription>
              Key findings from our analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Brain className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h4 className="font-medium">Brain Nutrient Patterns</h4>
                  <p className="text-sm text-muted-foreground">
                    Analysis of nutrient combinations that support optimal brain function
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="rounded-lg bg-primary/10 p-2">
                  <TestTube className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h4 className="font-medium">Clinical Evidence</h4>
                  <p className="text-sm text-muted-foreground">
                    Review of clinical trials and their implications for mental health
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Research Partnership</CardTitle>
            <CardDescription>
              Collaborate with our research team
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-muted-foreground">
              We welcome collaboration with researchers and institutions interested in advancing the field of nutritional psychiatry.
            </p>
            <Button asChild>
              <Link to="/contact">Partner With Us</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Research 