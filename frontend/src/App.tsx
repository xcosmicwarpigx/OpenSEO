import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Crawler from './pages/Crawler'
import Competitive from './pages/Competitive'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/crawler" element={<Crawler />} />
        <Route path="/competitive" element={<Competitive />} />
      </Routes>
    </Layout>
  )
}

export default App
