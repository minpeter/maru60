"""Exact positive-interior certificates for integer-nm polygon components.

Native Boolean results are optional *candidate generators*, never evidence.
No pcbnew dependency: prepare_polyset uses its read-only public duck-typed API.
Input contract: straight, simple closed outline with its physical holes. No
self-intersection repair or polygon Boolean operation is performed here.
Search is deliberately bounded and incomplete. NO_WITNESS is not disjointness.
"""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import gcd
import json

MIN_CLEARANCE_NM = 2


def _int(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Polygon coordinates and guard must be integers in nm")
    return value


def _guard(value):
    value = _int(value)
    if value < MIN_CLEARANCE_NM:
        raise ValueError("The positive-interior guard cannot be less than 2 nm")
    return value


def _ring(values):
    out = []
    for x, y in values:
        p = (_int(x), _int(y))
        if not out or p != out[-1]:
            out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    if len(out) < 3:
        raise ValueError("A ring needs three distinct nonconsecutive vertices")
    if sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(out, out[1:]+out[:1])) == 0:
        raise ValueError("Zero signed-area ring is not a material boundary")
    return tuple(out)


@dataclass(frozen=True, slots=True)
class ExactPoint:
    """Point (x_num/den, y_num/den) in nm; no float conversion allowed."""
    x_num: int
    y_num: int
    den: int = 1

    def __post_init__(self):
        for v in (self.x_num, self.y_num, self.den):
            _int(v)
        if self.den <= 0:
            raise ValueError("Point denominator must be positive")
        common = gcd(gcd(abs(self.x_num), abs(self.y_num)), self.den)
        object.__setattr__(self, 'x_num', self.x_num//common)
        object.__setattr__(self, 'y_num', self.y_num//common)
        object.__setattr__(self, 'den', self.den//common)

    @classmethod
    def of(cls, point):
        if isinstance(point, cls):
            return point
        x, y = point
        if type(x) not in (int, Fraction) or type(y) not in (int, Fraction):
            raise TypeError("Witness coordinates must be int or Fraction, not float")
        x, y = Fraction(x), Fraction(y)
        den = x.denominator*y.denominator//gcd(x.denominator, y.denominator)
        return cls(x.numerator*(den//x.denominator), y.numerator*(den//y.denominator), den)

    def to_dict(self):
        return {'x_num': self.x_num, 'y_num': self.y_num, 'den': self.den, 'unit': 'nm'}


@dataclass(frozen=True, slots=True)
class _Node:
    box: tuple
    edges: tuple = ()
    children: tuple = ()


def _tree(edges):
    box = (min(e[5] for e in edges), min(e[6] for e in edges),
           max(e[7] for e in edges), max(e[8] for e in edges))
    if len(edges) <= 16:
        return _Node(box, tuple(edges))
    axis = 0 if box[2]-box[0] >= box[3]-box[1] else 1
    edges = sorted(edges, key=lambda e: e[5+axis]+e[7+axis])
    mid = len(edges)//2
    return _Node(box, children=(_tree(edges[:mid]), _tree(edges[mid:])))


def _query(node, predicate):
    if not predicate(node.box):
        return
    if node.edges:
        for e in node.edges:
            if predicate(e[5:9]):
                yield e
    else:
        for child in node.children:
            yield from _query(child, predicate)


@dataclass(frozen=True, slots=True)
class PreparedComponent:
    rings: tuple
    bounds: tuple
    tree: _Node
    digest: str
    seeds: tuple
    sampled_y: tuple

    def contains_with_clearance(self, point, clearance_nm=2):
        """Exact strict PIP AND distance >= guard from every boundary segment."""
        p, r = ExactPoint.of(point), _guard(clearance_nm)
        x, y, d = p.x_num, p.y_num, p.den
        lo_x, lo_y, hi_x, hi_y = self.bounds
        if not ((lo_x+r)*d <= x <= (hi_x-r)*d and
                (lo_y+r)*d <= y <= (hi_y-r)*d):
            return False
        # Half-open horizontal-ray parity, independently for outer and holes.
        # A BVH prunes segments whose y range or rightmost x cannot cross.
        inside = set()
        for ax, ay, bx, by, ring_id, *_ in _query(
                self.tree, lambda b: b[1]*d <= y <= b[3]*d and b[2]*d > x):
            if (ay*d > y) == (by*d > y):
                continue
            cross = (bx-ax)*(y-ay*d)-(by-ay)*(x-ax*d)
            if (by > ay and cross > 0) or (by < ay and cross < 0):
                if ring_id in inside:
                    inside.remove(ring_id)
                else:
                    inside.add(ring_id)
        if inside != {0}:
            return False
        # Only segment boxes intersecting the guard square can be too close.
        rd = r*d
        threshold = rd*rd
        for ax, ay, bx, by, _, *_ in _query(
                self.tree, lambda b: b[0]*d <= x+rd and b[2]*d >= x-rd
                and b[1]*d <= y+rd and b[3]*d >= y-rd):
            vx, vy, dx, dy = x-ax*d, y-ay*d, bx-ax, by-ay
            length2 = dx*dx+dy*dy
            dot = vx*dx+vy*dy
            if dot <= 0:
                if vx*vx+vy*vy < threshold:
                    return False
            elif dot >= length2*d:
                vx, vy = x-bx*d, y-by*d
                if vx*vx+vy*vy < threshold:
                    return False
            elif (dx*vy-dy*vx)**2 < threshold*length2:
                return False
        return True

    def _scanline(self, y):
        """Exact material x intervals; only used as bounded fallback seeds."""
        y = Fraction(y)
        events = {}
        for ax, ay, bx, by, rid, *_ in _query(
                self.tree, lambda b: b[1]*y.denominator <= y.numerator < b[3]*y.denominator):
            if (ay > y) == (by > y):
                continue
            x = Fraction(ax)+(y-ay)*Fraction(bx-ax, by-ay)
            events.setdefault(x, []).append(rid)
        active, begin, intervals = set(), None, []
        for x in sorted(events):
            before = active == {0}
            for rid in events[x]:
                if rid in active:
                    active.remove(rid)
                else:
                    active.add(rid)
            after = active == {0}
            if after and not before:
                begin = x
            elif before and not after:
                intervals.append((begin, x))
        return intervals


def prepare_rings(outer, holes=()):
    """Prepare and cache once per immutable physical component."""
    rings = (_ring(outer),)+tuple(_ring(h) for h in holes)
    edges = []
    for rid, ring in enumerate(rings):
        for (ax, ay), (bx, by) in zip(ring, ring[1:]+ring[:1]):
            edges.append((ax, ay, bx, by, rid, min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)))
    outer = rings[0]
    bounds = (min(x for x, _ in outer), min(y for _, y in outer),
              max(x for x, _ in outer), max(y for _, y in outer))
    digest = sha256(json.dumps(rings, separators=(',', ':')).encode('ascii')).hexdigest()
    return PreparedComponent(rings, bounds, _tree(edges), digest,
                             tuple(_ring_seeds(outer)), tuple(y for _, y in _sample(outer, 8)))


def _native_ring(chain):
    if hasattr(chain, 'ArcCount') and chain.ArcCount() != 0:
        raise ValueError("Arcs must be polygonized before witness verification")
    points = []
    for i in range(chain.PointCount()):
        p = chain.CPoint(i)
        points.append((int(p.x), int(p.y)))
    return tuple(points)


def prepare_polyset(polyset, outline_index=None):
    """Read KiCad SHAPE_POLY_SET; select exactly one outline and ITS holes.

    For a multi-component polyset an explicit outline_index is mandatory.
    No simplification, area threshold, native point classification, or mutation.
    """
    count = polyset.OutlineCount()
    if outline_index is None:
        if count != 1:
            raise ValueError("Expected one physical component; explicitly select outline_index")
        outline_index = 0
    _int(outline_index)
    if not 0 <= outline_index < count:
        raise IndexError("Physical outline index out of range")
    return prepare_rings(_native_ring(polyset.COutline(outline_index)),
                         (_native_ring(polyset.CHole(outline_index, h))
                          for h in range(polyset.HoleCount(outline_index))))


def verify_positive_witness(a, b, point, clearance_nm=2):
    """Only this exact verifier can accept a contact certificate."""
    p, r = ExactPoint.of(point), _guard(clearance_nm)
    return a.contains_with_clearance(p, r) and b.contains_with_clearance(p, r)


@dataclass(frozen=True, slots=True)
class Witness:
    point: ExactPoint
    clearance_nm: int
    component_sha256: tuple

    def to_dict(self):
        return {'method': 'exact_integer_pip_and_segment_distance',
                'point': self.point.to_dict(), 'clearance_nm_at_least': self.clearance_nm,
                'component_sha256': list(self.component_sha256)}


def verify_witness_record(a, b, record):
    """Recheck serialized certificate against the same coordinate snapshots."""
    if record.get('method') != 'exact_integer_pip_and_segment_distance':
        return False
    if record.get('component_sha256') != [a.digest, b.digest]:
        return False
    p = record['point']
    if p.get('unit') != 'nm':
        return False
    return verify_positive_witness(a, b, ExactPoint(p['x_num'], p['y_num'], p['den']),
                                   record['clearance_nm_at_least'])


@dataclass(frozen=True, slots=True)
class SearchResult:
    witness: object
    candidates_checked: int
    reason: str

    @property
    def found(self):
        return self.witness is not None


class NoPositiveWitness(RuntimeError):
    pass


def _mean(vertices):
    return ExactPoint(sum(x for x, _ in vertices), sum(y for _, y in vertices), len(vertices))


def _sample(values, limit):
    n = len(values)
    return [values[i*n//min(n, limit)] for i in range(min(n, limit))] if n else []


def _ring_seeds(ring):
    yield _mean(ring)
    sample = _sample(ring, 12)
    if len(sample) >= 3:
        for i in range(1, len(sample)-1):
            yield _mean((sample[0], sample[i], sample[i+1]))


def find_positive_witness(a, b, *, seed_points=(), seed_polyset=None,
                          clearance_nm=2, max_candidates=128, max_scanlines=16):
    """Bounded deterministic search; failure is NOT evidence of no overlap.

    Optional seed_polyset can be an untrusted native intersection (even wrong).
    A found point always passes the exact verifier against a AND b. An
    area-positive contact with no witness must be blocked/reviewed, never waived.
    Candidate iterables must be finite. Returned certificate binds coordinates.
    """
    r = _guard(clearance_nm)
    if type(max_candidates) is not int or max_candidates < 1 or type(max_scanlines) is not int or max_scanlines < 0:
        raise ValueError("Positive candidate budget and nonnegative scanline budget required")
    box = (max(a.bounds[0], b.bounds[0])+r, max(a.bounds[1], b.bounds[1])+r,
           min(a.bounds[2], b.bounds[2])-r, min(a.bounds[3], b.bounds[3])-r)
    if box[0] > box[2] or box[1] > box[3]:
        return SearchResult(None, 0, 'guarded_bounding_boxes_disjoint')
    seen, checked, considered = set(), 0, 0

    def check(point):
        nonlocal checked, considered
        considered += 1
        p = ExactPoint.of(point)
        if p in seen:
            return None
        seen.add(p)
        checked += 1
        if verify_positive_witness(a, b, p, r):
            return Witness(p, r, (a.digest, b.digest))
        return None

    def seeds():
        yield ExactPoint(box[0]+box[2], box[1]+box[3], 2)
        yield from seed_points
        if seed_polyset is not None:
            # Native area and native inside tests are intentionally never used.
            for i in range(min(seed_polyset.OutlineCount(), 8)):
                ring = _native_ring(seed_polyset.COutline(i))
                if ring:
                    yield from _ring_seeds(ring)
        for c in sorted((a, b), key=lambda c: len(c.rings[0])):
            yield from c.seeds

    for point in seeds():
        if considered >= max_candidates:
            return SearchResult(None, checked, 'candidate_budget_exhausted')
        witness = check(point)
        if witness:
            return SearchResult(witness, checked, 'exact_witness_found')
    # Scanline interval centers are additional seeds, not a relaxation. The
    # BVH y filter makes the large-zone fallback avoid irrelevant segments.
    ys = [Fraction(box[1]+box[3], 2)]
    ys += [Fraction((4-i)*box[1]+i*box[3], 4) for i in (1, 3, 0, 4)]
    for c in (a, b):
        ys += [Fraction(y) for y in c.sampled_y if box[1] <= y <= box[3]]
    unique_y = list(dict.fromkeys(ys))[:max_scanlines]
    for y in unique_y:
        ia, ib = a._scanline(y), b._scanline(y)
        i = j = 0
        while i < len(ia) and j < len(ib):
            lo, hi = max(ia[i][0], ib[j][0], box[0]), min(ia[i][1], ib[j][1], box[2])
            if lo <= hi:
                if considered >= max_candidates:
                    return SearchResult(None, checked, 'candidate_budget_exhausted')
                witness = check(((lo+hi)/2, y))
                if witness:
                    return SearchResult(witness, checked, 'exact_witness_found')
            if ia[i][1] <= ib[j][1]:
                i += 1
            else:
                j += 1
    return SearchResult(None, checked, 'bounded_search_found_no_witness')


def require_positive_witness(a, b, **kwargs):
    """For a proposed material edge: raise rather than silently skip/waive."""
    result = find_positive_witness(a, b, **kwargs)
    if not result.found:
        raise NoPositiveWitness(f"Contact has no exact >=2 nm witness: {result.reason}; checked={result.candidates_checked}")
    return result.witness
