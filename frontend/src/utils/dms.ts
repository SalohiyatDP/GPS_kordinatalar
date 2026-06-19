/** Format a decimal degree value into the project's standard DMS string,
 *  mirroring the backend: 41°07'54.29"N  (minutes 2 digits, seconds 2 decimals). */
export function decimalToDms(value: number, isLat: boolean): string {
  const hemi = isLat ? (value >= 0 ? 'N' : 'S') : value >= 0 ? 'E' : 'W'
  let v = Math.abs(value)
  let deg = Math.floor(v)
  const minFull = (v - deg) * 60
  let min = Math.floor(minFull)
  let sec = Math.round((minFull - min) * 60 * 100) / 100
  if (sec >= 60) {
    sec -= 60
    min += 1
  }
  if (min >= 60) {
    min -= 60
    deg += 1
  }
  const mm = String(min).padStart(2, '0')
  const ss = sec.toFixed(2).padStart(5, '0')
  return `${deg}°${mm}'${ss}"${hemi}`
}

export function pairDms(lat: number, lon: number): string {
  return `${decimalToDms(lat, true)} ${decimalToDms(lon, false)}`
}
