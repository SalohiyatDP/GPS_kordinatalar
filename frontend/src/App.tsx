import { useCallback, useEffect, useRef, useState } from 'react'
import Header from './components/Header'
import CoordinateInput from './components/CoordinateInput'
import PointsTable from './components/PointsTable'
import MapView from './components/MapView'
import ResultsPanel from './components/ResultsPanel'
import CadastrePanel from './components/CadastrePanel'
import { useStore } from './store'

type RightTab = 'results' | 'cadastre'

const MIN_W = 240
const MAX_W = 640

export default function App() {
  const { t } = useStore()
  const [rightTab, setRightTab] = useState<RightTab>('results')

  const [leftW, setLeftW] = useState(320)
  const [rightW, setRightW] = useState(320)
  const [isWide, setIsWide] = useState(
    typeof window !== 'undefined' ? window.innerWidth >= 1024 : true,
  )
  const dragging = useRef<null | 'left' | 'right'>(null)

  useEffect(() => {
    const onResize = () => setIsWide(window.innerWidth >= 1024)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const onMouseMove = useCallback((e: MouseEvent) => {
    if (!dragging.current) return
    if (dragging.current === 'left') {
      setLeftW(Math.min(MAX_W, Math.max(MIN_W, e.clientX)))
    } else {
      setRightW(Math.min(MAX_W, Math.max(MIN_W, window.innerWidth - e.clientX)))
    }
  }, [])

  const stopDrag = useCallback(() => {
    dragging.current = null
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }, [])

  useEffect(() => {
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', stopDrag)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', stopDrag)
    }
  }, [onMouseMove, stopDrag])

  const startDrag = (side: 'left' | 'right') => (e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = side
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Header />
      <div className="flex flex-1 overflow-hidden flex-col lg:flex-row">
        {/* LEFT PANEL */}
        <aside
          className="w-full shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-auto panel-scroll p-3 space-y-4"
          style={isWide ? { width: leftW, flex: '0 0 auto' } : undefined}
        >
          <CoordinateInput />
          <div>
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
              {t('inputTab')}
            </h2>
            <PointsTable />
          </div>
        </aside>

        {/* LEFT RESIZER */}
        {isWide && <Resizer onMouseDown={startDrag('left')} />}

        {/* CENTER MAP */}
        <main className="flex-1 relative min-h-[300px]">
          <MapView />
        </main>

        {/* RIGHT RESIZER */}
        {isWide && <Resizer onMouseDown={startDrag('right')} />}

        {/* RIGHT PANEL */}
        <aside
          className="w-full shrink-0 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-auto panel-scroll"
          style={isWide ? { width: rightW, flex: '0 0 auto' } : undefined}
        >
          <div className="flex border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
            <TabButton
              active={rightTab === 'results'}
              onClick={() => setRightTab('results')}
            >
              {t('results')}
            </TabButton>
            <TabButton
              active={rightTab === 'cadastre'}
              onClick={() => setRightTab('cadastre')}
            >
              {t('cadastreTab')}
            </TabButton>
          </div>
          <div className="p-3">
            {rightTab === 'results' ? <ResultsPanel /> : <CadastrePanel />}
          </div>
        </aside>
      </div>
    </div>
  )
}

function Resizer({ onMouseDown }: { onMouseDown: (e: React.MouseEvent) => void }) {
  return (
    <div
      onMouseDown={onMouseDown}
      title="Surish"
      className="hidden lg:flex w-1.5 cursor-col-resize bg-gray-200 dark:bg-gray-700 hover:bg-brand active:bg-brand transition-colors items-center justify-center group"
    >
      <div className="h-10 w-0.5 bg-gray-400 dark:bg-gray-500 group-hover:bg-white rounded" />
    </div>
  )
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={
        'flex-1 text-sm py-2 font-medium transition-colors ' +
        (active
          ? 'text-brand border-b-2 border-brand'
          : 'text-gray-500 dark:text-gray-400 hover:text-brand')
      }
    >
      {children}
    </button>
  )
}
