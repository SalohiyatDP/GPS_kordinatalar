import { useEffect, useMemo } from 'react'
import {
  CircleMarker,
  GeoJSON,
  LayersControl,
  MapContainer,
  Polygon as LeafletPolygon,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
} from 'react-leaflet'
import L from 'leaflet'
import { useStore } from '../store'

const COLORS = {
  point: '#1d4ed8', // blue
  polygon: '#dc2626', // red
  full: '#16a34a', // green
  partial: '#eab308', // yellow
}

function FitBounds() {
  const map = useMap()
  const { points, layerGeoJSON } = useStore()
  useEffect(() => {
    const latlngs = points.map((p) => [p.latitude, p.longitude]) as [number, number][]
    if (latlngs.length > 0) {
      map.fitBounds(L.latLngBounds(latlngs).pad(0.3))
    } else if (layerGeoJSON) {
      try {
        const layer = L.geoJSON(layerGeoJSON)
        const b = layer.getBounds()
        if (b.isValid()) map.fitBounds(b.pad(0.1))
      } catch {
        /* ignore */
      }
    }
  }, [points, layerGeoJSON, map])
  return null
}

export default function MapView() {
  const { points, polygonGeoJSON, layerGeoJSON, contours, theme } = useStore()

  const polygonLatLngs = useMemo(
    () => points.map((p) => [p.latitude, p.longitude] as [number, number]),
    [points],
  )

  const tileUrl =
    theme === 'dark'
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

  return (
    <MapContainer
      center={[41.3111, 69.2797]}
      zoom={6}
      className="h-full w-full"
      scrollWheelZoom
    >
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="Base Map">
          <TileLayer
            url={tileUrl}
            attribution='&copy; OpenStreetMap contributors'
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Satellite">
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="&copy; Esri"
          />
        </LayersControl.BaseLayer>

        {/* Contour layer (uploaded) */}
        {layerGeoJSON && (
          <LayersControl.Overlay checked name="Contours">
            <GeoJSON
              data={layerGeoJSON}
              style={{ color: '#64748b', weight: 1, fillOpacity: 0.05 }}
            />
          </LayersControl.Overlay>
        )}

        {/* Intersection results */}
        {contours.length > 0 && (
          <LayersControl.Overlay checked name="Intersections">
            <GeoJSON
              key={JSON.stringify(contours.map((c) => c.code))}
              data={
                {
                  type: 'FeatureCollection',
                  features: contours
                    .filter((c) => c.geometry)
                    .map((c) => ({
                      type: 'Feature' as const,
                      geometry: c.geometry as GeoJSON.Geometry,
                      properties: { code: c.code, status: c.status },
                    })),
                } as GeoJSON.FeatureCollection
              }
              style={(f) => ({
                color: f?.properties?.status === 'Full' ? COLORS.full : COLORS.partial,
                weight: 2,
                fillColor:
                  f?.properties?.status === 'Full' ? COLORS.full : COLORS.partial,
                fillOpacity: 0.4,
              })}
              onEachFeature={(f, layer) => {
                layer.bindTooltip(String(f.properties?.code ?? ''), {
                  permanent: false,
                })
              }}
            />
          </LayersControl.Overlay>
        )}
      </LayersControl>

      {/* User polygon (red) */}
      {polygonLatLngs.length >= 3 && (
        <LeafletPolygon
          positions={polygonLatLngs}
          pathOptions={{ color: COLORS.polygon, weight: 3, fillOpacity: 0.1 }}
        />
      )}

      {/* Points (blue) */}
      {points.map((p) => (
        <CircleMarker
          key={p.point_number}
          center={[p.latitude, p.longitude]}
          radius={6}
          pathOptions={{
            color: '#fff',
            weight: 2,
            fillColor: COLORS.point,
            fillOpacity: 1,
          }}
        >
          <Tooltip permanent direction="top" offset={[0, -6]}>
            {p.point_number}
          </Tooltip>
          <Popup>
            <div className="text-xs">
              <b>#{p.point_number}</b>
              <br />
              {p.dms}
              <br />
              {p.latitude.toFixed(6)}, {p.longitude.toFixed(6)}
            </div>
          </Popup>
        </CircleMarker>
      ))}

      {/* polygonGeoJSON kept for downstream use; not separately rendered */}
      <span style={{ display: 'none' }}>{polygonGeoJSON ? '1' : '0'}</span>

      <FitBounds />
    </MapContainer>
  )
}
