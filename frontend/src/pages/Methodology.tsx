import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import SEO from '../components/SEO'
import { Brain, Database, FileText, TestTube } from "lucide-react"
import Mermaid from '../components/Mermaid'

const Methodology = () => {
  const dataCollectionChart = `flowchart TD
    %% Data Collection Sources
    USDA[USDA FoodData Central API]
    OFF[OpenFoodFacts API]
    LIT[Scientific Literature]
    MAN[Manual Entry]
    
    %% Collection Scripts
    USDA_SCRIPT[usda-api.py]
    OFF_SCRIPT[openfoodfacts-api.py]
    LIT_SCRIPT[literature-extract.py]
    MAN_SCRIPT[manual-entry-tool]
    
    %% Raw Data
    RAW_USDA[raw/usda_foods/*.json]
    RAW_OFF[raw/openfoodfacts/*.json]
    RAW_LIT[raw/literature/*.json]
    RAW_MAN[raw/manual_entries/*.json]
    
    %% Connections
    USDA --> USDA_SCRIPT
    OFF --> OFF_SCRIPT
    LIT --> LIT_SCRIPT
    MAN --> MAN_SCRIPT
    
    USDA_SCRIPT --> RAW_USDA
    OFF_SCRIPT --> RAW_OFF
    LIT_SCRIPT --> RAW_LIT
    MAN_SCRIPT --> RAW_MAN`

  const aiEnrichmentChart = `flowchart TD
    %% Input Data
    BASE[Base Food Data with Gaps]
    
    %% Enrichment Components
    TEMPLATE[Load Prompt Template]
    API[OpenAI API Client]
    PARSE[Parse & Validate Response]
    
    %% Enrichment Types
    BRAIN[Brain Nutrient Prediction]
    BIO[Bioactive Compound Prediction]
    IMPACT[Mental Health Impact Generation]
    INTERACT[Nutrient Interaction Identification]
    
    %% Quality Control
    VALIDATE[Known-Answer Testing]
    CALIBRATE[Confidence Calibration]
    
    %% Output
    ENRICHED[Enriched Food Data]
    
    %% Flow
    BASE --> BRAIN
    BASE --> BIO
    BASE --> IMPACT
    BASE --> INTERACT
    
    BRAIN --> TEMPLATE
    BIO --> TEMPLATE
    IMPACT --> TEMPLATE
    INTERACT --> TEMPLATE
    
    TEMPLATE --> API
    API --> PARSE
    PARSE --> VALIDATE
    VALIDATE --> CALIBRATE
    CALIBRATE --> ENRICHED`

  const sourcePrioritizationChart = `flowchart TB
    %% Input Sources
    USDA[USDA Data]
    OFF[OpenFoodFacts Data]
    LIT[Literature-Derived Data]
    AI[AI-Generated Data]
    
    %% Prioritization Process
    MERGE[Source Prioritization Process]
    
    %% Standard Nutrients
    SN_USDA[1. USDA]
    SN_OFF[2. OpenFoodFacts]
    SN_LIT[3. Literature]
    SN_AI[4. AI-Generated]
    
    %% Brain Nutrients
    BN_LIT[1. Literature]
    BN_USDA[2. USDA]
    BN_OFF[3. OpenFoodFacts]
    BN_AI[4. AI-Generated]
    
    %% Mental Health Impacts
    MH_LIT[1. Literature]
    MH_AI[2. AI-Generated with Citations]
    
    %% Merger Logic
    COMPONENT[Component-Level Merger]
    FIELD[Field-By-Field Selection]
    CONFLICT[Conflict Resolution]
    CONFIDENCE[Confidence Tracking]
    
    %% Output
    MERGED[Merged Food Entry with Source Tracking]
    
    %% Connections
    USDA --> MERGE
    OFF --> MERGE
    LIT --> MERGE
    AI --> MERGE
    
    MERGE --> SN_USDA
    SN_USDA --> SN_OFF
    SN_OFF --> SN_LIT
    SN_LIT --> SN_AI
    
    MERGE --> BN_LIT
    BN_LIT --> BN_USDA
    BN_USDA --> BN_OFF
    BN_OFF --> BN_AI
    
    MERGE --> MH_LIT
    MH_LIT --> MH_AI
    
    SN_AI --> COMPONENT
    BN_AI --> COMPONENT
    MH_AI --> COMPONENT
    
    COMPONENT --> FIELD
    FIELD --> CONFLICT
    CONFLICT --> CONFIDENCE
    CONFIDENCE --> MERGED`

  return (
    <>
      <SEO
        title="Methodology"
        description="Learn about our comprehensive methodology for creating the Nutritional Psychiatry Database, including data collection, AI enrichment, and validation processes."
        keywords={['methodology', 'data collection', 'AI enrichment', 'nutritional psychiatry', 'brain nutrients']}
      />

      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Our Methodology</h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            A comprehensive approach combining traditional nutritional data with AI-assisted enrichment to create the most complete database of brain-relevant nutrients.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 max-w-6xl mx-auto mb-12">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Database className="h-5 w-5" />
                <CardTitle>Data Collection</CardTitle>
              </div>
              <CardDescription>
                Multi-source integration from authoritative databases
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose prose-gray max-w-none">
                <p>Our foundation data comes from multiple authoritative sources:</p>
                <ul>
                  <li>USDA FoodData Central (primary source)</li>
                  <li>OpenFoodFacts API</li>
                  <li>Scientific Literature</li>
                  <li>Manual Expert Entry</li>
                </ul>
                <p>Each source is processed through dedicated scripts to ensure consistent data format and quality.</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Brain className="h-5 w-5" />
                <CardTitle>Brain Nutrient Enrichment</CardTitle>
              </div>
              <CardDescription>
                AI-assisted prediction of brain-specific nutrients
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose prose-gray max-w-none">
                <p>When brain-specific nutrients are missing, we use a multi-tiered approach:</p>
                <ol>
                  <li>Literature search for direct measurements</li>
                  <li>Derivation from related nutrients</li>
                  <li>AI-assisted prediction based on similar foods</li>
                </ol>
                <p>Each prediction includes confidence ratings and validation against known values.</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <TestTube className="h-5 w-5" />
                <CardTitle>AI Enrichment Process</CardTitle>
              </div>
              <CardDescription>
                Advanced AI methodology for data enrichment
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose prose-gray max-w-none">
                <p>Our AI enrichment pipeline includes:</p>
                <ul>
                  <li>Brain-nutrient prediction</li>
                  <li>Bioactive compound prediction</li>
                  <li>Mental health impact generation</li>
                  <li>Nutrient interaction identification</li>
                </ul>
                <p>Each prediction is validated and calibrated for accuracy.</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <CardTitle>Quality Control</CardTitle>
              </div>
              <CardDescription>
                Rigorous validation and confidence scoring
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="prose prose-gray max-w-none">
                <p>Our quality control system ensures data accuracy through:</p>
                <ul>
                  <li>Confidence calibration</li>
                  <li>Known-answer testing</li>
                  <li>Validation rules</li>
                  <li>Expert review</li>
                </ul>
                <p>Each data point includes a confidence rating and source information.</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-6">Data Collection Process</h2>
          <div className="bg-muted p-4 rounded-lg mb-8">
            <Mermaid chart={dataCollectionChart} />
          </div>

          <h2 className="text-2xl font-bold mb-6">AI Enrichment Pipeline</h2>
          <div className="bg-muted p-4 rounded-lg mb-8">
            <Mermaid chart={aiEnrichmentChart} />
          </div>

          <h2 className="text-2xl font-bold mb-6">Source Prioritization</h2>
          <div className="bg-muted p-4 rounded-lg">
            <Mermaid chart={sourcePrioritizationChart} />
          </div>
        </div>
      </div>
    </>
  )
}

export default Methodology 