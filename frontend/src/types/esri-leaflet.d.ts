declare module 'esri-leaflet' {
  import { Layer, PathOptions } from 'leaflet'

  export class FeatureLayer extends Layer {
    bindPopup(fn: (layer: unknown) => string): this
    setWhere(where: string): this
  }

  export interface FeatureLayerOptions {
    url: string
    simplifyFactor?: number
    precision?: number
    minZoom?: number
    maxZoom?: number
    where?: string
    fields?: string[]
    style?: (feature?: unknown) => PathOptions
    [key: string]: unknown
  }

  export function featureLayer(options: FeatureLayerOptions): FeatureLayer
}
