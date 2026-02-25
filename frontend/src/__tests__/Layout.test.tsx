import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Layout from '../components/Layout'

describe('Layout', () => {
  it('renders children content', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div data-testid="test-content">Test Content</div>
        </Layout>
      </MemoryRouter>
    )
    
    expect(screen.getByTestId('test-content')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('renders sidebar', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div>Content</div>
        </Layout>
      </MemoryRouter>
    )
    
    expect(screen.getByText('OpenSEO')).toBeInTheDocument()
  })
})