import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        night: '#0D1117',
        panel: '#151B23',
        raised: '#1C2430',
        line: '#2A3441',
        text: '#E6EAF0',
        dim: '#8B96A5',
        signal: '#3DD6B5',
        signalSoft: '#12332D',
        warn: '#F2B53D',
        warnSoft: '#3A2D12',
        crit: '#FF5D5D',
        critSoft: '#3D1719',
        caller: '#8AB4FF',
      },
      fontFamily: {
        sans: ['"Instrument Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config
