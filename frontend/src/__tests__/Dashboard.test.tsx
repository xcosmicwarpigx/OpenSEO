import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../pages/Dashboard'

// Mock the API module
vi.mock('../api', () => ({
  apiClient: {
    getDashboardStats: vi.fn().mockResolvedValue({
      data: {
        total_crawls: 5,
        active_tasks: 2,
        tools_available: [
          { id: 'crawler', name: 'Site Crawler' },
          { id: 'content_optimizer', name: 'Content Optimizer' }
        ]
      }
    })
  }
}))

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders stat cards', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Total Crawls')).toBeInTheDocument()
    expect(screen.getByText('Active Tasks')).toBeInTheDocument()
    expect(screen.getByText('Avg LCP')).toBeInTheDocument()
    expect(screen.getByText('Issues Found')).toBeInTheDocument()
  })

  it('renders charts section', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Organic Traffic Trend')).toBeInTheDocument()
    expect(screen.getByText('Keyword Positions')).toBeInTheDocument()
  })
})