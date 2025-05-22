import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar"
import { Quote } from "lucide-react"

const testimonials = [
  {
    quote: "This database represents a significant advancement in nutritional psychiatry research. The comprehensive analysis of brain nutrients and their mental health impacts provides valuable insights for both researchers and healthcare providers.",
    author: "Dr. Sarah Johnson",
    role: "Nutritional Psychiatry Researcher",
    institution: "Harvard Medical School",
    avatar: "/avatars/sarah-johnson.jpg",
    initials: "SJ"
  },
  {
    quote: "As a clinical dietitian specializing in mental health, I find this database invaluable. The evidence-based approach and detailed nutrient profiles help me make more informed recommendations for my patients.",
    author: "Dr. Michael Chen",
    role: "Clinical Dietitian",
    institution: "Stanford University",
    avatar: "/avatars/michael-chen.jpg",
    initials: "MC"
  },
  {
    quote: "The integration of AI-assisted analysis with traditional research methods creates a powerful tool for understanding the complex relationship between nutrition and mental wellness. This database fills a crucial gap in our field.",
    author: "Dr. Emily Rodriguez",
    role: "Neuroscience Researcher",
    institution: "MIT",
    avatar: "/avatars/emily-rodriguez.jpg",
    initials: "ER"
  }
]

const ExpertEndorsements = () => {
  return (
    <section className="py-20">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Expert Endorsements
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Our database is trusted and validated by leading experts in nutritional psychiatry, neuroscience, and clinical practice.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((testimonial) => (
            <Card key={testimonial.author} className="relative">
              <CardHeader>
                <div className="absolute -top-4 left-6 rounded-full bg-primary/10 p-2">
                  <Quote className="h-4 w-4 text-primary" />
                </div>
                <div className="mt-4 flex items-center gap-4">
                  <Avatar>
                    <AvatarImage src={testimonial.avatar} alt={testimonial.author} />
                    <AvatarFallback>{testimonial.initials}</AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-lg">{testimonial.author}</CardTitle>
                    <CardDescription>
                      {testimonial.role}
                      <br />
                      {testimonial.institution}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{testimonial.quote}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-16 rounded-lg bg-muted/50 p-8 text-center">
          <h3 className="text-xl font-semibold">Join Our Expert Network</h3>
          <p className="mt-2 text-muted-foreground">
            Are you a researcher or healthcare provider interested in contributing to our database?
            We welcome collaboration with experts in nutritional psychiatry and related fields.
          </p>
          <div className="mt-6 flex justify-center gap-4">
            <a
              href="mailto:experts@nutritionalpsychiatry.org"
              className="text-sm text-primary hover:underline"
            >
              Contact Us →
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}

export default ExpertEndorsements 