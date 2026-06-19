import { useRef, useState } from 'react'
import { useStore } from '../store'
import {
  analyzePolygon,
  analyzeUzkad,
  deleteLayer,
  generateReport,
  getErrorMessage,
  getLayerGeoJSON,
  uploadContours,
} from '../api/client'
import type { ContourResult } from '../types'

type Mode = 'kontur' | 'uzkad'

export default function CadastrePanel() {
  const store = useStore()
  const { t } = store
  const [mode, setMode] = useState<Mode>('kontur')

  return (
    <div className="space-y-3">
      <div className="flex rounded overflow-hidden border border-gray-300 dark:border-gray-600 text-xs">
        <button
          onClick={() => setMode('kontur')}
          className={
            'flex-1 py-1.5 font-medium ' +
            (mode === 'kontur'
              ? 'bg-brand text-white'
              : 'bg-transparent text-gray-600 dark:text-gray-300')
          }
        >
          {t('konturSection')}
        </button>
        <button
          onClick={() => setMode('uzkad')}
          className={
            'flex-1 py-1.5 font-medium ' +
            (mode === 'uzkad'
              ? 'bg-brand text-white'
              : 'bg-transparent text-gray-600 dark:text-gray-300')
          }
        >
          {t('uzkadSection')}
        </button>
      </div>

      {mode === 'kontur' ? <KonturSection /> : <UzkadSection />}
    </div>
  )
}

/* ----------------------------- Kontur section ----------------------------- */

