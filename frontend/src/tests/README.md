# Frontend Testing

This directory contains all tests for the OpenSEO frontend.

## Structure

```
src/
├── __tests__/           # Component tests
│   ├── Sidebar.test.tsx
│   ├── Layout.test.tsx
│   ├── Dashboard.test.tsx
│   └── Crawler.test.tsx
└── tests/
    └── setup.ts         # Test configuration
```

## Running Tests

### Run tests in watch mode (development)
```bash
npm test
```

### Run tests once
```bash
npm test -- --run
```

### Run with UI
```bash
npm run test:ui
```

### Run with coverage
```bash
npm run coverage
```

### Run specific test file
```bash
npm test -- Sidebar.test.tsx
```

## Test Coverage

Coverage reports are generated in `coverage/` directory.

View coverage report:
```bash
open coverage/index.html
```

## Writing Tests

### Component Test Example
```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MyComponent from '../components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### Testing with User Events
```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

describe('Form', () => {
  it('handles input changes', () => {
    render(<Form />)
    const input = screen.getByLabelText('Name')
    fireEvent.change(input, { target: { value: 'John' } })
    expect(input).toHaveValue('John')
  })
})
```

### Mocking API Calls
```tsx
import { vi } from 'vitest'
import { apiClient } from '../api'

vi.mock('../api', () => ({
  apiClient: {
    getData: vi.fn().mockResolvedValue({ data: 'test' })
  }
}))
```

## Testing Best Practices

1. **Test behavior, not implementation** - Focus on what the user sees/interacts with
2. **Use semantic queries** - Prefer `getByRole`, `getByLabelText` over `getByTestId`
3. **Mock external dependencies** - API calls, browser APIs
4. **Keep tests isolated** - Each test should be independent
5. **Use descriptive test names** - Clear descriptions help debugging

## Continuous Integration

Tests are automatically run on every push and pull request.
See `.github/workflows/ci.yml` for CI configuration.