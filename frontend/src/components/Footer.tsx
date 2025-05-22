import * as React from "react"
import { Link } from "react-router-dom"
import { Brain } from "lucide-react"

const Footer = () => {
  return (
    <footer className="border-t bg-background">
      <div className="container py-8 md:py-12">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          <div className="flex flex-col space-y-4">
            <div className="flex items-center space-x-2">
              <Brain className="h-6 w-6" />
              <span className="font-bold">NPD</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Connecting food, brain health, and mental wellness through evidence-based research.
            </p>
          </div>
          <div className="flex flex-col space-y-4">
            <h4 className="text-sm font-medium">Resources</h4>
            <nav className="flex flex-col space-y-2">
              <Link to="/research" className="text-sm text-muted-foreground hover:text-foreground">
                Research Papers
              </Link>
              <Link to="/methodology" className="text-sm text-muted-foreground hover:text-foreground">
                Methodology
              </Link>
              <Link to="/expert-collaboration" className="text-sm text-muted-foreground hover:text-foreground">
                Expert Guidelines
              </Link>
            </nav>
          </div>
          <div className="flex flex-col space-y-4">
            <h4 className="text-sm font-medium">Data</h4>
            <nav className="flex flex-col space-y-2">
              <Link to="/food-data" className="text-sm text-muted-foreground hover:text-foreground">
                Food Database
              </Link>
              <Link to="/sources" className="text-sm text-muted-foreground hover:text-foreground">
                Data Sources
              </Link>
              <Link to="/updates" className="text-sm text-muted-foreground hover:text-foreground">
                Updates
              </Link>
            </nav>
          </div>
          <div className="flex flex-col space-y-4">
            <h4 className="text-sm font-medium">Legal</h4>
            <nav className="flex flex-col space-y-2">
              <Link to="/terms" className="text-sm text-muted-foreground hover:text-foreground">
                Terms of Service
              </Link>
              <Link to="/privacy" className="text-sm text-muted-foreground hover:text-foreground">
                Privacy Policy
              </Link>
              <Link to="/contact" className="text-sm text-muted-foreground hover:text-foreground">
                Contact
              </Link>
            </nav>
          </div>
        </div>
        <div className="mt-8 border-t pt-8">
          <p className="text-center text-sm text-muted-foreground">
            © {new Date().getFullYear()} Nutritional Psychiatry Database. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer 