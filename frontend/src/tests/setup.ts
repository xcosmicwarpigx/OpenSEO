/// <reference types="vitest/globals" />
import '@testing-library/jest-dom'

// Mock matchMedia
;(globalThis as any).matchMedia = (globalThis as any).matchMedia || function() {
  return {
    matches: false,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }
}

// Mock ResizeObserver
;(globalThis as any).ResizeObserver = function() {
  return {
    observe: () => {},
    unobserve: () => {},
    disconnect: () => {},
  }
}