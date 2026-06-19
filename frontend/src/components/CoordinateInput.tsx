import { useRef, useState } from 'react'
import { useStore } from '../store'
import { normalizeText, uploadCoordinateFile, getErrorMessage } from '../api/client'

export default function CoordinateInput() {
  const { t, setNormalizeResult } = useStore()
  const [text, setText] = useState('')
  const [resolveUrls, setResolveUrls] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleNormalize() {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await normalizeText(text, resolveUrls)
      setNormalizeResult(res.coordinates, res.invalid, res.duplicates_removed)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await uploadCoordinateFile(file)
      setNormalizeResult(res.coordinates, res.invalid, res.duplicates_removed)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div className="space-y-2">
      <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200">
        {t('coordinateInput')}
      </h2>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t('inputPlaceholder')}
        rows={6}
        className="w-full text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 dark:text-gray-100 p-2 font-mono resize-y outline-none focus:ring-2 focus:ring-brand"
      />
      <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
        <input
          type="checkbox"
          checked={resolveUrls}
          onChange={(e) => setResolveUrls(e.target.checked)}
        />
        {t('resolveUrls')}
      </label>
      <div className="flex flex-col gap-2">
        <button
          onClick={handleNormalize}
          disabled={loading}
          className="bg-brand hover:bg-brand-light text-white text-sm rounded px-3 py-2 disabled:opacity-50"
        >
          {loading ? t('loading') : t('normalize')}
        </button>
        <button
          onClick={() => fileRef.current?.click()}
          disabled={loading}
          className="border border-brand text-brand dark:text-brand-light text-sm rounded px-3 py-2 hover:bg-brand/10"
        >
          {t('uploadFile')}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.csv,.xlsx,.xls"
          className="hidden"
          onChange={handleFile}
        />
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}
