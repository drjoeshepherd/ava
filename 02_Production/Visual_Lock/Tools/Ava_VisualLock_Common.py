"""Ava visual-lock shared library (repository-local, portable).

Created by AVA-BASELINE-INTEGRITY-001 (02_Production/Tasks/AVA-BASELINE-INTEGRITY-001.sign.md).

Sections:
  1. Portable repository paths, checksums, Blender discovery.
  2. Raster measurement functions. These are copied verbatim (by AST extraction, not retyped)
     from the superseded Ava_RebuildVisualLock_v1.1.py so that measurements and formulas are
     identical to the ones that produced Ava_Geometry_Lock_v1.1.json. Do not edit them to
     improve scores; any change needs a new, approved gate/lock version.
  3. Front metrics, gate evaluation, and review artifacts.

This module must import inside Blender's bundled Python, which usually has no Pillow.
Pillow is only required for measurement, not for Blender-side rendering or inspection.
"""

TOOL_VERSION = "1.0.0"

import glob
import hashlib
import json
import math
import os
import shutil
import sys
from collections import deque

try:  # Pillow is absent inside Blender; only measurement needs it.
    from PIL import Image, ImageChops, ImageEnhance, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover
    Image = ImageChops = ImageEnhance = ImageDraw = ImageFont = None
    PIL_AVAILABLE = False

# ---------------------------------------------------------------------------
# 1. Portable paths, checksums, Blender discovery
# ---------------------------------------------------------------------------

VISUAL_LOCK_REL = os.path.join("02_Production", "Visual_Lock")


def find_repo_root(start=None):
    """Walk up from `start` (default: this file) to the folder holding CLAUDE.md and 02_Production/Visual_Lock."""
    here = os.path.abspath(start or os.path.dirname(os.path.abspath(__file__)))
    while True:
        if os.path.isfile(os.path.join(here, "CLAUDE.md")) and os.path.isdir(os.path.join(here, VISUAL_LOCK_REL)):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            raise RuntimeError("Ava repository root not found (looked for CLAUDE.md and 02_Production/Visual_Lock).")
        here = parent


def repo_paths(root):
    lock = os.path.join(root, VISUAL_LOCK_REL)
    return {
        "root": root,
        "visual_lock": lock,
        "manifest": os.path.join(lock, "Ava_Target_Manifest_v1.0.json"),
        "geometry_lock": os.path.join(lock, "Ava_Geometry_Lock_v1.1.json"),
        "gates": os.path.join(lock, "Ava_Front_Acceptance_Gates_v1.0.json"),
        "camera_lock": os.path.join(lock, "Ava_Camera_Lock_v1.0.json"),
        "material_lock": os.path.join(lock, "Ava_Material_Lock_v1.0.json"),
        "target_front": os.path.join(lock, "Targets", "Ava_Target_Front.png"),
        "target_front_mask": os.path.join(lock, "Targets", "Ava_Target_Front_Mask.png"),
        "renders": os.path.join(root, "05_Renders", "Visual_Lock"),
        "tools": os.path.join(lock, "Tools"),
    }


def rel(root, path):
    return os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def verify_manifest(paths):
    """Check every manifest entry against the file on disk. Returns a report; raises on any mismatch."""
    manifest = load_json(paths["manifest"])
    report = {"manifest": rel(paths["root"], paths["manifest"]), "entries": {}, "all_match": True}
    source = manifest["authoritative_source"]
    entries = {"authoritative_source": (os.path.join(paths["root"], source["file"]), source["sha256"])}
    for name, item in manifest["targets"].items():
        entries[name] = (os.path.join(paths["visual_lock"], item["file"]), item["sha256"])
    for name, (path, expected) in entries.items():
        actual = file_sha256(path) if os.path.isfile(path) else None
        ok = actual == expected.upper()
        report["entries"][name] = {"file": rel(paths["root"], path), "expected": expected.upper(), "actual": actual, "match": ok}
        report["all_match"] = report["all_match"] and ok
    if "FrontMask" not in manifest["targets"]:
        raise RuntimeError("Manifest has no FrontMask entry; the front silhouette mask is not checksum-locked.")
    if not report["all_match"]:
        raise RuntimeError("Canonical target checksum mismatch: " + json.dumps(report, indent=2))
    return report


def find_blender(explicit=None):
    """Locate blender. Order: --blender argument, AVA_BLENDER env var, PATH, standard install folders.
    Returns (path, searched_locations). Never installs anything."""
    searched = []
    candidates = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("AVA_BLENDER"):
        candidates.append(os.environ["AVA_BLENDER"])
    for name in ("blender", "blender.exe"):
        found = shutil.which(name)
        searched.append("PATH:" + name)
        if found:
            candidates.append(found)
    patterns = [
        r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
        r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Blender Foundation\Blender*\blender.exe"),
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/usr/bin/blender", "/usr/local/bin/blender", "/snap/bin/blender",
    ]
    for pattern in patterns:
        searched.append(pattern)
        candidates.extend(sorted(glob.glob(pattern), reverse=True))  # newest version folder first
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return os.path.abspath(candidate), searched
    return None, searched


