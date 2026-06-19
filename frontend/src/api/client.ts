import axios from 'axios'
import type {
  GeometryResponse,
  LayerUploadResponse,
  NormalizeResponse,
  Point,
  PolygonAnalysis,
} from '../types'

const api = axios.create({ baseURL: '/api' })

export interface PointInput {
  latitude: number
  longitude: number
}

export async function normalizeText(
  text: string,
  resolveUrls: boolean,
): Promise<NormalizeResponse> {
  const { data } = await api.post('/coordinates/normalize', {
    text,
    resolve_urls: resolveUrls,
  })
  return data
}

export async function uploadCoordinateFile(file: File): Promise<NormalizeResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/coordinates/upload', form)
  return data
}

export async function computeGeometry(points: PointInput[]): Promise<GeometryResponse> {
  const { data } = await api.post('/geometry/compute', { points })
  return data
}

export function exportUrl() {
  return '/api/geometry/export'
}

export async function downloadExport(
  points: PointInput[],
  format: string,
  kind: 'points' | 'polygon',
): Promise<void> {
  const resp = await api.post(
    '/geometry/export',
    { points, format, kind },
    { responseType: 'blob' },
  )
  triggerDownload(resp.data, resp.headers['content-disposition'])
}

export async function uploadContours(file: File): Promise<LayerUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/cadastre/upload', form)
  return data
}

export async function analyzePolygon(
  layerId: string,
  points: PointInput[],
): Promise<PolygonAnalysis> {
  const { data } = await api.post('/cadastre/analyze-polygon', {
    layer_id: layerId,
    points,
    include_geometry: true,
  })
  return data
}

export async function analyzePoints(layerId: string, points: PointInput[]) {
  const { data } = await api.post('/cadastre/analyze-points', {
    layer_id: layerId,
    points,
    include_geometry: false,
  })
  return data.points
}

export async function getLayerGeoJSON(
  layerId: string,
  simplify = 0.0001,
): Promise<GeoJSON.FeatureCollection> {
  const { data } = await api.get(`/cadastre/layer/${layerId}/geojson`, {
    params: { simplify },
  })
  return data
}

export async function generateReport(
  name: string,
  points: Point[],
  contours: unknown[],
  summary: string,
  format: string,
  mapImageBase64?: string,
): Promise<void> {
  const resp = await api.post(
    '/reports/generate',
    {
      name,
      points: points.map((p) => ({ latitude: p.latitude, longitude: p.longitude })),
      contours,
      summary,
      format,
      map_image_base64: mapImageBase64,
    },
    { responseType: 'blob' },
  )
  triggerDownload(resp.data, resp.headers['content-disposition'])
}

function triggerDownload(blob: Blob, contentDisposition?: string) {
  let filename = 'download'
  if (contentDisposition) {
    const match = /filename="?([^"]+)"?/.exec(contentDisposition)
    if (match) filename = match[1]
  }
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
