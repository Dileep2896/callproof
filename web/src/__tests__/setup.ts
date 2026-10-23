import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => cleanup())

class IO {
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return [] }
}
// framer-motion's whileInView needs it in jsdom
;(globalThis as unknown as { IntersectionObserver: unknown }).IntersectionObserver = IO
