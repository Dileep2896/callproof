import fs from 'node:fs'
import path from 'node:path'
import type { Snapshot } from '../types'

export const snap: Snapshot = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../public/snapshot.json'), 'utf8'))

/** Serve /snapshot.json from the committed snapshot and make every /api call fail (offline mode). */
export function offlineFetch() {
  return vi.fn(async (url: string) => {
    if (url === '/snapshot.json') return new Response(JSON.stringify(snap), { status: 200, headers: { 'content-type': 'application/json' } })
    throw new TypeError('fetch failed')
  })
}
