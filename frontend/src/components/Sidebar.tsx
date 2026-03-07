import { Link, useLocation } from 'react-router-dom'
import { Home, Bug, BarChart3, FileText, List, Settings } from 'lucide-react'

const menuItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/crawler', icon: Bug, label: 'Site Crawler' },
  { path: '/competitive', icon: BarChart3, label: 'Competitive Intel' },
  { path: '/content-optimizer', icon: FileText, label: 'Content Optimizer' },
  { path: '/bulk-analyzer', icon: List, label: 'Bulk Analyzer' },
]

interface SidebarProps {
  onNavigate?: () => void
}

export default function Sidebar({ onNavigate }: SidebarProps) {
  const location = useLocation()

  return (
    <aside className="h-full bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 sm:p-6">
        <h1 className="text-xl sm:text-2xl font-bold text-primary-600">OpenSEO</h1>
        <p className="text-sm text-gray-500">SEO Analysis Platform</p>
      </div>

      <nav className="px-3 sm:px-4 pb-4 flex-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path

          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={onNavigate}
              className={`flex items-center gap-3 px-3 sm:px-4 py-3 rounded-lg mb-1 transition-colors ${
                isActive ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium text-sm sm:text-base">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-3 sm:px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg cursor-pointer">
          <Settings size={20} />
          <span className="font-medium text-sm sm:text-base">Settings</span>
        </div>
      </div>
    </aside>
  )
}
