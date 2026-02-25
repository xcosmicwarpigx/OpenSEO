import { Link, useLocation } from 'react-router-dom'
import { Home, Spider, BarChart3, Settings } from 'lucide-react'

const menuItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/crawler', icon: Spider, label: 'Site Crawler' },
  { path: '/competitive', icon: BarChart3, label: 'Competitive Intel' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 bg-white border-r border-gray-200">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-primary-600">OpenSEO</h1>
        <p className="text-sm text-gray-500">SEO Analysis Platform</p>
      </div>
      
      <nav className="px-4 pb-4">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </Link>
          )
        })}
      </nav>
      
      <div className="absolute bottom-0 left-0 w-64 p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-4 py-2 text-gray-600">
          <Settings size={20} />
          <span className="font-medium">Settings</span>
        </div>
      </div>
    </aside>
  )
}
