import { Link } from 'react-router-dom'
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Search, Brain, Utensils, BookOpen, TestTube } from "lucide-react"
import SEO from '../components/SEO'
import BrainIcon from "../components/BrainIcon"

const features = [
  {
    title: "Food Database",
    description: "Explore our comprehensive database of foods and their brain nutrient profiles.",
    icon: Utensils,
    link: "/food-data"
  },
  {
    title: "Research",
    description: "Access the latest research on nutritional psychiatry and mental health.",
    icon: TestTube,
    link: "/research"
  },
  {
    title: "Methodology",
    description: "Learn about our AI-assisted methodology for predicting brain nutrients.",
    icon: Brain,
    link: "/methodology"
  },
  {
    title: "Literature",
    description: "Browse our curated collection of scientific literature.",
    icon: BookOpen,
    link: "/literature"
  }
]

const Home = () => {
  // Schema.org markup for the website
  const websiteSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "Nutritional Psychiatry Database",
    "url": "https://nutritional-psychiatry-database.com",
    "description": "A comprehensive database connecting nutrition and mental health through evidence-based research.",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://nutritional-psychiatry-database.com/food-data?search={search_term_string}",
      "query-input": "required name=search_term_string"
    }
  }

  // Schema.org markup for the organization
  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Nutritional Psychiatry Database",
    "url": "https://nutritional-psychiatry-database.com",
    "logo": "https://nutritional-psychiatry-database.com/logo.png",
    "sameAs": [
      "https://twitter.com/nutritional_psych",
      "https://linkedin.com/company/nutritional-psychiatry-database"
    ]
  }

  return (
    <>
      <SEO
        title="Home"
        description="Explore the Nutritional Psychiatry Database - A comprehensive resource connecting food, brain health, and mental wellness."
        keywords={['nutritional psychiatry', 'brain health', 'mental wellness', 'food database']}
      />
      
      {/* Schema.org JSON-LD */}
      <script type="application/ld+json">
        {JSON.stringify(websiteSchema)}
      </script>
      <script type="application/ld+json">
        {JSON.stringify(organizationSchema)}
      </script>

      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <BrainIcon size={64} className="text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold mb-4">
            Connecting Food, Brain Health, and Mental Wellness
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Explore evidence-based connections between nutrition and mental health through our comprehensive database of brain-relevant nutrients.
          </p>
        </div>

        {/* Search Section */}
        <section className="max-w-2xl mx-auto mb-16">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search for foods..."
              className="w-full pl-10 pr-4 py-2 rounded-md border border-input bg-background"
            />
          </div>
        </section>

        {/* Features Grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <Card key={feature.title} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{feature.description}</CardDescription>
                <Button variant="link" className="mt-4 p-0" asChild>
                  <Link to={feature.link}>Learn more →</Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </section>
      </div>
    </>
  )
}

export default Home 