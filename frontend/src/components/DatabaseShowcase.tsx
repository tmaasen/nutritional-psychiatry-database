import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, FileSearch, Scale, Shield, Sparkles, TestTube, Search } from "lucide-react"
import { Input } from "./ui/input"

const features = [
  {
    id: "food-detail",
    title: "Food Detail View",
    description: "Comprehensive analysis of individual foods and their brain nutrient profiles.",
    icon: FileSearch,
    image: "/images/food-detail.png",
    alt: "Food detail view showing comprehensive nutrient analysis",
    highlights: [
      "Complete nutrient breakdown",
      "Brain-specific nutrient analysis",
      "Mental health impact assessment",
      "Research-backed evidence levels"
    ]
  },
  {
    id: "brain-nutrients",
    title: "Brain Nutrient Panel",
    description: "Detailed exploration of nutrients that affect brain function and mental health.",
    icon: Brain,
    image: "/images/brain-nutrients.png",
    alt: "Brain nutrient panel showing detailed nutrient analysis",
    highlights: [
      "Mechanism of action",
      "Clinical relevance",
      "Dosage information",
      "Interaction warnings"
    ]
  },
  {
    id: "comparison",
    title: "Food Comparison Tool",
    description: "Compare nutritional profiles and mental health impacts across different foods.",
    icon: Scale,
    image: "/images/comparison-tool.png",
    alt: "Food comparison tool showing side-by-side analysis",
    highlights: [
      "Side-by-side comparisons",
      "Nutrient density analysis",
      "Mental health impact scoring",
      "Personalized insights"
    ]
  }
]

const trustIndicators = [
  {
    title: "Expert Validation",
    description: "All data is reviewed by nutritional psychiatry experts",
    icon: Shield
  },
  {
    title: "Research-Backed",
    description: "Based on 1000+ peer-reviewed research papers",
    icon: TestTube
  },
  {
    title: "AI-Enhanced",
    description: "Advanced analysis of nutrient-mental health relationships",
    icon: Sparkles
  }
]

// This will be replaced with actual API calls
const mockSearchResults = [
  {
    id: 1,
    name: "Salmon",
    nutrients: {
      omega3: "High",
      vitaminD: "High",
      b12: "High"
    },
    mentalHealthImpacts: [
      "Supports brain function",
      "May improve mood",
      "Anti-inflammatory effects"
    ]
  },
  {
    id: 2,
    name: "Blueberries",
    nutrients: {
      antioxidants: "Very High",
      vitaminC: "High",
      fiber: "Moderate"
    },
    mentalHealthImpacts: [
      "Cognitive enhancement",
      "Neuroprotective effects",
      "Anti-inflammatory properties"
    ]
  }
]

const DatabaseShowcase = () => {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [searchResults, setSearchResults] = React.useState<typeof mockSearchResults>([])
  const [selectedFood, setSelectedFood] = React.useState<typeof mockSearchResults[0] | null>(null)

  // This will be replaced with actual API call
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value.toLowerCase();
    setSearchQuery(query);
    if (query) {
      const results = mockSearchResults.filter(food => 
        food.name.toLowerCase().includes(query) ||
        food.mentalHealthImpacts[0].toLowerCase().includes(query)
      );
      setSearchResults(results);
    } else {
      setSearchResults([]);
    }
  };

  return (
    <section className="py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Explore Our Database Interface
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Search and explore the connection between food and mental health in our comprehensive database.
          </p>
        </div>

        <div className="mt-16">
          <Card className="w-full">
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search for foods..."
                    className="pl-9"
                    value={searchQuery}
                    onChange={handleSearch}
                  />
                </div>
                <Button>Search</Button>
              </div>

              {searchResults.length > 0 && (
                <div className="mt-4 space-y-4">
                  {searchResults.map((food) => (
                    <Card
                      key={food.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => setSelectedFood(food)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-semibold">{food.name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {food.mentalHealthImpacts[0]}
                            </p>
                          </div>
                          <Button variant="ghost" size="sm">
                            View Details →
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {selectedFood && (
                <div className="mt-8">
                  <Tabs defaultValue="nutrients" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="nutrients">Nutrients</TabsTrigger>
                      <TabsTrigger value="impacts">Mental Health Impacts</TabsTrigger>
                      <TabsTrigger value="research">Research</TabsTrigger>
                    </TabsList>

                    <TabsContent value="nutrients">
                      <Card>
                        <CardHeader>
                          <CardTitle>Nutrient Profile</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid gap-4">
                            {Object.entries(selectedFood.nutrients).map(([nutrient, level]) => (
                              <div key={nutrient} className="flex items-center justify-between">
                                <span className="capitalize">{nutrient}</span>
                                <span className="text-muted-foreground">{level}</span>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </TabsContent>

                    <TabsContent value="impacts">
                      <Card>
                        <CardHeader>
                          <CardTitle>Mental Health Impacts</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2">
                            {selectedFood.mentalHealthImpacts.map((impact) => (
                              <li key={impact} className="flex items-center gap-2">
                                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                                <span>{impact}</span>
                              </li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    </TabsContent>

                    <TabsContent value="research">
                      <Card>
                        <CardHeader>
                          <CardTitle>Research Evidence</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-muted-foreground">
                            Research data will be displayed here when the API is connected.
                          </p>
                        </CardContent>
                      </Card>
                    </TabsContent>
                  </Tabs>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <CardTitle className="text-xl">Expert Validation</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                All data is reviewed by nutritional psychiatry experts
              </CardDescription>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                <TestTube className="h-6 w-6 text-primary" />
              </div>
              <CardTitle className="text-xl">Research-Backed</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Based on 1000+ peer-reviewed research papers
              </CardDescription>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <div className="mb-4 rounded-lg bg-primary/10 p-2 w-fit">
                <Sparkles className="h-6 w-6 text-primary" />
              </div>
              <CardTitle className="text-xl">AI-Enhanced</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Advanced analysis of nutrient-mental health relationships
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        <div className="mt-16 text-center">
          <Button size="lg" asChild>
            <Link to="/database">Start Using the Database</Link>
          </Button>
          <p className="mt-4 text-sm text-muted-foreground">
            Begin exploring the connection between food and mental health today.
          </p>
        </div>
      </div>
    </section>
  )
}

export default DatabaseShowcase 