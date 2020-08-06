from . import geohash
import math
from collections import namedtuple


Box = namedtuple("Box", ["s", "w", "n", "e"])


def geohash_bbox(gh):
    ret = geohash.bbox(gh)
    return Box(ret["s"], ret["w"], ret["n"], ret["e"])


def bbox(lat, lon, radius):
    lat_delta = radius * 360 / 40000
    lon_delta = lat_delta / math.cos(lat * math.pi / 180.0)
    return Box(lat - lat_delta, lon - lon_delta, lat + lat_delta, lon + lon_delta)


def overlap(a1, a2, b1, b2):
    return a1 < b2 and a2 > b1


def box_overlap(box1: Box, box2: Box):
    return overlap(box1.s, box1.n, box2.s, box2.n) and overlap(
        box1.w, box1.e, box2.w, box2.e
    )


def compute_geohash_tiles(lat, lon, radius, precision):
    bounds = bbox(lat, lon, radius)
    center = geohash.encode(lat, lon, precision)

    stack = set()
    checked = set()

    stack.add(center)
    checked.add(center)

    while stack:
        current = stack.pop()
        for neighbor in geohash.neighbors(current):
            if neighbor not in checked and box_overlap(geohash_bbox(neighbor), bounds):
                stack.add(neighbor)
                checked.add(neighbor)
    return checked


def geohash_overlap(lat, lon, radius, max_tiles=9):
    result = []
    for precision in range(1, 13):
        tiles = compute_geohash_tiles(lat, lon, radius, precision)
        if len(tiles) <= 9:
            result = tiles
            precision += 1
        else:
            break
    return result
