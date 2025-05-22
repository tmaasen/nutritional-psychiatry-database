import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import FoodData from './pages/FoodData'
import FoodDetails from './pages/FoodDetails'
import Research from './pages/Research'
import Methodology from './pages/Methodology'
import Literature from './pages/Literature'
import Dashboard from './pages/Dashboard'
import ExpertCollaboration from './pages/ExpertCollaboration'
import PrivacyPolicy from './pages/PrivacyPolicy'
import TermsOfService from './pages/TermsOfService'
import Contact from './pages/Contact'
import BackToTop from './components/BackToTop'

function App() {
  return (
    <HelmetProvider>
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
              <Route path="/expert-collaboration" element={<ExpertCollaboration />} />
              <Route path="/privacy" element={<PrivacyPolicy />} />
              <Route path="/terms" element={<TermsOfService />} />
              <Route path="/contact" element={<Contact />} />
            </Routes>
          </main>
          <Footer />
          <BackToTop />
        </div>
      </Router>
    </HelmetProvider>
  )
}

export default App 