def blender_script_args():
    """Arguments after '--' when a script runs inside Blender."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


# ---------------------------------------------------------------------------
# 2. Raster measurement functions (verbatim from Ava_RebuildVisualLock_v1.1.py)
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 600, 800







def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()

def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]

def rgb_distance(color, background):
    return max(abs(color[index] - background[index]) for index in range(3))

def luminance(color):
    return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]

def chroma(color):
    return max(color) - min(color)

def connected_components(binary, minimum_area=1):
    height = len(binary)
    width = len(binary[0])
    visited = [bytearray(width) for _ in range(height)]
    components = []
    for y in range(height):
        for x in range(width):
            if not binary[y][x] or visited[y][x]:
                continue
            queue = [(x, y)]
            visited[y][x] = 1
            points = []
            while queue:
                px, py = queue.pop()
                points.append((px, py))
                for ny in range(max(0, py - 1), min(height, py + 2)):
                    for nx in range(max(0, px - 1), min(width, px + 2)):
                        if binary[ny][nx] and not visited[ny][nx]:
                            visited[ny][nx] = 1
                            queue.append((nx, ny))
            if len(points) >= minimum_area:
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                components.append({
                    "points": points,
                    "area": len(points),
                    "bbox": [min(xs), min(ys), max(xs), max(ys)],
                    "centroid": [sum(xs) / len(xs), sum(ys) / len(ys)],
                })
    return components

def derive_silhouette(image):
    image = image.convert("RGB")
    pixels = image.load()
    border = []
    for x in range(image.width):
        border.extend([pixels[x, 0], pixels[x, image.height - 1]])
    for y in range(image.height):
        border.extend([pixels[0, y], pixels[image.width - 1, y]])
    background = tuple(int(round(sum(color[channel] for color in border) / len(border))) for channel in range(3))
    border_distances = [rgb_distance(color, background) for color in border]
    tolerance = max(3, percentile(border_distances, 0.995) + 2)

    background_reached = [bytearray(image.width) for _ in range(image.height)]
    queue = deque()
    for x in range(image.width):
        for y in (0, image.height - 1):
            if rgb_distance(pixels[x, y], background) <= tolerance and not background_reached[y][x]:
                background_reached[y][x] = 1
                queue.append((x, y))
    for y in range(image.height):
        for x in (0, image.width - 1):
            if rgb_distance(pixels[x, y], background) <= tolerance and not background_reached[y][x]:
                background_reached[y][x] = 1
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < image.width and 0 <= ny < image.height and not background_reached[ny][nx]:
                if rgb_distance(pixels[nx, ny], background) <= tolerance:
                    background_reached[ny][nx] = 1
                    queue.append((nx, ny))

    candidate = [bytearray(image.width) for _ in range(image.height)]
    for y in range(image.height):
        for x in range(image.width):
            if not background_reached[y][x]:
                candidate[y][x] = 1

    # Derive floor contact from the dark sole profile, then remove the broad,
    # low-contrast horizontal shadow outside the two sole-supported x ranges.
    bottom_start = round(image.height * 0.60)
    dark_counts = []
    dark_x_by_row = {}
    candidate_counts = []
    for y in range(bottom_start, image.height):
        dark_x = [x for x in range(image.width) if candidate[y][x] and luminance(pixels[x, y]) < 140]
        dark_x_by_row[y] = dark_x
        dark_counts.append((len(dark_x), y))
        candidate_counts.append((sum(candidate[y]), y))
    valid_contact_rows = [y for count, y in dark_counts if count >= 8]
    body_bottom = max(valid_contact_rows)
    _, sole_peak_row = max(dark_counts)
    sole_x = dark_x_by_row[sole_peak_row]
    runs = []
    if sole_x:
        start = previous = sole_x[0]
        for x in sole_x[1:]:
            if x - previous > 4:
                runs.append([start, previous])
                start = x
            previous = x
        runs.append([start, previous])
    sole_runs = sorted(runs, key=lambda run: run[1] - run[0], reverse=True)[:2]
    sole_runs = [[max(0, run[0] - 8), min(image.width - 1, run[1] + 8)] for run in sole_runs]
    count_map = {y: count for count, y in candidate_counts}
    onset_candidates = []
    for y in range(max(bottom_start + 1, sole_peak_row - 90), sole_peak_row + 1):
        onset_candidates.append((count_map.get(y, 0) - count_map.get(y - 1, 0), y))
    _, shadow_onset = max(onset_candidates)
    for y in range(shadow_onset, body_bottom + 1):
        for x in range(image.width):
            if candidate[y][x] and not any(run[0] <= x <= run[1] for run in sole_runs):
                candidate[y][x] = 0
    for y in range(body_bottom + 1, image.height):
        candidate[y] = bytearray(image.width)

    components = connected_components(candidate, minimum_area=18)
    kept = [component for component in components if component["bbox"][1] <= body_bottom and component["bbox"][3] - component["bbox"][1] >= 4]
    mask = [bytearray(image.width) for _ in range(image.height)]
    for component in kept:
        for x, y in component["points"]:
            mask[y][x] = 1

    points = [(x, y) for y in range(image.height) for x in range(image.width) if mask[y][x]]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    bounds = [min(xs), min(ys), max(xs), max(ys)]
    return mask, {
        "background_rgb": list(background),
        "background_tolerance": tolerance,
        "shadow_exclusion_bottom_row": body_bottom,
        "shadow_onset_row": shadow_onset,
        "sole_peak_row": sole_peak_row,
        "sole_supported_x_ranges": sole_runs,
        "bounds_inclusive": bounds,
        "foreground_pixel_count": len(points),
        "derivation": "Border-connected background flood fill; floor contact derived from the last row with at least eight pixels below luminance 140; broad lower-row shadow pixels outside the two peak-sole support ranges removed; components below 18 pixels discarded.",
    }

def save_mask(mask, path):
    image = Image.new("L", (len(mask[0]), len(mask)), 0)
    pixels = image.load()
    for y, row in enumerate(mask):
        for x, value in enumerate(row):
            if value:
                pixels[x, y] = 255
    image.save(path, optimize=True)

def mask_bounds(mask):
    points = [(x, y) for y, row in enumerate(mask) for x, value in enumerate(row) if value]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]

def row_extents(mask, y, x_min=0, x_max=None):
    x_max = len(mask[0]) - 1 if x_max is None else x_max
    xs = [x for x in range(x_min, x_max + 1) if mask[y][x]]
    return [min(xs), max(xs)] if xs else None

def find_head_cut(mask, bounds):
    left, top, right, bottom = bounds
    widths = []
    for y in range(top, bottom + 1):
        extent = row_extents(mask, y)
        widths.append((extent[1] - extent[0] + 1) if extent else 0)
    smooth = []
    for index in range(len(widths)):
        values = widths[max(0, index - 3):min(len(widths), index + 4)]
        smooth.append(sum(values) / len(values))
    start = round(len(widths) * 0.18)
    stop = round(len(widths) * 0.52)
    candidates = []
    for index in range(start + 4, stop - 4):
        drop = smooth[index - 4] - smooth[index + 4]
        candidates.append((drop, index))
    _, best = max(candidates)
    return top + best

def norm_point(point, bounds):
    left, top, right, bottom = bounds
    height = bottom - top + 1
    center_x = (left + right) / 2.0
    return [(point[0] - center_x) / height, (bottom - point[1]) / height]

def norm_distance(pixels, bounds):
    return pixels / (bounds[3] - bounds[1] + 1)

def entry(pixel_value, normalized_value, derivation, status="measured"):
    return {
        "status": status,
        "source": "Ava_Target_Front.png",
        "pixel_value": pixel_value,
        "normalized_value": normalized_value,
        "derivation": derivation,
    }

def manual(reason, observed=None):
    value = {
        "status": "manual_review_required",
        "source": "Ava_Target_Front.png",
        "reason": reason,
        "pixel_value": None,
        "normalized_value": None,
        "derivation": "No exact value stored because the raster does not expose an unambiguous boundary or joint center.",
    }
    if observed is not None:
        value["observed_visible_region"] = observed
    return value

def feature_mask(image, predicate):
    pixels = image.load()
    return [bytearray(1 if predicate(pixels[x, y], x, y) else 0 for x in range(image.width)) for y in range(image.height)]

def component_bbox_entry(component, bounds, derivation):
    x0, y0, x1, y1 = component["bbox"]
    normalized = {
        "xmin": norm_point((x0, y0), bounds)[0],
        "xmax": norm_point((x1, y1), bounds)[0],
        "ymin": norm_point((x0, y1), bounds)[1],
        "ymax": norm_point((x1, y0), bounds)[1],
    }
    return entry({"xmin": x0, "ymin": y0, "xmax": x1, "ymax": y1}, normalized, derivation)

def analyze_raster(image, mask, segmentation):
    pixels = image.load()
    bounds = mask_bounds(mask)
    left, top, right, bottom = bounds
    char_height = bottom - top + 1
    center_x = (left + right) / 2.0
    head_bottom = find_head_cut(mask, bounds)
    head_points = [(x, y) for y in range(top, head_bottom + 1) for x in range(WIDTH) if mask[y][x]]
    hx = [point[0] for point in head_points]
    hy = [point[1] for point in head_points]
    head_left, head_right = min(hx), max(hx)
    head_top = min(hy)
    head_height = head_bottom - head_top + 1
    head_row_widths = []
    for y in range(head_top, head_bottom + 1):
        extent = row_extents(mask, y)
        if extent:
            head_row_widths.append((extent[1] - extent[0] + 1, y, extent))
    head_max_width, head_max_row, head_max_extent = max(head_row_widths)

    face_binary = feature_mask(image, lambda color, x, y:
        mask[y][x] and head_top <= y <= head_bottom and
        abs(x - center_x) <= head_max_width * 0.30 and color[0] >= 150 and
        color[0] - color[1] >= 2 and color[1] - color[2] >= 2)
    face_components = connected_components(face_binary, minimum_area=60)
    face_component = max(face_components, key=lambda component: component["area"])
    face_points = face_component["points"]
    central_face_points = [point for point in face_points if abs(point[0] - center_x) <= head_max_width * 0.10]
    chin_y = max(point[1] for point in central_face_points)
    chin_row = [point[0] for point in central_face_points if point[1] == chin_y]
    chin = [sum(chin_row) / len(chin_row), chin_y]
    lower_face_rows = []
    lower_start = round(head_top + head_height * (2.0 / 3.0))
    for y in range(lower_start, chin_y + 1):
        xs = [x for x, py in face_points if py == y]
        if xs:
            lower_face_rows.append((max(xs) - min(xs) + 1, y, [min(xs), max(xs)]))
    _, cheek_row, cheek_extent = max(lower_face_rows)

    amber_binary = feature_mask(image, lambda color, x, y:
        color[0] > 112 and 38 < color[1] < 210 and color[2] < 122 and
        color[0] > color[1] * 1.12 and color[1] > max(1, color[2]) * 1.15)
    amber_components = connected_components(amber_binary, minimum_area=20)
    eye_candidates = []
    for component in amber_components:
        width = component["bbox"][2] - component["bbox"][0] + 1
        height = component["bbox"][3] - component["bbox"][1] + 1
        aspect = width / max(1, height)
        if (component["centroid"][1] < head_bottom and
                abs(component["centroid"][0] - center_x) < char_height * 0.22 and
                20 <= width <= 80 and 20 <= height <= 80 and 0.55 <= aspect <= 1.65):
            eye_candidates.append(component)
    eyes = sorted(sorted(eye_candidates, key=lambda component: component["area"], reverse=True)[:2], key=lambda component: component["centroid"][0])

    eye_data = []
    for component in eyes:
        ix0, iy0, ix1, iy1 = component["bbox"]
        cx, cy = component["centroid"]
        window = [max(0, ix0 - 20), max(0, iy0 - 32), min(WIDTH - 1, ix1 + 20), min(HEIGHT - 1, iy1 + 32)]
        feature_points = []
        for y in range(window[1], window[3] + 1):
            for x in range(window[0], window[2] + 1):
                color = pixels[x, y]
                if luminance(color) < 155 or (chroma(color) > 40 and color[0] > color[1]):
                    feature_points.append((x, y))
        ex = [point[0] for point in feature_points]
        ey = [point[1] for point in feature_points]
        eye_bbox = [min(ex), min(ey), max(ex), max(ey)]
        pupil_points = []
        for y in range(iy0, iy1 + 1):
            for x in range(ix0, ix1 + 1):
                if luminance(pixels[x, y]) < 70:
                    pupil_points.append((x, y))
        pupil_center = [sum(p[0] for p in pupil_points) / len(pupil_points), sum(p[1] for p in pupil_points) / len(pupil_points)] if pupil_points else None
        eye_data.append({"iris": component, "eye_bbox": eye_bbox, "pupil_center": pupil_center})

    central_dark = feature_mask(image, lambda color, x, y:
        abs(x - center_x) <= char_height * 0.13 and
        (sum(item["iris"]["centroid"][1] for item in eye_data) / 2 + 18) <= y <= chin_y and
        luminance(color) < 155)
    mouth_components = connected_components(central_dark, minimum_area=8)
    mouth_component = max(mouth_components, key=lambda component: (component["bbox"][2] - component["bbox"][0], component["area"])) if mouth_components else None

    nose_binary = feature_mask(image, lambda color, x, y:
        abs(x - center_x) <= 28 and eye_data[0]["iris"]["centroid"][1] <= y <= (mouth_component["centroid"][1] if mouth_component else chin_y) and
        color[0] > 175 and color[0] - color[1] > 12 and color[1] - color[2] > 6)
    nose_components = connected_components(nose_binary, minimum_area=5)
    nose_component = max(nose_components, key=lambda component: component["area"]) if nose_components else None

    hair_binary = feature_mask(image, lambda color, x, y:
        mask[y][x] and head_top <= y <= head_bottom and
        color[2] >= color[0] - 14 and abs(color[0] - color[1]) <= 28 and luminance(color) >= 110)
    hair_components = connected_components(hair_binary, minimum_area=50)
    hair_points = [point for component in hair_components for point in component["points"]]
    hair_x = [point[0] for point in hair_points]
    hair_y = [point[1] for point in hair_points]
    hair_bbox = [min(hair_x), min(hair_y), max(hair_x), max(hair_y)]

    dark_binary = feature_mask(image, lambda color, x, y: mask[y][x] and luminance(color) < 125)
    dark_components = connected_components(dark_binary, minimum_area=25)
    hand_candidates = [component for component in dark_components
                       if component["centroid"][1] > head_bottom and abs(component["centroid"][0] - center_x) > char_height * 0.20]
    hands = sorted(sorted(hand_candidates, key=lambda component: component["area"], reverse=True)[:2], key=lambda component: component["centroid"][0])

    chest_candidates = [component for component in amber_components
                        if component["centroid"][1] > head_bottom and abs(component["centroid"][0] - center_x) < char_height * 0.10]
    chest = max(chest_candidates, key=lambda component: component["area"]) if chest_candidates else None

    character = {
        "topmost_visible_pixel": entry([center_x, top], norm_point((center_x, top), bounds), "Minimum y in canonical silhouette mask."),
        "bottommost_visible_pixel": entry([center_x, bottom], norm_point((center_x, bottom), bounds), "Maximum y in shadow-free canonical silhouette mask."),
        "centerline": entry(center_x, 0.0, "Midpoint of the inclusive leftmost and rightmost canonical silhouette pixels."),
        "bounding_box": entry({"xmin": left, "ymin": top, "xmax": right, "ymax": bottom}, {"xmin": norm_point((left, top), bounds)[0], "xmax": norm_point((right, bottom), bounds)[0], "ymin": 0.0, "ymax": 1.0}, "Inclusive bounds of the shadow-free canonical silhouette mask."),
        "total_height": entry(char_height, 1.0, "bottommost_y - topmost_y + 1."),
    }

    head = {
        "top": entry([center_x, head_top], norm_point((center_x, head_top), bounds), "Top row of the upper silhouette component."),
        "bottom": entry([center_x, head_bottom], norm_point((center_x, head_bottom), bounds), "Strongest upper-half silhouette-width contraction, derived from an 7-row smoothed row-width profile."),
        "leftmost": entry([head_left, next(y for x, y in head_points if x == head_left)], norm_point((head_left, next(y for x, y in head_points if x == head_left)), bounds), "Minimum x within the raster-derived head region."),
        "rightmost": entry([head_right, next(y for x, y in head_points if x == head_right)], norm_point((head_right, next(y for x, y in head_points if x == head_right)), bounds), "Maximum x within the raster-derived head region."),
        "max_width_row": entry({"row": head_max_row, "left": head_max_extent[0], "right": head_max_extent[1], "width": head_max_width}, {"row_y": norm_point((center_x, head_max_row), bounds)[1], "width": norm_distance(head_max_width, bounds)}, "Maximum inclusive silhouette width within the raster-derived head region."),
        "height": entry(head_height, norm_distance(head_height, bounds), "head_bottom - head_top + 1."),
        "canonical_heads_tall": entry(char_height / head_height, char_height / head_height, "character_total_height_pixels / head_height_pixels."),
        "chin": entry(chin, norm_point(chin, bounds), "Bottommost pixel of the largest warm face-color component inside the central head region."),
        "cheek_left": entry([cheek_extent[0], cheek_row], norm_point((cheek_extent[0], cheek_row), bounds), "Left extent on the widest lower-half row of the warm face-color component."),
        "cheek_right": entry([cheek_extent[1], cheek_row], norm_point((cheek_extent[1], cheek_row), bounds), "Right extent on the widest lower-half row of the warm face-color component."),
    }

    eyes_output = {}
    for label, data in zip(["left", "right"], eye_data):
        iris = data["iris"]
        bbox = data["eye_bbox"]
        iris_width = iris["bbox"][2] - iris["bbox"][0] + 1
        iris_height = iris["bbox"][3] - iris["bbox"][1] + 1
        eyes_output[label] = {
            "eye_center": entry([(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2], norm_point(((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2), bounds), "Center of the local eye-feature bounding box surrounding the detected amber iris."),
            "eye_bounding_box": entry({"xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3]}, {"xmin": norm_point((bbox[0], bbox[1]), bounds)[0], "xmax": norm_point((bbox[2], bbox[3]), bounds)[0], "ymin": norm_point((bbox[0], bbox[3]), bounds)[1], "ymax": norm_point((bbox[2], bbox[1]), bounds)[1]}, "Bounds of dark or strongly chromatic eye-feature pixels within the iris-local window."),
            "iris_center": entry(iris["centroid"], norm_point(iris["centroid"], bounds), "Centroid of the connected amber iris component."),
            "iris_diameter": entry({"width": iris_width, "height": iris_height, "equivalent": (iris_width + iris_height) / 2}, {"width": norm_distance(iris_width, bounds), "height": norm_distance(iris_height, bounds), "equivalent": norm_distance((iris_width + iris_height) / 2, bounds)}, "Inclusive amber-component width and height; equivalent diameter is their arithmetic mean."),
            "pupil_center": entry(data["pupil_center"], norm_point(data["pupil_center"], bounds), "Centroid of pixels with luminance below 70 inside the detected iris bounding box.") if data["pupil_center"] else manual("Pupil pixels were not isolated unambiguously."),
        }

    face = {
        "mouth_center": entry(mouth_component["centroid"], norm_point(mouth_component["centroid"], bounds), "Centroid of the widest connected dark component below the eye band in the central face region.") if mouth_component else manual("Mouth component not isolated."),
        "mouth_extents": entry({"left": mouth_component["bbox"][0], "right": mouth_component["bbox"][2], "row_range": [mouth_component["bbox"][1], mouth_component["bbox"][3]]}, {"left": norm_point((mouth_component["bbox"][0], mouth_component["centroid"][1]), bounds)[0], "right": norm_point((mouth_component["bbox"][2], mouth_component["centroid"][1]), bounds)[0]}, "Horizontal bounds of the detected mouth component.") if mouth_component else manual("Mouth extents not isolated."),
        "nose_center": entry(nose_component["centroid"], norm_point(nose_component["centroid"], bounds), "Centroid of the largest warm chromatic component between the eye and mouth bands.") if nose_component else manual("Nose component not isolated."),
        "brow_landmarks": manual("Hair, brow, and eyelash tones overlap in the raster; individual brow endpoints cannot be isolated without human annotation."),
    }

    hair = {
        "outer_extents": entry({"left": hair_bbox[0], "top": hair_bbox[1], "right": hair_bbox[2], "bottom": hair_bbox[3]}, {"left": norm_point((hair_bbox[0], hair_bbox[1]), bounds)[0], "right": norm_point((hair_bbox[2], hair_bbox[3]), bounds)[0], "top": norm_point((hair_bbox[0], hair_bbox[1]), bounds)[1], "bottom": norm_point((hair_bbox[2], hair_bbox[3]), bounds)[1]}, "Bounds of connected light neutral/silver pixels inside the raster-derived head region."),
        "lower_bob_boundary": entry(hair_bbox[3], norm_point((center_x, hair_bbox[3]), bounds)[1], "Maximum y of the detected silver-hair pixel set."),
        "top_silhouette": entry(hair_bbox[1], norm_point((center_x, hair_bbox[1]), bounds)[1], "Minimum y of the detected silver-hair pixel set."),
        "side_silhouette_landmarks": manual("The white hair edge and white background merge at several anti-aliased locations; exact side landmark correspondence requires human annotation.", {"hair_bbox": hair_bbox}),
    }

    modules = {
        "left": manual("The left listening module is partially occluded by hair; its full circle, center, and diameters are not directly visible."),
        "right": manual("The right listening module is partially occluded by hair; its full circle, center, and diameters are not directly visible."),
    }

    torso = {
        "shoulder_centers": manual("Shoulder joint centers are partially occluded by shell overlaps."),
        "widest_points": manual("Torso and upper-arm white shells touch in the raster, preventing an unambiguous torso-only width."),
        "chest_light": {
            "center": entry(chest["centroid"], norm_point(chest["centroid"], bounds), "Centroid of the largest central amber component below the head.") if chest else manual("Chest light not isolated."),
            "visible_bbox": component_bbox_entry(chest, bounds, "Bounds of the connected central amber chest-light component.") if chest else manual("Chest light not isolated."),
        },
        "waist_extents": manual("White torso, graphite waist, and thigh shells overlap without a single unambiguous raster boundary."),
        "pelvis_extents": manual("Pelvis shell boundaries are occluded by graphite waist and thigh shells."),
    }

    arms_hands = {
        "shoulder": manual("Shoulder centers require human joint annotation."),
        "elbow": manual("Elbow centers require human joint annotation."),
        "wrist": manual("Wrist centers require human joint annotation."),
        "hand_bounding_boxes": {
            "left": component_bbox_entry(hands[0], bounds, "Bounds of the outermost connected dark hand component on the image-left side.") if len(hands) == 2 else manual("Left hand component not isolated."),
            "right": component_bbox_entry(hands[1], bounds, "Bounds of the outermost connected dark hand component on the image-right side.") if len(hands) == 2 else manual("Right hand component not isolated."),
        },
    }

    legs_feet = {
        "hip": manual("Hip centers are occluded by pelvis and thigh shells."),
        "knee": manual("Knee centers are occluded by overlapping shell and joint pixels."),
        "ankle": manual("Ankle centers are occluded by shin and foot shell overlap."),
        "thigh_width": manual("The thigh/pelvis boundary is not unambiguous in the raster."),
        "lower_leg_width": manual("The knee/shin boundary is not unambiguous in the raster."),
        "foot_bounding_boxes": manual("The foot/shin boundary and floor contact contain anti-aliased overlap; human annotation is required."),
    }

    return {
        "bounds": bounds,
        "segmentation": segmentation,
        "character": character,
        "head": head,
        "eyes": eyes_output,
        "face": face,
        "hair": hair,
        "listening_modules": modules,
        "torso": torso,
        "arms_hands": arms_hands,
        "legs_feet": legs_feet,
        "manual_review_required": [
            "face.brow_landmarks",
            "hair.side_silhouette_landmarks",
            "listening_modules.left center/outer diameter/inner diameter",
            "listening_modules.right center/outer diameter/inner diameter",
            "torso.shoulder_centers/widest_points/waist_extents/pelvis_extents",
            "arms_hands.shoulder/elbow/wrist",
            "legs_feet.hip/knee/ankle/thigh_width/lower_leg_width/foot_bounding_boxes",
        ],
    }

def bbox_value(record):
    return record.get("pixel_value") if record.get("status") == "measured" else None

def draw_landmarks(image, analysis, path):
    canvas = image.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font = ImageFont.load_default()
    colors = {"character": (0, 210, 255), "head": (255, 80, 80), "eye": (0, 255, 110), "face": (255, 210, 0), "hair": (160, 80, 255), "hand": (255, 80, 210)}
    bounds = analysis["bounds"]
    draw.rectangle(bounds, outline=colors["character"], width=2)
    h = analysis["head"]
    head_top = round(h["top"]["pixel_value"][1]); head_bottom = round(h["bottom"]["pixel_value"][1])
    draw.line((0, head_bottom, WIDTH - 1, head_bottom), fill=colors["head"], width=2)
    maxrow = h["max_width_row"]["pixel_value"]
    draw.line((maxrow["left"], maxrow["row"], maxrow["right"], maxrow["row"]), fill=colors["head"], width=3)
    for label in ["left", "right"]:
        eye = analysis["eyes"][label]
        box = eye["eye_bounding_box"]["pixel_value"]
        draw.rectangle((box["xmin"], box["ymin"], box["xmax"], box["ymax"]), outline=colors["eye"], width=2)
        center = eye["iris_center"]["pixel_value"]
        draw.ellipse((center[0] - 3, center[1] - 3, center[0] + 3, center[1] + 3), fill=colors["eye"])
        draw.text((box["xmin"], box["ymin"] - 15), label + " eye", fill=colors["eye"], font=font)
    for key in ["chin", "cheek_left", "cheek_right"]:
        point = h[key]["pixel_value"]
        draw.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3), fill=colors["face"])
        draw.text((point[0] + 4, point[1]), key, fill=colors["face"], font=font)
    hair = analysis["hair"]["outer_extents"]["pixel_value"]
    draw.rectangle((hair["left"], hair["top"], hair["right"], hair["bottom"]), outline=colors["hair"], width=2)
    for side in ["left", "right"]:
        record = analysis["arms_hands"]["hand_bounding_boxes"][side]
        if record["status"] == "measured":
            box = record["pixel_value"]
            draw.rectangle((box["xmin"], box["ymin"], box["xmax"], box["ymax"]), outline=colors["hand"], width=2)
    draw.rectangle((10, 10, 385, 90), fill=(255, 255, 255), outline=(0, 0, 0))
    draw.text((20, 18), "Ava Geometry Lock v1.1 — raster-derived", fill=(0, 0, 0), font=font)
    draw.text((20, 38), "Solid marks: automated direct measurements", fill=(0, 0, 0), font=font)
    draw.text((20, 58), "Unmarked ambiguous joints/modules require manual review", fill=(0, 0, 0), font=font)
    canvas.save(path, optimize=True)

def metric(status, formula, target, rendered, error, threshold, passed=None, note=None):
    value = {"status": status, "formula": formula, "target_measurement": target, "rendered_measurement": rendered, "error": error, "threshold": threshold}
    if passed is not None:
        value["pass"] = passed
    if note:
        value["note"] = note
    return value

def measured(record):
    return record.get("status") == "measured"


# ---------------------------------------------------------------------------
# 3. Front metrics, gates, artifacts
# ---------------------------------------------------------------------------

def load_binary_mask(path):
    image = Image.open(path).convert("L")
    if image.size != (WIDTH, HEIGHT):
        raise RuntimeError("Mask %s is %s, expected %s" % (path, image.size, (WIDTH, HEIGHT)))
    pixels = image.load()
    return [bytearray(1 if pixels[x, y] > 127 else 0 for x in range(WIDTH)) for y in range(HEIGHT)]


def _box_wh(box):
    return box["xmax"] - box["xmin"] + 1, box["ymax"] - box["ymin"] + 1


def _gate_result(value_for_pass, comparison, threshold):
    if comparison == ">=":
        return value_for_pass >= threshold
    if comparison == "<=":
        return value_for_pass <= threshold
    raise ValueError(comparison)


def compute_front_metrics(lock, gates, target_mask, render_mask, render_analysis, render_segmentation):
    """Front metrics. Target values come from the approved Geometry Lock (authority 2), the target
    silhouette from the checksum-locked mask file. Formulas match Ava_RebuildVisualLock_v1.1.py."""
    L = lock["landmarks"]
    blocking = gates["blocking_gates"]
    secondary = gates["secondary_metrics"]
    results = {}

    # SilhouetteIoU
    intersection = union = target_count = render_count = 0
    for y in range(HEIGHT):
        t_row, r_row = target_mask[y], render_mask[y]
        for x in range(WIDTH):
            t, r = t_row[x], r_row[x]
            target_count += t
            render_count += r
            intersection += t and r
            union += t or r
    iou = intersection / union if union else 0.0
    g = blocking["SilhouetteIoU"]
    results["SilhouetteIoU"] = {"status": "calculated", "blocking": True, "formula": g["formula"],
        "target_measurement": {"foreground_pixels": target_count},
        "rendered_measurement": {"foreground_pixels": render_count, "intersection": intersection, "union": union},
        "value": iou, "comparison": g["comparison"], "threshold": g["threshold"],
        "pass": _gate_result(iou, g["comparison"], g["threshold"])}

    # HeadBodyRatioError
    target_ratio = L["head"]["canonical_heads_tall"]["pixel_value"]
    render_ratio = render_analysis["head"]["canonical_heads_tall"]["pixel_value"]
    ratio_error = abs(render_ratio - target_ratio) / target_ratio
    g = blocking["HeadBodyRatioError"]
    results["HeadBodyRatioError"] = {"status": "calculated", "blocking": True, "formula": g["formula"],
        "target_measurement": {"heads_tall": target_ratio, "character_height_px": L["character"]["total_height"]["pixel_value"], "head_height_px": L["head"]["height"]["pixel_value"]},
        "rendered_measurement": {"heads_tall": render_ratio, "character_height_px": render_analysis["character"]["total_height"]["pixel_value"], "head_height_px": render_analysis["head"]["height"]["pixel_value"]},
        "value": ratio_error, "comparison": g["comparison"], "threshold": g["threshold"],
        "pass": _gate_result(ratio_error, g["comparison"], g["threshold"])}

    # Eyes
    head_width = L["head"]["max_width_row"]["pixel_value"]["width"]
    center_errors, size_errors, t_centers, r_centers, t_boxes, r_boxes = [], [], [], [], [], []
    for side in ("left", "right"):
        tc = L["eyes"][side]["eye_center"]["pixel_value"]
        rc = render_analysis["eyes"][side]["eye_center"]["pixel_value"]
        center_errors.append(math.dist(tc, rc) / head_width)
        tb = L["eyes"][side]["eye_bounding_box"]["pixel_value"]
        rb = render_analysis["eyes"][side]["eye_bounding_box"]["pixel_value"]
        tw, th = _box_wh(tb)
        rw, rh = _box_wh(rb)
        size_errors.append((abs(rw - tw) / tw + abs(rh - th) / th) / 2)
        t_centers.append(tc); r_centers.append(rc); t_boxes.append(tb); r_boxes.append(rb)
    for name, errors, tv, rv in (("EyeCenterError", center_errors, t_centers, r_centers),
                                 ("EyeSizeError", size_errors, t_boxes, r_boxes)):
        g = blocking[name]
        results[name] = {"status": "calculated", "blocking": True, "formula": g["formula"],
            "normalization": g.get("normalization"), "target_measurement": tv, "rendered_measurement": rv,
            "per_eye": {"left": errors[0], "right": errors[1]},
            "value": sum(errors) / len(errors), "reported_value_rule": g["reported_value"],
            "pass_rule": g["pass_rule"], "comparison": g["comparison"], "threshold": g["threshold"],
            "pass": _gate_result(max(errors), g["comparison"], g["threshold"])}

    # Listening modules: evaluated only when the target is directly measurable.
    modules = L["listening_modules"]
    measurable = all(modules[s].get("status") == "measured" for s in ("left", "right"))
    for name in ("ListeningModuleCenterError", "ListeningModuleDiameterError"):
        g = blocking[name]
        if measurable:
            raise RuntimeError("Listening-module targets are now measured in the lock, but render-side module "
                               "measurement is not implemented. Implement it under a new approved tool version.")
        results[name] = {"status": "manual_review_required", "blocking": True, "formula": g["formula"],
            "target_measurement": None, "rendered_measurement": None, "value": None,
            "comparison": g["comparison"], "threshold": g["threshold"],
            "reason": modules["left"].get("reason", "Target not directly measurable.")}

    # Secondary: HandScaleError (non-blocking)
    t_hands = L["arms_hands"]["hand_bounding_boxes"]
    r_hands = render_analysis["arms_hands"]["hand_bounding_boxes"]
    hand_errors = {}
    for side in ("left", "right"):
        if measured(t_hands[side]) and measured(r_hands[side]):
            tw, th = _box_wh(t_hands[side]["pixel_value"])
            rw, rh = _box_wh(r_hands[side]["pixel_value"])
            hand_errors[side] = (abs(rw - tw) / tw + abs(rh - th) / th) / 2
    s = secondary["HandScaleError"]
    if hand_errors:
        value = sum(hand_errors.values()) / len(hand_errors)
        results["HandScaleError"] = {"status": "calculated", "blocking": False, "formula": s["formula"],
            "target_measurement": [bbox_value(t_hands[k]) for k in ("left", "right")],
            "rendered_measurement": [bbox_value(r_hands[k]) for k in ("left", "right")],
            "per_hand": hand_errors, "value": value, "reference_threshold": s["reference_threshold"],
            "within_reference_threshold": max(hand_errors.values()) <= s["reference_threshold"],
            "note": s["note"]}
    else:
        results["HandScaleError"] = {"status": "manual_review_required", "blocking": False, "formula": s["formula"],
            "value": None, "note": "Hand components not isolated in both images."}
    for name in ("TorsoWidthError", "ThighWidthError", "FootWidthError"):
        results[name] = {"status": "manual_review_required", "blocking": False,
                         "formula": secondary[name]["formula"], "value": None}

    calculated_blocking = [k for k, v in results.items() if v["blocking"] and v["status"] == "calculated"]
    failing = [k for k in calculated_blocking if not results[k]["pass"]]
    manual = [k for k, v in results.items() if v["status"] == "manual_review_required"]
    summary = {
        "front_identity_gates": "PASS" if not failing else "FAIL",
        "calculated_blocking_gates": calculated_blocking,
        "failing_blocking_gates": failing,
        "manual_review_required_metrics": manual,
        "rule": gates["overall_rule"],
        "visual_approval": "NOT_GRANTED_BY_METRICS — human review approves character fidelity.",
    }
    return results, summary


def save_overlay(target_image, render_image, path):
    Image.blend(target_image, render_image, 0.5).save(path, optimize=True)


def save_difference(target_image, render_image, path):
    ImageEnhance.Contrast(ImageChops.difference(target_image, render_image)).enhance(2.4).save(path, optimize=True)


def save_mask_comparison(target_mask, render_mask, path):
    """White = both, red = target only (render missing), cyan = render only (render extra)."""
    image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    px = image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            t, r = target_mask[y][x], render_mask[y][x]
            if t and r:
                px[x, y] = (255, 255, 255)
            elif t:
                px[x, y] = (255, 70, 70)
            elif r:
                px[x, y] = (0, 200, 255)
    image.save(path, optimize=True)


def save_landmark_visualization(render_image, lock, render_analysis, path, title):
    """Render with its measured landmarks (green) and the Geometry Lock target landmarks (red)."""
    canvas = render_image.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
    target_color, render_color = (230, 40, 40), (0, 170, 60)
    L = lock["landmarks"]

    def box(record, color, width=2):
        if record.get("status") == "measured":
            b = record["pixel_value"]
            draw.rectangle((b["xmin"], b["ymin"], b["xmax"], b["ymax"]), outline=color, width=width)

    def dot(point, color, r=3):
        draw.ellipse((point[0] - r, point[1] - r, point[0] + r, point[1] + r), outline=color, width=2)

    for source, color in ((L, target_color), (render_analysis, render_color)):
        bounds = source["character"]["bounding_box"]["pixel_value"]
        draw.rectangle((bounds["xmin"], bounds["ymin"], bounds["xmax"], bounds["ymax"]), outline=color, width=1)
        head_bottom = round(source["head"]["bottom"]["pixel_value"][1])
        draw.line((0, head_bottom, WIDTH - 1, head_bottom), fill=color, width=1)
        for side in ("left", "right"):
            box(source["eyes"][side]["eye_bounding_box"], color)
            dot(source["eyes"][side]["eye_center"]["pixel_value"], color)
            box(source["arms_hands"]["hand_bounding_boxes"][side], color)
    draw.rectangle((8, 8, 330, 64), fill=(255, 255, 255), outline=(0, 0, 0))
    draw.text((14, 12), title, fill=(0, 0, 0), font=font)
    draw.text((14, 28), "Red: Geometry Lock v1.1 target landmarks", fill=target_color, font=font)
    draw.text((14, 44), "Green: landmarks measured on this render", fill=render_color, font=font)
    canvas.save(path, optimize=True)


def find_identical_prior_artifacts(root, output_paths, exclude_dir):
    """Map each output to any byte-identical file elsewhere under 05_Renders/Visual_Lock."""
    renders = os.path.join(root, "05_Renders", "Visual_Lock")
    exclude_dir = os.path.abspath(exclude_dir)
    prior = {}
    for dirpath, _, files in os.walk(renders):
        if os.path.abspath(dirpath).startswith(exclude_dir):
            continue
        for name in files:
            path = os.path.join(dirpath, name)
            prior.setdefault(file_sha256(path), []).append(rel(root, path))
    hits = {}
    for key, path in output_paths.items():
        matches = prior.get(file_sha256(path), [])
        if matches:
            hits[key] = matches
    return hits
