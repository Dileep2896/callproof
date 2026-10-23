import { clock, money, splitSpans } from '../format'

test('clock formats seconds', () => {
  expect(clock(0)).toBe('0:00')
  expect(clock(71.4)).toBe('1:11')
})

test('money', () => {
  expect(money(1248)).toBe('$1,248')
})

test('splitSpans marks evidence and keeps the rest', () => {
  const text = 'It is $1,284 a year.'
  const p = splitSpans(text, [{ start: 6, end: 12, severity: 'critical' }])
  expect(p).toEqual([
    { text: 'It is ', mark: null },
    { text: '$1,284', mark: 'critical' },
    { text: ' a year.', mark: null },
  ])
  expect(p.map((x) => x.text).join('')).toBe(text)
})

test('splitSpans ignores invalid and overlapping spans', () => {
  const p = splitSpans('abcdef', [{ start: 1, end: 3, severity: 'high' }, { start: 2, end: 4, severity: 'high' }, { start: 4, end: 99, severity: 'high' }])
  expect(p.map((x) => x.text).join('')).toBe('abcdef')
  expect(p.filter((x) => x.mark).length).toBe(1)
})
