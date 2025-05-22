import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"

const Methodology = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">Our Methodology</h1>
      
      <div className="grid gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Data Collection</CardTitle>
            <CardDescription>
              How we gather and validate nutritional psychiatry data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">
              Our methodology combines multiple data sources to create a comprehensive understanding of the relationship between food and mental health:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>USDA FoodData Central for standard nutritional information</li>
              <li>Peer-reviewed scientific literature for brain-specific nutrients</li>
              <li>AI-assisted analysis for data gap filling</li>
              <li>Expert validation for quality assurance</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI-Assisted Analysis</CardTitle>
            <CardDescription>
              How we use artificial intelligence to enhance our understanding
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">
              Our AI system processes and analyzes data through several key steps:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Natural language processing of scientific literature</li>
              <li>Pattern recognition in nutrient-mental health relationships</li>
              <li>Confidence scoring for predictions</li>
              <li>Continuous learning from new research</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quality Assurance</CardTitle>
            <CardDescription>
              Our rigorous validation process
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4">
              Every data point in our database undergoes multiple validation steps:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Source prioritization based on reliability</li>
              <li>Cross-validation across multiple sources</li>
              <li>Expert review of AI predictions</li>
              <li>Regular updates with new research findings</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Methodology 