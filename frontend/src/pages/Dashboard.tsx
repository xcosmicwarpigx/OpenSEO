import { useState, useEffect } from 'react'
import { apiClient } from '../api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { Activity, Globe, Search, AlertTriangle } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_crawls: 0,
    active_tasks: 0,
    avg_lcp: 0,
    issues_found: 0
  })
  
  useEffect(() => {
    apiClient.getDashboardStats().then(res => {
      setStats(prev => ({ ...prev, ...res.data }))
    })
  }, [])

  const mockTrafficData = [
    { month: 'Jan', traffic: 45000 },
    { month: 'Feb', traffic: 52000 },
    { month: 'Mar', traffic: 48000 },
    { month: 'Apr', traffic: 61000 },
    { month: 'May', traffic: 68000 },
    { month: 'Jun', traffic: 72000 },
  ]

  const mockKeywordData = [
    { position: '1-3', count: 45 },
    { position: '4-10', count: 89 },
    { position: '11-20', count: 156 },
    { position: '21-50', count: 324 },
  ]

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h2>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Crawls</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_crawls}</p>
            </div>
            <div className="p-3 bg-primary-50 rounded-lg">
              <Globe className="text-primary-600" size={24} />
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Active Tasks</p>
              <p className="text-2xl font-bold text-gray-900">{stats.active_tasks}</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <Activity className="text-green-600" size={24} />
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Avg LCP</p>
              <p className="text-2xl font-bold text-gray-900">1.2s</p>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg">
              <Search className="text-yellow-600" size={24} />
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Issues Found</p>
              <p className="text-2xl font-bold text-gray-900">23</p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <AlertTriangle className="text-red-600" size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Organic Traffic Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mockTrafficData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip />
              <Line type="monotone" dataKey="traffic" stroke="#0ea5e9" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Keyword Positions</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={mockKeywordData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="position" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip />
              <Bar dataKey="count" fill="#0ea5e9" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
