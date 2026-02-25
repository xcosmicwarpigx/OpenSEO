import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Crawler from './pages/Crawler'
import Competitive from './pages/Competitive'
import ContentOptimizer from './pages/ContentOptimizer'
import BulkAnalyzer from './pages/BulkAnalyzer'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/crawler" element={<Crawler />} />
        <Route path="/competitive" element={<Competitive />} />
        <Route path="/content-optimizer" element={<ContentOptimizer />} />
        <Route path="/bulk-analyzer" element={<BulkAnalyzer />} />
      </Routes>
    </Layout>
  )
}

export default App
