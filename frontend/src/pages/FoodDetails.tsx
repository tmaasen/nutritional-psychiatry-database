import { useParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"

// Mock data for demonstration
const mockFood = {
  id: 1,
  name: "Salmon",
  category: "Seafood",
  description: "Rich in omega-3 fatty acids, particularly DHA and EPA, which are essential for brain health and have been linked to reduced depression symptoms.",
    nutrients: [
    { name: "Omega-3", amount: "2.3g", rda: "1.6g", impact: "High" },
    { name: "Vitamin D", amount: "13.1mcg", rda: "15mcg", impact: "Medium" },
    { name: "B12", amount: "2.6mcg", rda: "2.4mcg", impact: "High" }
    ],
    mentalHealthImpacts: [
      {
      effect: "Mood Regulation",
      confidence: "High",
      evidence: "Multiple clinical trials show positive effects on depression symptoms"
    },
    {
      effect: "Cognitive Function",
      confidence: "Medium",
      evidence: "Observational studies suggest improved memory and focus"
    }
  ],
  researchPapers: [
    {
      title: "Omega-3 Fatty Acids and Depression",
      authors: ["Smith, J.", "Johnson, A."],
      year: 2023,
      doi: "10.1234/jnp.2023.001"
    }
  ]
}

const FoodDetails = () => {
  const { id } = useParams()

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">{mockFood.name}</h1>
        <p className="text-xl text-muted-foreground">{mockFood.category}</p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="nutrients">Brain Nutrients</TabsTrigger>
          <TabsTrigger value="impacts">Mental Health Impacts</TabsTrigger>
          <TabsTrigger value="research">Research</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Food Overview</CardTitle>
              <CardDescription>
                General information about {mockFood.name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="mb-4">{mockFood.description}</p>
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Brain Nutrients</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{mockFood.nutrients.length}</div>
                    <p className="text-xs text-muted-foreground">
                      Key nutrients tracked
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Mental Health Impacts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{mockFood.mentalHealthImpacts.length}</div>
                    <p className="text-xs text-muted-foreground">
                      Documented effects
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Research Papers</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{mockFood.researchPapers.length}</div>
                    <p className="text-xs text-muted-foreground">
                      Related studies
                    </p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="nutrients">
          <Card>
            <CardHeader>
              <CardTitle>Brain Nutrients</CardTitle>
              <CardDescription>
                Key nutrients that affect brain function
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockFood.nutrients.map((nutrient) => (
                  <div key={nutrient.name} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-medium">{nutrient.name}</h4>
                      <p className="text-sm text-muted-foreground">
                        Amount: {nutrient.amount} (RDA: {nutrient.rda})
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-md text-sm ${
                      nutrient.impact === 'High' 
                        ? 'bg-primary/10 text-primary'
                        : 'bg-secondary/10 text-secondary'
                    }`}>
                      {nutrient.impact} Impact
                    </span>
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
              <CardDescription>
                Documented effects on mental health
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockFood.mentalHealthImpacts.map((impact) => (
                  <div key={impact.effect} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{impact.effect}</h4>
                      <span className={`px-2 py-1 rounded-md text-sm ${
                        impact.confidence === 'High' 
                          ? 'bg-primary/10 text-primary'
                          : 'bg-secondary/10 text-secondary'
                      }`}>
                        {impact.confidence} Confidence
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{impact.evidence}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="research">
          <Card>
            <CardHeader>
              <CardTitle>Research Papers</CardTitle>
              <CardDescription>
                Scientific literature related to {mockFood.name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockFood.researchPapers.map((paper) => (
                  <div key={paper.doi} className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-1">{paper.title}</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      {paper.authors.join(", ")} • {paper.year}
                    </p>
                    <Button variant="outline" size="sm" asChild>
                      <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer">
                        View Paper
                      </a>
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default FoodDetails 