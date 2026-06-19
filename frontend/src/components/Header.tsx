import { useStore } from '../store'
import { LANGUAGES } from '../i18n/translations'
import type { Lang } from '../i18n/translations'

export default function Header() {
  const { t, lang, setLang, theme, toggleTheme } = useStore()
  return (
    <header className="flex items-center justify-between bg-brand dark:bg-brand-dark text-white px-4 py-2 shadow-md z-[1000]">
      <div className="flex items-center gap-2">
        <span className="text-xl">🗺️</span>
        <h1 className="text-sm sm:text-base font-semibold tracking-tight">
          {t('appTitle')}
        </h1>
      </div>
      <div className="flex items-center gap-3">
        <select
          aria-label={t('language')}
          value={lang}
          onChange={(e) => setLang(e.target.value as Lang)}
          className="bg-brand-light/30 text-white text-sm rounded px-2 py-1 outline-none border border-white/20"
        >
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code} className="text-black">
              {l.label}
            </option>
          ))}
        </select>
        <button
          onClick={toggleTheme}
          title={t('theme')}
          className="rounded px-2 py-1 bg-brand-light/30 hover:bg-brand-light/50 border border-white/20"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  )
}
