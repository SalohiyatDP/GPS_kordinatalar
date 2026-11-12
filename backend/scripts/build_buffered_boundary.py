"""Build the 3 km buffered Uzbekistan boundary used by backend and frontend.

Usage: python build_buffered_boundary.py <source.geojson> <output.geojson>
"""
import json, sys
from shapely.geometry import shape
from pyproj import Transformer, CRS

BUFFER_M = 3000.0  # 3 km
SRC, DST = sys.argv[1], sys.argv[2]

src = json.load(open(SRC, encoding="utf-8"))
geom = shape(src["geometry"]).buffer(0)
c = geom.centroid
aeqd = CRS.from_proj4(f"+proj=aeqd +lat_0={c.y} +lon_0={c.x} +datum=WGS84 +units=m +no_defs")
to_m = Transformer.from_crs("EPSG:4326", aeqd, always_xy=True).transform
to_ll = Transformer.from_crs(aeqd, "EPSG:4326", always_xy=True).transform
g_m = tr(to_m, geom)
buf_m = g_m.buffer(BUFFER_M, quad_segs=16)
buf = tr(to_ll, buf_m).buffer(0)
assert buf.geom_type == "Polygon", buf.geom_type
print("area src km2 (aeqd):", round(g_m.area/1e6,1), "buffered:", round(buf_m.area/1e6,1))
print("ring pts:", len(buf.exterior.coords), "holes:", len(buf.interiors))
buf = buf.simplify(0.0005, preserve_topology=True)  # ~50 m tolerance
def rnd(coords):
    return [[round(x, 6), round(y, 6)] for x, y in coords]
out = {
    "type": "Feature",
    "properties": {"name": "Uzbekistan", "buffer_m": BUFFER_M},
    "geometry": {"type": "Polygon",
                 "coordinates": [rnd(buf.exterior.coords)] +
                                [rnd(r.coords) for r in buf.interiors]},
}
with open(DST, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
print("wrote", DST)
