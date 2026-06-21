import { useEffect, useMemo } from 'react'
import {
  GeoJSON,
  LayersControl,
  MapContainer,
  Marker,
  Polygon as LeafletPolygon,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
  useMapEvents,
} from 'react-leaflet'
import L from 'leaflet'
import { useStore } from '../store'
import { NgisFeatureLayer } from './NgisLayer'
import { NGIS_LAYERS } from '../data/ngisLayers'

const COLORS = {
  point: '#1d4ed8', // blue
  polygon: '#dc2626', // red
  full: '#16a34a', // green
  partial: '#eab308', // yellow
  vacant: '#f97316', // orange
}

function numberIcon(n: number) {
  return L.divIcon({
    className: '',
    html:
      `<div style="background:${COLORS.point};color:#fff;border:2px solid #fff;` +
      `border-radius:50%;width:22px;height:22px;display:flex;align-items:center;` +
      `justify-content:center;font-size:11px;font-weight:700;` +
      `box-shadow:0 0 3px rgba(0,0,0,.5)">${n}</div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  })
}

function FitBounds() {
  const map = useMap()
  const { points, layerGeoJSON, mapPickMode } = useStore()
  useEffect(() => {
    if (mapPickMode) return // don't auto-recenter while picking points manually
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
  }, [points, layerGeoJSON, map, mapPickMode])
  return null
}

function MapClickHandler({
  active,
  onPick,
}: {
  active: boolean
  onPick: (lat: number, lon: number) => void
}) {
  useMapEvents({
    click(e) {
      if (active) onPick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

export default function MapView() {
  const { points, polygonGeoJSON, layerGeoJSON, contours, theme,
    uzkadGeoJSON, uzkadResults, t, mapPickMode, addPointLatLng,
    updatePointLatLng, notice, setNotice, ngisResults } = useStore()

  const polygonLatLngs = useMemo(
    () => points.map((p) => [p.latitude, p.longitude] as [number, number]),
    [points],
  )

  const tileUrl =
    theme === 'dark'
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

  useEffect(() => {
    if (!notice) return
    const id = setTimeout(() => setNotice(null), 4500)
    return () => clearTimeout(id)
  }, [notice, setNotice])

  return (
    <>
      {notice && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1200] bg-orange-500 text-white text-xs sm:text-sm px-3 py-2 rounded shadow-lg max-w-[90%] text-center">
          ⚠️ {notice}
        </div>
      )}
      <MapContainer
        center={[41.3111, 69.2797]}
        zoom={6}
        className={'h-full w-full' + (mapPickMode ? ' cursor-crosshair' : '')}
        scrollWheelZoom
      >
        <MapClickHandler active={mapPickMode} onPick={addPointLatLng} />
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name={t('layerBaseMap')}>
          <TileLayer
            url={tileUrl}
            attribution='&copy; OpenStreetMap contributors'
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name={t('layerSatellite')}>
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="&copy; Esri"
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name={t('layerGoogleStreets')}>
          <TileLayer
            url="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
            subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
            attribution="&copy; Google"
            maxZoom={21}
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name={t('layerGoogleSatellite')}>
          <TileLayer
            url="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
            subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
            attribution="&copy; Google"
            maxZoom={21}
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name={t('layerGoogleHybrid')}>
          <TileLayer
            url="https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
            subdomains={['mt0', 'mt1', 'mt2', 'mt3']}
            attribution="&copy; Google"
            maxZoom={21}
          />
        </LayersControl.BaseLayer>

        {/* NGIS (open.ngis.uz) UZKAD cadastral layers */}
        {NGIS_LAYERS.map((lyr) => (
          <LayersControl.Overlay key={lyr.key} name={`NGIS: ${lyr.key}`}>
            <NgisFeatureLayer url={lyr.url} color={lyr.color} />
          </LayersControl.Overlay>
        ))}

        {/* Contour layer (uploaded) */}
        {layerGeoJSON && (
          <LayersControl.Overlay checked name={t('overlayContours')}>
            <GeoJSON
              data={layerGeoJSON}
              style={{ color: '#64748b', weight: 1, fillOpacity: 0.05 }}
            />
          </LayersControl.Overlay>
        )}

        {/* Intersection results */}
        {contours.length > 0 && (
          <LayersControl.Overlay checked name={t('overlayIntersections')}>
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

        {/* UZKAD base layer */}
        {uzkadGeoJSON && (
          <LayersControl.Overlay checked name={t('overlayUzkad')}>
            <GeoJSON
              data={uzkadGeoJSON}
              style={{ color: '#7c3aed', weight: 1, fillOpacity: 0.04,
                dashArray: '3' }}
            />
          </LayersControl.Overlay>
        )}

        {/* UZKAD analysis (cadastral parcels + vacant) */}
        {uzkadResults.length > 0 && (
          <LayersControl.Overlay checked name={t('overlayUzkadResult')}>
            <GeoJSON
              key={JSON.stringify(uzkadResults.map((c) => c.code))}
              data={
                {
                  type: 'FeatureCollection',
                  features: uzkadResults
                    .filter((c) => c.geometry)
                    .map((c) => ({
                      type: 'Feature' as const,
                      geometry: c.geometry as GeoJSON.Geometry,
                      properties: { code: c.code, status: c.status },
                    })),
                } as GeoJSON.FeatureCollection
              }
              style={(f) => {
                const st = f?.properties?.status
                const color =
                  st === 'Full' ? COLORS.full
                    : st === 'Vacant' ? COLORS.vacant
                      : COLORS.partial
                return { color, weight: 2, fillColor: color, fillOpacity: 0.45 }
              }}
              onEachFeature={(f, layer) => {
                layer.bindTooltip(String(f.properties?.code ?? ''), {
                  permanent: false,
                })
              }}
            />
          </LayersControl.Overlay>
        )}

        {/* NGIS live analysis results */}
        {ngisResults.length > 0 && (
          <LayersControl.Overlay checked name="NGIS natija">
            <GeoJSON
              key={JSON.stringify(ngisResults.map((c) => c.code + c.status))}
              data={
                {
                  type: 'FeatureCollection',
                  features: ngisResults
                    .filter((c) => c.geometry)
                    .map((c) => ({
                      type: 'Feature' as const,
                      geometry: c.geometry as GeoJSON.Geometry,
                      properties: { code: c.code, status: c.status },
                    })),
                } as GeoJSON.FeatureCollection
              }
              style={(f) => {
                const st = f?.properties?.status
                const color =
                  st === 'Full' ? COLORS.full
                    : st === 'Vacant' ? COLORS.vacant
                      : COLORS.partial
                return { color, weight: 2, fillColor: color, fillOpacity: 0.45 }
              }}
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

      {/* Points (blue, draggable) */}
      {points.map((p, idx) => (
        <Marker
          key={idx}
          position={[p.latitude, p.longitude]}
          icon={numberIcon(p.point_number)}
          draggable
          eventHandlers={{
            dragend: (e) => {
              const m = e.target as L.Marker
              const ll = m.getLatLng()
              const ok = updatePointLatLng(idx, ll.lat, ll.lng)
              if (!ok) {
                // Outside Uzbekistan -> revert to the original position.
                m.setLatLng([p.latitude, p.longitude])
              }
            },
          }}
        >
          <Tooltip direction="top" offset={[0, -10]}>
            #{p.point_number}
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
        </Marker>
      ))}

      {/* polygonGeoJSON kept for downstream use; not separately rendered */}
      <span style={{ display: 'none' }}>{polygonGeoJSON ? '1' : '0'}</span>

      <FitBounds />
    </MapContainer>
    </>
  )
}
