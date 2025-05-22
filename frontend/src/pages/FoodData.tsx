import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Search, Filter, Brain, TestTube } from "lucide-react"

// Mock data for demonstration
const mockFoods = [
  {
    id: 1,
    name: "Salmon",
    category: "Seafood",
    brainNutrients: ["Omega-3", "Vitamin D", "B12"],
    mentalHealthImpacts: ["Mood Regulation", "Cognitive Function"]
  },
  {
    id: 2,
    name: "Blueberries",
    category: "Fruits",
    brainNutrients: ["Anthocyanins", "Vitamin C", "Fiber"],
    mentalHealthImpacts: ["Memory", "Anti-inflammatory"]
  },
  // Add more mock foods as needed
]

const FoodData = () => {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("all")

  const filteredFoods = mockFoods.filter(food => 
    food.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
    (selectedCategory === "all" || food.category === selectedCategory)
  )

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Food Database</h1>
        <Button asChild>
          <Link to="/methodology">
            <TestTube className="mr-2 h-4 w-4" />
            View Methodology
          </Link>
        </Button>
      </div>

      {/* Search and Filter Section */}
      <div className="grid gap-4 md:grid-cols-2 mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search foods..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="flex-1">
            <Filter className="mr-2 h-4 w-4" />
            Filter
          </Button>
          <Button variant="outline" className="flex-1">
            <Brain className="mr-2 h-4 w-4" />
            Brain Nutrients
          </Button>
        </div>
      </div>

      {/* Food Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredFoods.map((food) => (
          <Card key={food.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle>{food.name}</CardTitle>
              <CardDescription>{food.category}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium mb-2">Brain Nutrients</h4>
                  <div className="flex flex-wrap gap-2">
                    {food.brainNutrients.map((nutrient) => (
                      <span
                        key={nutrient}
                        className="px-2 py-1 bg-primary/10 text-primary rounded-md text-sm"
                      >
                        {nutrient}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium mb-2">Mental Health Impacts</h4>
                  <div className="flex flex-wrap gap-2">
                    {food.mentalHealthImpacts.map((impact) => (
                      <span
                        key={impact}
                        className="px-2 py-1 bg-secondary/10 text-secondary rounded-md text-sm"
                      >
                        {impact}
                      </span>
                    ))}
                  </div>
                </div>
                <Button variant="outline" className="w-full" asChild>
                  <Link to={`/food/${food.id}`}>View Details</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default FoodData 