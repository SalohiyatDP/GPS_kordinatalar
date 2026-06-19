import { create } from 'zustand'
import type { Lang } from './i18n/translations'
import { TRANSLATIONS } from './i18n/translations'
import type {
  AreaResult,
  ContourResult,
  PerimeterResult,
  Point,
} from './types'

interface AppState {
  // i18n & theme
  lang: Lang
  theme: 'light' | 'dark'
  setLang: (l: Lang) => void
  toggleTheme: () => void
  t: (key: string) => string

  // coordinates / points
  points: Point[]
  invalid: Point[]
  duplicatesRemoved: number
  setPoints: (p: Point[]) => void
  setNormalizeResult: (p: Point[], invalid: Point[], dups: number) => void
  movePoint: (index: number, dir: -1 | 1) => void
  deletePoint: (index: number) => void

  // geometry
  area: AreaResult | null
  perimeter: PerimeterResult | null
  polygonGeoJSON: GeoJSON.Polygon | null
  centroid: [number, number] | null
  setGeometry: (
    area: AreaResult,
    perimeter: PerimeterResult,
    poly: GeoJSON.Polygon,
    centroid: [number, number],
  ) => void

  // cadastre
  layerId: string | null
  layerGeoJSON: GeoJSON.FeatureCollection | null
  contours: ContourResult[]
  summary: string
  setLayer: (id: string, gj: GeoJSON.FeatureCollection | null) => void
  setAnalysis: (contours: ContourResult[], summary: string) => void

  // reset
  clearAll: () => void
}

function initialTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  const stored = localStorage.getItem('theme')
  if (stored === 'dark' || stored === 'light') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme: 'light' | 'dark') {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('dark', theme === 'dark')
  localStorage.setItem('theme', theme)
}

const startTheme = initialTheme()
applyTheme(startTheme)

export const useStore = create<AppState>((set, get) => ({
  lang: (localStorage.getItem('lang') as Lang) || 'uz',
  theme: startTheme,
  setLang: (l) => {
    localStorage.setItem('lang', l)
    set({ lang: l })
  },
  toggleTheme: () => {
    const next = get().theme === 'dark' ? 'light' : 'dark'
    applyTheme(next)
    set({ theme: next })
  },
  t: (key) => {
    const dict = TRANSLATIONS[get().lang]
    return dict[key] ?? key
  },

  points: [],
  invalid: [],
  duplicatesRemoved: 0,
  setPoints: (p) => set({ points: renumber(p) }),
  setNormalizeResult: (p, invalid, dups) =>
    set({ points: renumber(p), invalid, duplicatesRemoved: dups }),
  movePoint: (index, dir) => {
    const pts = [...get().points]
    const target = index + dir
    if (target < 0 || target >= pts.length) return
    ;[pts[index], pts[target]] = [pts[target], pts[index]]
    set({ points: renumber(pts) })
  },
  deletePoint: (index) => {
    const pts = get().points.filter((_, i) => i !== index)
    set({ points: renumber(pts) })
  },

  area: null,
  perimeter: null,
  polygonGeoJSON: null,
  centroid: null,
  setGeometry: (area, perimeter, poly, centroid) =>
    set({ area, perimeter, polygonGeoJSON: poly, centroid }),

  layerId: null,
  layerGeoJSON: null,
  contours: [],
  summary: '',
  setLayer: (id, gj) => set({ layerId: id, layerGeoJSON: gj }),
  setAnalysis: (contours, summary) => set({ contours, summary }),

  clearAll: () =>
    set({
      points: [],
      invalid: [],
      duplicatesRemoved: 0,
      area: null,
      perimeter: null,
      polygonGeoJSON: null,
      centroid: null,
      contours: [],
      summary: '',
    }),
}))

function renumber(points: Point[]): Point[] {
  return points.map((p, i) => ({ ...p, point_number: i + 1 }))
}
