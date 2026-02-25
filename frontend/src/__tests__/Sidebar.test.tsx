import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

// Mock useLocation
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useLocation: () => ({ pathname: '/' }),
  }
})

describe('Sidebar', () => {
  it('renders OpenSEO branding', () => {
    render(
      <BrowserRouter>
        <Sidebar />
      </BrowserRouter>
    )
    
    expect(screen.getByText('OpenSEO')).toBeInTheDocument()
    expect(screen.getByText('SEO Analysis Platform')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(
      <BrowserRouter>
        <Sidebar />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Site Crawler')).toBeInTheDocument()
    expect(screen.getByText('Competitive Intel')).toBeInTheDocument()
    expect(screen.getByText('Content Optimizer')).toBeInTheDocument()
    expect(screen.getByText('Bulk Analyzer')).toBeInTheDocument()
  })

  it('renders settings link', () => {
    render(
      <BrowserRouter>
        <Sidebar />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })
})