function KonturSection() {
  const {
    t, points, layerId, layerGeoJSON, contours, summary,
    setLayer, setAnalysis, clearContourLayer,
  } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [count, setCount] = useState<number | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await uploadContours(file)
      setCount(res.feature_count)
      const gj = await getLayerGeoJSON(res.layer_id, 0.0002)
      setLayer(res.layer_id, gj)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function analyze() {
    if (!layerId || points.length < 3) return
    setLoading(true)
    setError(null)
    try {
      const res = await analyzePolygon(
        layerId,
        points.map((p) => ({ latitude: p.latitude, longitude: p.longitude })),
      )
      setAnalysis(res.contours, res.summary)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function clearLayer() {
    const id = layerId
    clearContourLayer()
    setCount(null)
    if (id) {
      try {
        await deleteLayer(id)
      } catch {
        /* ignore */
      }
    }
  }

  return (
    <>
      <UploadRow
        label={t('uploadContour')}
        onUpload={handleUpload}
        fileRef={fileRef}
        loading={loading}
        loaded={layerGeoJSON !== null}
        count={count}
        onClear={clearLayer}
      />
      <button
        onClick={analyze}
        disabled={loading || !layerId || points.length < 3}
        className="w-full bg-brand hover:bg-brand-light text-white text-sm rounded px-3 py-2 disabled:opacity-50"
      >
        {loading ? t('loading') : t('analyzePolygon')}
      </button>
      {error && <p className="text-xs text-red-600 break-words">{error}</p>}
      {contours.length > 0 && (
        <ResultsBlock
          results={contours}
          summary={summary}
          idLabel={t('contour')}
          reportLabel="Kontur"
        />
      )}
    </>
  )
}

/* ----------------------------- UZKAD section ------------------------------ */

function UzkadSection() {
  const {
    t, points, uzkadLayerId, uzkadGeoJSON, uzkadResults, uzkadSummary,
    setUzkadLayer, setUzkadAnalysis, clearUzkadLayer,
  } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [count, setCount] = useState<number | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await uploadContours(file)
      setCount(res.feature_count)
      const gj = await getLayerGeoJSON(res.layer_id, 0.0002)
      setUzkadLayer(res.layer_id, gj)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function analyze() {
    if (!uzkadLayerId || points.length < 3) return
    setLoading(true)
    setError(null)
    try {
      const res = await analyzeUzkad(
        uzkadLayerId,
        points.map((p) => ({ latitude: p.latitude, longitude: p.longitude })),
      )
      setUzkadAnalysis(res.contours, res.summary)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function clearLayer() {
    const id = uzkadLayerId
    clearUzkadLayer()
    setCount(null)
    if (id) {
      try {
        await deleteLayer(id)
      } catch {
        /* ignore */
      }
    }
  }

  return (
    <>
      <UploadRow
        label={t('uploadUzkad')}
        onUpload={handleUpload}
        fileRef={fileRef}
        loading={loading}
        loaded={uzkadGeoJSON !== null}
        count={count}
        onClear={clearLayer}
      />
      <button
        onClick={analyze}
        disabled={loading || !uzkadLayerId || points.length < 3}
        className="w-full bg-brand hover:bg-brand-light text-white text-sm rounded px-3 py-2 disabled:opacity-50"
      >
        {loading ? t('loading') : t('analyzeUzkad')}
      </button>
      {error && <p className="text-xs text-red-600 break-words">{error}</p>}
      {uzkadResults.length > 0 && (
        <ResultsBlock
          results={uzkadResults}
          summary={uzkadSummary}
          idLabel={t('cadastralNumber')}
          reportLabel="Kadastr"
        />
      )}
    </>
  )
}

/* ------------------------------ Shared parts ------------------------------ */

function UploadRow({
  label, onUpload, fileRef, loading, loaded, count, onClear,
}: {
  label: string
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
  fileRef: React.RefObject<HTMLInputElement | null>
  loading: boolean
  loaded: boolean
  count: number | null
  onClear: () => void
}) {
  const { t } = useStore()
  return (
    <div className="space-y-1.5">
      <div className="flex gap-1.5">
        <button
          onClick={() => fileRef.current?.click()}
          disabled={loading}
          className="flex-1 border border-brand text-brand dark:text-brand-light text-sm rounded px-3 py-2 hover:bg-brand/10 disabled:opacity-50"
        >
          {label}
        </button>
        {loaded && (
          <button
            onClick={onClear}
            title={t('clearLayer')}
            className="border border-red-400 text-red-600 dark:text-red-400 text-sm rounded px-3 py-2 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            🗑
          </button>
        )}
      </div>
      <input
        ref={fileRef}
        type="file"
        accept=".zip"
        className="hidden"
        onChange={onUpload}
      />
      {count !== null && (
        <p className="text-xs text-green-600">
          {count.toLocaleString()} {t('featuresLoaded')}
        </p>
      )}
    </div>
  )
}

function statusBadge(status: string, t: (k: string) => string) {
  if (status === 'Full')
    return <span className="inline-block px-1.5 rounded text-white text-[10px] bg-green-600">{t('full')}</span>
  if (status === 'Vacant')
    return <span className="inline-block px-1.5 rounded text-white text-[10px] bg-orange-500">{t('vacant')}</span>
  return <span className="inline-block px-1.5 rounded text-white text-[10px] bg-yellow-500">{t('partial')}</span>
}

function ResultsBlock({
  results, summary, idLabel, reportLabel,
}: {
  results: ContourResult[]
  summary: string
  idLabel: string
  reportLabel: string
}) {
  const { t, points } = useStore()
  const [error, setError] = useState<string | null>(null)

  async function report(format: string) {
    try {
      await generateReport(
        'Kadastr tahlili',
        points,
        results.map(({ geometry, ...rest }) => rest),
        summary,
        format,
        reportLabel,
      )
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <>
      <div className="overflow-auto panel-scroll max-h-64 border border-gray-200 dark:border-gray-700 rounded">
        <table className="w-full text-[11px]">
          <thead className="bg-gray-100 dark:bg-gray-700 sticky top-0">
            <tr>
              <th className="px-1.5 py-1 text-left">{idLabel}</th>
              <th className="px-1.5 py-1 text-left">{t('district')}</th>
              <th className="px-1.5 py-1 text-left">{t('massif')}</th>
              <th className="px-1.5 py-1 text-right">{t('coverage')}</th>
              <th className="px-1.5 py-1 text-center">{t('status')}</th>
            </tr>
          </thead>
          <tbody>
            {results.map((c, i) => (
              <tr key={i} className="border-t border-gray-100 dark:border-gray-700">
                <td className="px-1.5 py-1 font-mono font-semibold">{c.code}</td>
                <td className="px-1.5 py-1">{c.district ?? '-'}</td>
                <td className="px-1.5 py-1">{c.massif ?? '-'}</td>
                <td className="px-1.5 py-1 text-right font-mono">
                  {c.coverage_percent.toFixed(1)}%
                </td>
                <td className="px-1.5 py-1 text-center">{statusBadge(c.status, t)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded bg-blue-50 dark:bg-gray-800 p-2 text-xs text-gray-700 dark:text-gray-200">
        <b>{t('summary')}:</b> {summary}
      </div>

      <div>
        <h3 className="text-xs font-semibold mb-1 text-gray-700 dark:text-gray-200">
          {t('generateReport')}
        </h3>
        <div className="grid grid-cols-2 gap-1.5">
          {['xlsx', 'pdf', 'kmz', 'geojson'].map((f) => (
            <button
              key={f}
              onClick={() => report(f)}
              className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 hover:bg-brand hover:text-white"
            >
              {t('wordReport')} {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      {error && <p className="text-xs text-red-600 break-words">{error}</p>}
    </>
  )
}
