"""P5 Case Study · Nearby Drivers (Uber-style geo lookup).

When a rider opens the app, you need to find the few drivers within 2 km in
&lt; 50 ms. Scanning every driver in the city is too slow. The standard fix is
a *geohash*: encode each (lat, lng) into a short string where nearby points
share a common prefix. Bucket drivers by geohash prefix and only scan the
buckets that overlap the rider's location.

This file implements a simple geohash (axis-by-axis bit interleaving) and a
NearbyService that returns drivers within an approximate radius.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"  # geohash alphabet (no a, i, l, o)


def encode_geohash(lat: float, lng: float, precision: int = 6) -> str:
    """Encode (lat, lng) to a geohash string of `precision` characters."""
    lat_range = [-90.0, 90.0]
    lng_range = [-180.0, 180.0]
    bits: list[int] = []
    even = True  # alternates lng / lat
    while len(bits) < precision * 5:
        if even:
            mid = (lng_range[0] + lng_range[1]) / 2
            if lng >= mid:
                bits.append(1)
                lng_range[0] = mid
            else:
                bits.append(0)
                lng_range[1] = mid
        else:
            mid = (lat_range[0] + lat_range[1]) / 2
            if lat >= mid:
                bits.append(1)
                lat_range[0] = mid
            else:
                bits.append(0)
                lat_range[1] = mid
        even = not even

    out = []
    for i in range(0, len(bits), 5):
        chunk = bits[i : i + 5]
        n = 0
        for b in chunk:
            n = (n << 1) | b
        out.append(BASE32[n])
    return "".join(out)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@dataclass
class NearbyService:
    """Bucket drivers by geohash prefix and answer 'nearby' queries fast."""

    precision: int = 5  # ~ 4.9 km cell width
    _by_bucket: dict[str, list[tuple[str, float, float]]] = field(default_factory=dict)

    def update_driver(self, driver_id: str, lat: float, lng: float) -> None:
        """Re-register a driver's position into the right geohash bucket."""
        # Remove the driver from any previous bucket (toy implementation).
        for bucket in self._by_bucket.values():
            bucket[:] = [(d, la, ln) for (d, la, ln) in bucket if d != driver_id]
        gh = encode_geohash(lat, lng, self.precision)
        self._by_bucket.setdefault(gh, []).append((driver_id, lat, lng))

    def nearby(
        self, lat: float, lng: float, radius_km: float = 2.0
    ) -> list[tuple[str, float]]:
        """Return drivers within `radius_km`, smallest distance first."""
        center = encode_geohash(lat, lng, self.precision)
        # For the demo we look at the center bucket only. Real systems also
        # scan the 8 neighbouring buckets to handle the edge case where the
        # rider is near a cell boundary.
        candidates = self._by_bucket.get(center, [])
        results = []
        for driver_id, dlat, dlng in candidates:
            distance = haversine_km(lat, lng, dlat, dlng)
            if distance <= radius_km:
                results.append((driver_id, round(distance, 2)))
        return sorted(results, key=lambda x: x[1])


def main() -> None:
    """Place 50 random drivers around Bengaluru and find nearby ones."""
    random.seed(7)
    center_lat, center_lng = 12.9716, 77.5946  # Bengaluru
    svc = NearbyService(precision=5)
    for i in range(50):
        # Spread drivers within ~5 km
        dlat = (random.random() - 0.5) * 0.09
        dlng = (random.random() - 0.5) * 0.09
        svc.update_driver(f"driver-{i:02d}", center_lat + dlat, center_lng + dlng)

    riders = [
        ("MG Road", 12.9758, 77.6066),
        ("Indiranagar", 12.9784, 77.6408),
    ]
    for name, lat, lng in riders:
        bucket = encode_geohash(lat, lng, 5)
        nearby = svc.nearby(lat, lng, radius_km=2.0)
        print(f"rider @ {name:12s} bucket={bucket}  nearby_within_2km={nearby}")


if __name__ == "__main__":
    main()
