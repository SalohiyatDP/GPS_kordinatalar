// Shared definition of NGIS (open.ngis.uz) UZKAD cadastral layers (region DB16).
export interface NgisLayerDef {
  key: string // Uzbek display name
  service: string // ArcGIS FeatureServer service id
  color: string
  url: string
}

const NGIS_BASE = 'https://db.ngis.uz/db/rest/services/UZKAD'

export const NGIS_LAYERS: NgisLayerDef[] = [
  { key: 'Turar-joy yerlar', service: 'TURAR_UZKAD_DB16', color: '#eab308' },
  { key: 'Noturar yerlar', service: 'NOTURAR_UZKAD_DB16', color: '#f97316' },
  { key: 'Qishloq xoʻjaligi yerlar', service: 'AGR_ONLY_UZKAD_DB16', color: '#84cc16' },
  { key: 'Oʻrmon yerlar', service: 'FOREST_UZKAD_DB16', color: '#15803d' },
  { key: 'Suv yerlar', service: 'WATER_UZKAD_DB16', color: '#0ea5e9' },
  { key: 'Avtoyoʻl yerlar', service: 'AVTOYUL_UZKAD_DB16', color: '#78716c' },
  { key: 'Davlat zaxira yerlar', service: 'DZY_UZKAD_DB16', color: '#a855f7' },
  { key: 'Muhofaza yerlar', service: 'MUHOFAZA_UZKAD_DB16', color: '#14b8a6' },
  { key: 'Mahalla', service: 'MAHALLA_UZKAD_DB16', color: '#ec4899' },
].map((l) => ({ ...l, url: `${NGIS_BASE}/${l.service}/FeatureServer/0` }))
