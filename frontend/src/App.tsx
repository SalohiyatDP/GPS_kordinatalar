import { useState } from 'react'
import Header from './components/Header'
import CoordinateInput from './components/CoordinateInput'
import PointsTable from './components/PointsTable'
import MapView from './components/MapView'
import ResultsPanel from './components/ResultsPanel'
import CadastrePanel from './components/CadastrePanel'
import { useStore } from './store'

type RightTab = 'results' | 'cadastre'

export default function App() {
  const { t } = useStore()
  const [rightTab, setRightTab] = useState<RightTab>('results')

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Header />
      <div className="flex flex-1 overflow-hidden flex-col lg:flex-row">
        {/* LEFT PANEL */}
        <aside className="w-full lg:w-80 shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-auto panel-scroll p-3 space-y-4">
          <CoordinateInput />
          <div>
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
              {t('inputTab')}
            </h2>
            <PointsTable />
          </div>
        </aside>

        {/* CENTER MAP */}
        <main className="flex-1 relative min-h-[300px]">
          <MapView />
        </main>

        {/* RIGHT PANEL */}
        <aside className="w-full lg:w-80 shrink-0 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-auto panel-scroll">
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
