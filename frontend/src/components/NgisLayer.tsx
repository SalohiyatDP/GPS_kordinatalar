import {
  createLayerComponent,
  type LayerProps,
  type LeafletContextInterface,
} from '@react-leaflet/core'
import { featureLayer, type FeatureLayer } from 'esri-leaflet'

export interface NgisLayerProps extends LayerProps {
  url: string
  color?: string
  minZoom?: number
}

/**
 * Renders an NGIS (open.ngis.uz) ArcGIS FeatureServer cadastral layer as a
 * Leaflet vector layer. esri-leaflet queries only the current viewport, so it
 * stays fast even on very large datasets.
 *
 * Note: requires the browser to be able to reach db.ngis.uz (works from within
 * Uzbekistan). The service must allow cross-origin requests (CORS).
 */
export const NgisFeatureLayer = createLayerComponent<FeatureLayer, NgisLayerProps>(
  function createInstance(
    { url, color = '#ff7800', minZoom = 14 },
    context: LeafletContextInterface,
  ) {
    const instance = featureLayer({
      url,
      simplifyFactor: 0.4,
      precision: 6,
      minZoom,
      style: () => ({ color, weight: 1, fillColor: color, fillOpacity: 0.06 }),
    })
    instance.bindPopup((layer: unknown) => {
      const props =
        (layer as { feature?: { properties?: Record<string, unknown> } })?.feature
          ?.properties ?? {}
      const cad = props.cadastral_number ?? '-'
      const kind = props.property_kind ?? '-'
      return `<b>Kadastr raqami:</b> ${cad}<br/><b>Turi:</b> ${kind}`
    })
    return {
      instance,
      context: { ...context, overlayContainer: instance },
    }
  },
)
