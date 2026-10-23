import { useEffect, useState } from 'react'
import { Console } from './pages/Console'
import { Gate } from './pages/Gate'
import { Story } from './pages/Story'

function usePath(): [string, (p: string) => void] {
  const [path, setPath] = useState(window.location.pathname)
  useEffect(() => {
    const on = () => setPath(window.location.pathname)
    window.addEventListener('popstate', on)
    return () => window.removeEventListener('popstate', on)
  }, [])
  return [path, (p) => { window.history.pushState({}, '', p); setPath(p); window.scrollTo(0, 0) }]
}

const NAV: [string, string][] = [['/', 'Calls'], ['/gate', 'Gate'], ['/story', 'Story']]

export function App() {
  const [path, go] = usePath()
  const page = path.startsWith('/story') ? '/story' : path.startsWith('/gate') ? '/gate' : '/'
  return (
    <div className="min-h-screen bg-night font-sans text-text">
      <nav className="sticky top-0 z-20 border-b border-line bg-night/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-6 py-2.5">
          <a href="/" onClick={(e) => { e.preventDefault(); go('/') }} className="flex items-center gap-2 text-[15px] font-semibold">
            <img src="/favicon.svg" alt="" className="h-6 w-6" />
            Callproof
            <span className="ml-2 hidden text-[12px] font-normal text-dim sm:inline">post-call audit for insurance voice agents</span>
          </a>
          <div className="flex gap-1 text-[13px]">
            {NAV.map(([p, l]) => (
              <a
                key={p}
                href={p}
                onClick={(e) => { e.preventDefault(); go(p) }}
                className={`rounded-md px-3 py-1.5 font-medium ${page === p ? 'bg-text text-night' : 'text-dim hover:text-text'}`}
              >
                {l}
              </a>
            ))}
          </div>
        </div>
      </nav>
      {page === '/story' ? <Story onOpen={() => go('/')} /> : page === '/gate' ? <Gate /> : <Console />}
    </div>
  )
}
