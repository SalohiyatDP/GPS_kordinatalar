// Point-in-Uzbekistan check using a bundled, simplified national boundary.
import uz from '../assets/uzbekistan.json'

type Ring = number[][] // [[lon, lat], ...]

function pointInRing(lon: number, lat: number, ring: Ring): boolean {
  // Ray casting algorithm.
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0]
    const yi = ring[i][1]
    const xj = ring[j][0]
    const yj = ring[j][1]
    const intersect =
      yi > lat !== yj > lat &&
      lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi
    if (intersect) inside = !inside
  }
  return inside
}

function pointInPolygon(lon: number, lat: number, polygon: Ring[]): boolean {
  if (polygon.length === 0) return false
  // First ring is the outer boundary; the rest are holes.
  if (!pointInRing(lon, lat, polygon[0])) return false
  for (let k = 1; k < polygon.length; k++) {
    if (pointInRing(lon, lat, polygon[k])) return false
  }
  return true
}

export function isInUzbekistan(lat: number, lon: number): boolean {
  const geom = (uz as { geometry: { type: string; coordinates: unknown } }).geometry
  if (!geom) return true
  if (geom.type === 'Polygon') {
    return pointInPolygon(lon, lat, geom.coordinates as Ring[])
  }
  if (geom.type === 'MultiPolygon') {
    return (geom.coordinates as Ring[][]).some((poly) =>
      pointInPolygon(lon, lat, poly),
    )
  }
  return true
}
