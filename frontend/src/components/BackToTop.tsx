import { Button } from "./ui/button"
import { ArrowUp } from "lucide-react"
import { useEffect, useState } from "react"

const BackToTop = () => {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const toggleVisibility = () => {
      if (window.pageYOffset > 300) {
        setIsVisible(true)
      } else {
        setIsVisible(false)
      }
    }

    window.addEventListener("scroll", toggleVisibility)
    return () => window.removeEventListener("scroll", toggleVisibility)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth"
    })
  }

  if (!isVisible) return null

  return (
    <Button
      onClick={scrollToTop}
      className="fixed bottom-4 right-4 rounded-full p-2 shadow-lg transition-all hover:scale-105"
      size="icon"
    >
      <ArrowUp className="h-4 w-4" />
    </Button>
  )
}

export default BackToTop 