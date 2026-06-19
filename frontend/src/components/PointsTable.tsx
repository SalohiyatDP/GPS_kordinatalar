import { useStore } from '../store'

export default function PointsTable() {
  const { t, points, invalid, duplicatesRemoved, movePoint, deletePoint } = useStore()

  if (points.length === 0 && invalid.length === 0) {
    return (
      <p className="text-xs text-gray-400 italic px-1">{t('noData')}</p>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-3 text-xs text-gray-600 dark:text-gray-300">
        <span>
          {t('pointsCount')}: <b>{points.length}</b>
        </span>
        <span>
          {t('duplicatesRemoved')}: <b>{duplicatesRemoved}</b>
        </span>
        {invalid.length > 0 && (
          <span className="text-red-600">
            {t('invalidCoords')}: <b>{invalid.length}</b>
          </span>
        )}
      </div>
      <div className="overflow-auto panel-scroll max-h-72 border border-gray-200 dark:border-gray-700 rounded">
        <table className="w-full text-xs">
          <thead className="bg-gray-100 dark:bg-gray-700 sticky top-0">
            <tr>
              <th className="px-2 py-1 text-left">{t('pointNumber')}</th>
              <th className="px-2 py-1 text-left">{t('latitude')}</th>
              <th className="px-2 py-1 text-left">{t('longitude')}</th>
              <th className="px-2 py-1 text-left">{t('dms')}</th>
              <th className="px-2 py-1 text-center">{t('actions')}</th>
            </tr>
          </thead>
          <tbody>
            {points.map((p, i) => (
              <tr
                key={i}
                className="border-t border-gray-100 dark:border-gray-700 hover:bg-blue-50 dark:hover:bg-gray-700/50"
              >
                <td className="px-2 py-1">{p.point_number}</td>
                <td className="px-2 py-1 font-mono">{p.latitude.toFixed(6)}</td>
                <td className="px-2 py-1 font-mono">{p.longitude.toFixed(6)}</td>
                <td className="px-2 py-1 font-mono text-[10px] whitespace-nowrap">
                  {p.dms}
                </td>
                <td className="px-2 py-1">
                  <div className="flex items-center justify-center gap-1">
                    <button
                      title={t('moveUp')}
                      onClick={() => movePoint(i, -1)}
                      className="px-1 hover:text-brand"
                    >
                      ▲
                    </button>
                    <button
                      title={t('moveDown')}
                      onClick={() => movePoint(i, 1)}
                      className="px-1 hover:text-brand"
                    >
                      ▼
                    </button>
                    <button
                      title={t('delete')}
                      onClick={() => deletePoint(i)}
                      className="px-1 text-red-500 hover:text-red-700"
                    >
                      ✕
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
