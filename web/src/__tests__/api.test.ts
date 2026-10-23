import { api, isOffline, resetApiCache } from '../api'
import { offlineFetch, snap } from './fixtures'

beforeEach(() => resetApiCache())

test('falls back to the snapshot when the API is down', async () => {
  vi.stubGlobal('fetch', offlineFetch())
  const rows = await api.calls('v14')
  expect(rows).toHaveLength(24)
  expect(isOffline()).toBe(true)
  const g = await api.gate('v14', 'v15')
  expect(g.verdict).toBe('BLOCK')
})

test('uses the live API when it answers', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(snap.health), { status: 200, headers: { 'content-type': 'application/json' } })))
  const h = await api.health()
  expect(h.baseline).toBe('v14')
  expect(isOffline()).toBe(false)
})

test('unknown call id rejects', async () => {
  vi.stubGlobal('fetch', offlineFetch())
  await expect(api.call('NOPE')).rejects.toThrow('not found')
})

test('snapshot agrees with the seeded audit', () => {
  expect(snap.lists['v14'].filter((r) => !r.passed).map((r) => r.scenario).sort()).toEqual(['F02', 'F04', 'M03', 'M05', 'Q03', 'Q05', 'V02', 'V04'])
  expect(snap.gates['v14..v15.1'].verdict).toBe('PASS')
})
