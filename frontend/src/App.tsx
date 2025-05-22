import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import FoodData from './pages/FoodData'
import FoodDetails from './pages/FoodDetails'
import Research from './pages/Research'
import Methodology from './pages/Methodology'
import Literature from './pages/Literature'
import Dashboard from './pages/Dashboard'
import BackToTop from './components/BackToTop'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/food-data" element={<FoodData />} />
            <Route path="/food/:id" element={<FoodDetails />} />
            <Route path="/research" element={<Research />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/literature" element={<Literature />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
        <Footer />
        <BackToTop />
      </div>
    </Router>
  )
}

export default App 