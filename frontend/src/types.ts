export interface Point {
  point_number: number
  latitude: number
  longitude: number
  dms: string
  status: string
  error?: string | null
}

export interface NormalizeResponse {
  coordinates: Point[]
  invalid: Point[]
  duplicates_removed: number
  count: number
}

export interface AreaResult {
  square_meters: number
  hectares: number
  square_kilometers: number
  sotix: number
}

export interface PerimeterResult {
  meters: number
  kilometers: number
}

export interface GeometryResponse {
  area: AreaResult
  perimeter: PerimeterResult
  polygon_geojson: GeoJSON.Polygon
  centroid: [number, number]
}

export interface ContourResult {
  contour: string | number | null
  code: string
  region: string | null
  district: string | null
  massif: string | null
  land_type: string | null
  contour_area: number
  intersection_area: number
  coverage_percent: number
  status: 'Full' | 'Partial'
  geometry?: GeoJSON.Geometry
}

export interface PolygonAnalysis {
  contours: ContourResult[]
  summary: string
  summary_codes: string[]
}

export interface LayerUploadResponse {
  layer_id: string
  feature_count: number
  original_crs: string | null
  columns: Record<string, string | null>
  bounds: [number, number, number, number]
}
