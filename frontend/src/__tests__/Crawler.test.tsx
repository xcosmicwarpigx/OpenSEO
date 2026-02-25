import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Crawler from '../pages/Crawler'

// Mock the API module
vi.mock('../api', () => ({
  apiClient: {
    startCrawl: vi.fn().mockResolvedValue({
      data: { task_id: 'test-task-123', status: 'pending' }
    }),
    getCrawlStatus: vi.fn().mockResolvedValue({
      data: { status: 'SUCCESS', result: { pages_crawled: 10 } }
    })
  }
}))

describe('Crawler', () => {
  it('renders crawler page title', () => {
    render(
      <BrowserRouter>
        <Crawler />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Site Crawler')).toBeInTheDocument()
  })

  it('renders input form', () => {
    render(
      <BrowserRouter>
        <Crawler />
      </BrowserRouter>
    )
    
    expect(screen.getByLabelText('Website URL')).toBeInTheDocument()
    expect(screen.getByLabelText('Max Pages')).toBeInTheDocument()
    expect(screen.getByText('Check Core Web Vitals')).toBeInTheDocument()
  })

  it('renders start crawl button', () => {
    render(
      <BrowserRouter>
        <Crawler />
      </BrowserRouter>
    )
    
    expect(screen.getByRole('button', { name: /start crawl/i })).toBeInTheDocument()
  })

  it('updates URL input when typed', () => {
    render(
      <BrowserRouter>
        <Crawler />
      </BrowserRouter>
    )
    
    const input = screen.getByPlaceholderText('https://example.com')
    fireEvent.change(input, { target: { value: 'https://test.com' } })
    
    expect(input).toHaveValue('https://test.com')
  })
})