import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { resetApiCache } from '../api'
import { Console } from '../pages/Console'
import { Gate } from '../pages/Gate'
import { Story } from '../pages/Story'
import { offlineFetch } from './fixtures'

beforeEach(() => {
  resetApiCache()
  vi.stubGlobal('fetch', offlineFetch())
  window.history.replaceState({}, '', '/')
})

test('console opens the first failing call and highlights the evidence', async () => {
  render(<Console />)
  expect(await screen.findByText(/8/, { selector: 'span.tabular' })).toBeInTheDocument()
  const transcript = await screen.findByTestId('transcript')
  const mark = within(transcript).getByText('$1,284')
  expect(mark.tagName).toBe('MARK')
  expect(screen.getByText(/read-only snapshot/)).toBeInTheDocument()
})

test('console deep link and switching versions keeps the scenario', async () => {
  window.history.replaceState({}, '', '/?call=F02-v14')
  render(<Console />)
  expect(await screen.findByText(/started at 71 s/, { selector: 'p.text-\\[12\\.5px\\]' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('tab', { name: /v15\.1/ }))
  expect(await screen.findByText(/All 7 rules pass/)).toBeInTheDocument()
  expect(screen.getByText('F02-v15.1', { exact: false })).toBeInTheDocument()
})

test('gate shows BLOCK for v15 and PASS for v15.1', async () => {
  render(<Gate />)
  const verdict = await screen.findByTestId('verdict')
  expect(within(verdict).getByText('BLOCK')).toBeInTheDocument()
  expect(within(verdict).getByText(/Q01 passed on v14/)).toBeInTheDocument()
  expect(screen.getByTestId('case-Q01')).toHaveTextContent('regressed')
  await userEvent.click(screen.getByRole('tab', { name: /v15\.1/ }))
  expect(await screen.findByText('PASS')).toBeInTheDocument()
})

test('story renders the measured impact rows', async () => {
  render(<Story onOpen={() => {}} />)
  expect(screen.getByTestId('story-hero')).toHaveTextContent('quote a premium')
  const impact = await screen.findByTestId('impact')
  expect(impact).toHaveTextContent('Critical regressions shipped by prompt v15')
  expect(impact).toHaveTextContent('0 (gate blocks)')
})
