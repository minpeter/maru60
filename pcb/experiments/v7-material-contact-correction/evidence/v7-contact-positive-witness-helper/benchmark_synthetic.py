"""Synthetic scale smoke test only. No board load/export or native Booleans."""
import json
import math
import time
from positive_witness import prepare_rings, require_positive_witness


def polygon(n, r, x=0, y=0):
    return tuple((x+round(r*math.cos(2*math.pi*i/n)),
                  y+round(r*math.sin(2*math.pi*i/n))) for i in range(n))


t = time.monotonic()
zone = prepare_rings(polygon(57000, 10000000))
zone_prepare_seconds = time.monotonic()-t
# Hundreds of vertices in each prepared small component; cache reused.
t = time.monotonic()
pairs = [(prepare_rings(polygon(256, 10000, x=i*50000)),
          prepare_rings(polygon(256, 10000, x=i*50000+5000))) for i in range(32)]
small_prepare_seconds = time.monotonic()-t
t = time.monotonic()
for i in range(22000):
    require_positive_witness(*pairs[i % len(pairs)])
small_contact_seconds = time.monotonic()-t
t = time.monotonic()
for i in range(731):
    require_positive_witness(pairs[i % len(pairs)][0], zone)
zone_contact_seconds = time.monotonic()-t
print(json.dumps(dict(synthetic_only=True, native_board_loaded=False,
                     zone_vertices=57000, vertices_per_small_component=256,
                     cached_small_components=64,
                     zone_prepare_seconds=zone_prepare_seconds,
                     small_prepare_seconds=small_prepare_seconds,
                     small_contacts=22000, small_contact_seconds=small_contact_seconds,
                     zone_contacts=731, zone_contact_seconds=zone_contact_seconds), indent=2))
