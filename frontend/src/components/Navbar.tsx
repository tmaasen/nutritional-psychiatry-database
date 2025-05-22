import * as React from "react"
import { Link } from "react-router-dom"
import { Button } from "./ui/button"
import BrainIcon from "./BrainIcon"

const Navbar = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <Link to="/" className="flex items-center space-x-2">
          <BrainIcon size={32} className="text-blue-600" />
          <span className="font-bold">Nutritional Psychiatry Database</span>
        </Link>
        <div className="flex flex-1 items-center justify-end space-x-6">
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link to="/research" className="transition-colors hover:text-foreground/80">
              Research
            </Link>
            <Link to="/methodology" className="transition-colors hover:text-foreground/80">
              Methodology
            </Link>
            <Link to="/food-data" className="transition-colors hover:text-foreground/80">
              Search Foods
            </Link>
          </nav>
          <nav className="flex items-center space-x-2">
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