import { useState } from 'react'
import { useStore } from '../store'
import { computeGeometry, downloadExport, getErrorMessage } from '../api/client'

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs py-0.5">
      <span className="text-gray-500 dark:text-gray-400">{label}</span>
      <span className="font-mono font-semibold">{value}</span>
    </div>
  )
}

export default function ResultsPanel() {
  const { t, points, area, perimeter, setGeometry } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const pointInputs = points.map((p) => ({
    latitude: p.latitude,
    longitude: p.longitude,
  }))

  async function build() {
    if (points.length < 3) {
      setError('Need at least 3 points')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await computeGeometry(pointInputs)
      setGeometry(res.area, res.perimeter, res.polygon_geojson, res.centroid)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  async function doExport(
    format: string,
    kind: 'points' | 'polygon',
    epsg?: number,
  ) {
    try {
      await downloadExport(pointInputs, format, kind, epsg)
    } catch (e) {
      setError(getErrorMessage(e))
    }
  }

  return (
    <div className="space-y-3">
      <button
        onClick={build}
        disabled={loading || points.length < 3}
        className="w-full bg-brand hover:bg-brand-light text-white text-sm rounded px-3 py-2 disabled:opacity-50"
      >
        {loading ? t('loading') : t('buildPolygon')}
      </button>
      {error && <p className="text-xs text-red-600">{error}</p>}

      {area && perimeter && (
        <div className="rounded border border-gray-200 dark:border-gray-700 p-2">
          <h3 className="text-xs font-semibold mb-1 text-gray-700 dark:text-gray-200">
            {t('area')}
          </h3>
          <Metric label={t('squareMeters')} value={area.square_meters.toLocaleString()} />
          <Metric label={t('hectares')} value={area.hectares.toFixed(4)} />
          <Metric label={t('squareKm')} value={area.square_kilometers.toFixed(6)} />
          <Metric label={t('sotix')} value={area.sotix.toFixed(2)} />
          <h3 className="text-xs font-semibold mt-2 mb-1 text-gray-700 dark:text-gray-200">
            {t('perimeter')}
          </h3>
          <Metric label={t('meters')} value={perimeter.meters.toLocaleString()} />
          <Metric label={t('kilometers')} value={perimeter.kilometers.toFixed(4)} />
        </div>
      )}

      <div>
        <h3 className="text-xs font-semibold mb-1 text-gray-700 dark:text-gray-200">
          {t('exports')}
        </h3>
        <div className="grid grid-cols-2 gap-1.5">
          <ExportBtn label={`${t('wordPoints')} XLSX`} onClick={() => doExport('xlsx', 'points')} />
          <ExportBtn label={`${t('wordPoints')} KMZ`} onClick={() => doExport('kmz', 'points')} />
          <ExportBtn label={`${t('wordPolygon')} KMZ`} onClick={() => doExport('kmz', 'polygon')} />
          <ExportBtn label="GeoJSON" onClick={() => doExport('geojson', 'polygon')} />
          <ExportBtn label="PDF" onClick={() => doExport('pdf', 'polygon')} />
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold mb-1 text-gray-700 dark:text-gray-200">
          {t('shapefiles')}
        </h3>
        <div className="grid grid-cols-1 gap-1.5">
          <ExportBtn
            label={t('shapePulkovo')}
            disabled={points.length < 3}
            onClick={() => doExport('shp', 'polygon', 28472)}
          />
          <ExportBtn
            label={t('shapeWebMercator')}
            disabled={points.length < 3}
            onClick={() => doExport('shp', 'polygon', 3857)}
          />
        </div>
      </div>
    </div>
  )
}

function ExportBtn({
  label,
  onClick,
  disabled = false,
}: {
  label: string
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 hover:bg-brand hover:text-white transition-colors disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-inherit"
    >
      {label}
    </button>
  )
}
