import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "./ui/button"
import { Brain } from "lucide-react"

const Navbar = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <div className="mr-4 flex">
          <Link to="/" className="mr-6 flex items-center space-x-2">
            <Brain className="h-6 w-6" />
            <span className="font-bold">Nutritional Psychiatry Database</span>
          </Link>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link to="/" className="transition-colors hover:text-foreground/80">
              Home
            </Link>
            <Link to="/food-data" className="transition-colors hover:text-foreground/80">
              Food Database
            </Link>
            <Link to="/research" className="transition-colors hover:text-foreground/80">
              Research
            </Link>
            <Link to="/methodology" className="transition-colors hover:text-foreground/80">
              Methodology
            </Link>
          </nav>
        </div>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <nav className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/search">Search Foods</Link>
            </Button>
            <Button variant="default" size="sm" asChild>
              <Link to="/expert-collaboration">Expert Collaboration</Link>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Navbar 