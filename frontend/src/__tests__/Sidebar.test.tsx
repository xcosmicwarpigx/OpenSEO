import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

describe('Sidebar', () => {
  it('renders OpenSEO branding', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    
    expect(screen.getByText('OpenSEO')).toBeInTheDocument()
    expect(screen.getByText('SEO Analysis Platform')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Site Crawler')).toBeInTheDocument()
    expect(screen.getByText('Competitive Intel')).toBeInTheDocument()
    expect(screen.getByText('Content Optimizer')).toBeInTheDocument()
    expect(screen.getByText('Bulk Analyzer')).toBeInTheDocument()
  })

  it('renders settings link', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })
})