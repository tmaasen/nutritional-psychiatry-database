import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Search, Filter, BookOpen, Brain } from "lucide-react"

// Mock data for demonstration
const mockPapers = [
  {
    id: 1,
    title: "The Role of Omega-3 Fatty Acids in Depression",
    authors: ["Smith, J.", "Johnson, A.", "Williams, B."],
    journal: "Journal of Nutritional Psychiatry",
    year: 2023,
    impact: "High",
    keywords: ["Depression", "Omega-3", "Clinical Trial"]
  },
  {
    id: 2,
    title: "Gut-Brain Axis: The Impact of Diet on Mental Health",
    authors: ["Brown, C.", "Davis, D."],
    journal: "Nutritional Neuroscience",
    year: 2022,
    impact: "Medium",
    keywords: ["Gut-Brain Axis", "Microbiome", "Mental Health"]
  }
]

const Literature = () => {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedYear, setSelectedYear] = useState("all")

  const filteredPapers = mockPapers.filter(paper => 
    paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    paper.authors.some(author => author.toLowerCase().includes(searchQuery.toLowerCase())) ||
    paper.keywords.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Scientific Literature</h1>
        <Button asChild>
          <a href="/docs/literature-review.md" target="_blank" rel="noopener noreferrer">
            <BookOpen className="mr-2 h-4 w-4" />
            Full Review
          </a>
        </Button>
      </div>

      {/* Search and Filter Section */}
      <div className="grid gap-4 md:grid-cols-2 mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search papers..."
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
            Brain Health
          </Button>
        </div>
      </div>

      {/* Papers Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {filteredPapers.map((paper) => (
          <Card key={paper.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="text-lg">{paper.title}</CardTitle>
              <CardDescription>
                {paper.authors.join(", ")} • {paper.journal} ({paper.year})
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium mb-2">Keywords</h4>
                  <div className="flex flex-wrap gap-2">
                    {paper.keywords.map((keyword) => (
                      <span
                        key={keyword}
                        className="px-2 py-1 bg-primary/10 text-primary rounded-md text-sm"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Impact: {paper.impact}
                  </span>
                  <Button variant="outline" size="sm" asChild>
                    <a href="#" target="_blank" rel="noopener noreferrer">
                      View Paper
                    </a>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default Literature 