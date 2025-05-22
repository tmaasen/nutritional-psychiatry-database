import * as React from "react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion"
import { Brain, Database, FileSearch, Shield } from "lucide-react"

const faqs = [
  {
    question: "What is nutritional psychiatry?",
    answer: "Nutritional psychiatry is an emerging field that studies the relationship between diet, brain function, and mental health. Our database combines traditional nutritional data with brain-specific nutrients and their impacts on mental wellness, backed by scientific research.",
    icon: Brain
  },
  {
    question: "How accurate is the nutrient data?",
    answer: "Our data comes from multiple authoritative sources with a clear prioritization strategy: USDA FoodData Central for standard nutrients, scientific literature for brain-specific nutrients, and AI-assisted predictions for missing data. Each data point includes confidence ratings and source citations.",
    icon: Database
  },
  {
    question: "What sources does the database use?",
    answer: "We integrate data from USDA FoodData Central, OpenFoodFacts, peer-reviewed scientific literature, and AI-assisted analysis. For brain nutrients and mental health impacts, we prioritize literature-based data, followed by AI-generated predictions with confidence ratings.",
    icon: FileSearch
  },
  {
    question: "How are mental health impacts determined?",
    answer: "Mental health impacts are determined through a combination of literature review, expert validation, and AI-assisted analysis. Each impact includes the mechanism of action, strength of evidence, time to effect, and relevant research context.",
    icon: Brain
  },
  {
    question: "Can I contribute research to the database?",
    answer: "Yes! We welcome contributions from researchers and healthcare providers. You can submit research papers, validate existing data, or suggest new connections between nutrients and mental health outcomes. Contact us to join our expert network.",
    icon: Shield
  },
  {
    question: "How often is the database updated?",
    answer: "The database is continuously updated as new research emerges. We regularly incorporate new studies, validate existing data, and refine our AI models. Major updates are released quarterly, with minor updates occurring as new data becomes available.",
    icon: Database
  }
]

const FAQ = () => {
  return (
    <section className="py-20 bg-muted/50">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Frequently Asked Questions
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Find answers to common questions about our database, methodology, and how to use it effectively.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-3xl">
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="flex items-center gap-2 text-left">
                  <div className="rounded-lg bg-primary/10 p-1">
                    <faq.icon className="h-4 w-4 text-primary" />
                  </div>
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>

        <div className="mt-16 text-center">
          <p className="text-muted-foreground">
            Still have questions? Check out our{" "}
            <a href="/methodology" className="text-primary hover:underline">
              detailed methodology
            </a>{" "}
            or{" "}
            <a href="/contact" className="text-primary hover:underline">
              contact our team
            </a>
            .
          </p>
        </div>
      </div>
    </section>
  )
}

export default FAQ 