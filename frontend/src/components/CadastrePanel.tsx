import { useRef, useState } from 'react'
import { useStore } from '../store'
import {
  analyzePolygon,
  generateReport,
  getLayerGeoJSON,
  uploadContours,
  getErrorMessage,
} from '../api/client'

export default function CadastrePanel() {
  const {
    t,
    points,
    layerId,
    contours,
    summary,
    setLayer,
    setAnalysis,
  } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [featureCount, setFeatureCount] = useState<number | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await uploadContours(file)
      setFeatureCount(res.feature_count)
      // Load a simplified version for display (avoid huge payloads).
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

  async function report(format: string) {
    try {
      await generateReport(
        'Cadastre Analysis',
        points,
        contours.map(({ geometry, ...rest }) => rest),
        summary,
        format,
      )
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="space-y-3">
      <button
        onClick={() => fileRef.current?.click()}
        disabled={loading}
        className="w-full border border-brand text-brand dark:text-brand-light text-sm rounded px-3 py-2 hover:bg-brand/10 disabled:opacity-50"
      >
        {t('uploadContour')}
      </button>
      <input
        ref={fileRef}
        type="file"
        accept=".zip"
        className="hidden"
        onChange={handleUpload}
      />
      {featureCount !== null && (
        <p className="text-xs text-green-600">
          {featureCount.toLocaleString()} {t('featuresLoaded')}
        </p>
      )}

      <button
        onClick={analyze}
        disabled={loading || !layerId || points.length < 3}
        className="w-full bg-brand hover:bg-brand-light text-white text-sm rounded px-3 py-2 disabled:opacity-50"
      >
        {loading ? t('loading') : t('analyzePolygon')}
      </button>
      {error && <p className="text-xs text-red-600 break-words">{error}</p>}

      {contours.length > 0 && (
        <>
          <div className="overflow-auto panel-scroll max-h-64 border border-gray-200 dark:border-gray-700 rounded">
            <table className="w-full text-[11px]">
              <thead className="bg-gray-100 dark:bg-gray-700 sticky top-0">
                <tr>
                  <th className="px-1.5 py-1 text-left">{t('contour')}</th>
                  <th className="px-1.5 py-1 text-left">{t('district')}</th>
                  <th className="px-1.5 py-1 text-left">{t('massif')}</th>
                  <th className="px-1.5 py-1 text-left">{t('mfy')}</th>
                  <th className="px-1.5 py-1 text-right">{t('coverage')}</th>
                  <th className="px-1.5 py-1 text-center">{t('status')}</th>
                </tr>
              </thead>
              <tbody>
                {contours.map((c, i) => (
                  <tr
                    key={i}
                    className="border-t border-gray-100 dark:border-gray-700"
                  >
                    <td className="px-1.5 py-1 font-mono font-semibold">{c.code}</td>
                    <td className="px-1.5 py-1">{c.district ?? '-'}</td>
                    <td className="px-1.5 py-1">{c.massif ?? '-'}</td>
                    <td className="px-1.5 py-1">{c.mfy ?? '-'}</td>
                    <td className="px-1.5 py-1 text-right font-mono">
                      {c.coverage_percent.toFixed(1)}%
                    </td>
                    <td className="px-1.5 py-1 text-center">
                      <span
                        className={
                          'inline-block px-1.5 rounded text-white text-[10px] ' +
                          (c.status === 'Full' ? 'bg-green-600' : 'bg-yellow-500')
                        }
                      >
                        {c.status === 'Full' ? t('full') : t('partial')}
                      </span>
                    </td>
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
              <button
                onClick={() => report('xlsx')}
                className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 hover:bg-brand hover:text-white"
              >
                Analysis.xlsx
              </button>
              <button
                onClick={() => report('pdf')}
                className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 hover:bg-brand hover:text-white"
              >
                Analysis.pdf
              </button>
              <button
                onClick={() => report('kmz')}
                className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 hover:bg-brand hover:text-white"
              >
                Analysis.kmz
              </button>
              <button
                onClick={() => report('geojson')}
                className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 hover:bg-brand hover:text-white"
              >
                Analysis.geojson
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
