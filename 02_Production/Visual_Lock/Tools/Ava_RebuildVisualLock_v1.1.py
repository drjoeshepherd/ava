from PIL import Image, ImageChops, ImageEnhance, ImageDraw, ImageFont
from collections import deque
import hashlib
import json
import math
import os
import shutil

ROOT = r"C:\Users\joesh\Documents\Codex\2026-10-07\build-ava-v1-0-as-a-2"
LOCK_DIR = os.path.join(ROOT, "outputs", "visual-lock-system")
TARGET = os.path.join(LOCK_DIR, "Targets", "Ava_Target_Front.png")
TARGET_MASK_PATH = os.path.join(LOCK_DIR, "Targets", "Ava_Target_Front_Mask.png")
LANDMARK_PATH = os.path.join(LOCK_DIR, "Ava_Target_Front_Landmarks_v1.1.png")
GEOMETRY_PATH = os.path.join(LOCK_DIR, "Ava_Geometry_Lock_v1.1.json")
CHANGELOG_PATH = os.path.join(LOCK_DIR, "Ava_Geometry_Lock_v1.0_to_v1.1_Changes.md")
FIT_RENDER = os.path.join(ROOT, "outputs", "05_Renders", "Visual_Lock", "FrontFit_v01", "Front_Render_vFit01.png")
REEVAL_DIR = os.path.join(ROOT, "outputs", "05_Renders", "Visual_Lock", "FrontFit_v01_Reeval")
os.makedirs(REEVAL_DIR, exist_ok=True)

REEVAL_RENDER = os.path.join(REEVAL_DIR, "Front_vFit01_Reeval_Render.png")
REEVAL_OVERLAY = os.path.join(REEVAL_DIR, "Front_vFit01_Reeval_Overlay.png")
REEVAL_DIFFERENCE = os.path.join(REEVAL_DIR, "Front_vFit01_Reeval_Difference.png")
REEVAL_MASK = os.path.join(REEVAL_DIR, "Front_vFit01_Reeval_RenderMask.png")
REEVAL_MASK_COMPARISON = os.path.join(REEVAL_DIR, "Front_vFit01_Reeval_MaskComparison.png")
REEVAL_METRICS = os.path.join(REEVAL_DIR, "Front_vFit01_Reeval_Metrics.json")

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

target_hash_before = sha256(TARGET)
target_image = Image.open(TARGET).convert("RGB")
target_mask, target_segmentation = derive_silhouette(target_image)
save_mask(target_mask, TARGET_MASK_PATH)
target_analysis = analyze_raster(target_image, target_mask, target_segmentation)
draw_landmarks(target_image, target_analysis, LANDMARK_PATH)

geometry_v11 = {
    "schema": "Ava_Geometry_Lock_v1.1",
    "status": "RASTER_DERIVED_REVIEW_REQUIRED",
    "authority_hierarchy": [
        "Ava_Target_Front.png",
        "measurements derived mathematically from Ava_Target_Front.png",
        "canon prose and approximate design descriptions",
        "current Blender implementation",
    ],
    "source_image": {
        "file": "Targets/Ava_Target_Front.png",
        "dimensions_pixels": [WIDTH, HEIGHT],
        "sha256": target_hash_before,
        "modified": False,
    },
    "coordinate_system": {
        "pixel_origin": "top-left",
        "pixel_x": "right",
        "pixel_y": "down",
        "normalized_origin": "character bottom on raster-derived centerline",
        "normalized_x": "(pixel_x - centerline_pixel_x) / character_height_pixels",
        "normalized_y": "(bottommost_character_pixel_y - pixel_y) / character_height_pixels",
        "character_height": 1.0,
        "centerline_x": 0.0,
    },
    "proportion_rule": {
        "canonical_head_body_ratio": target_analysis["head"]["canonical_heads_tall"],
        "approximate_description": "~2.5 heads",
        "acceptance_authority": "canonical_head_body_ratio",
    },
    "silhouette_mask": {
        "file": "Targets/Ava_Target_Front_Mask.png",
        "character_value": 255,
        "background_value": 0,
        "shadow_included": False,
        "glow_included": False,
        "soft_edge_policy": "binary after border-connected background segmentation",
        "derivation": target_segmentation,
    },
    "landmarks": {key: target_analysis[key] for key in ["character", "head", "eyes", "face", "hair", "listening_modules", "torso", "arms_hands", "legs_feet"]},
    "manual_review_required": target_analysis["manual_review_required"],
    "metric_definitions": {
        "HeadBodyRatioError": "abs(render_heads_tall - target_heads_tall) / target_heads_tall",
        "EyeCenterError": "Euclidean pixel-center distance / target head maximum width",
        "EyeSizeError": "mean(abs(render_eye_width-target_eye_width)/target_eye_width, abs(render_eye_height-target_eye_height)/target_eye_height)",
        "ListeningModuleCenterError": "Euclidean pixel-center distance / target head maximum width; not evaluated until manual module annotation exists",
        "ListeningModuleDiameterError": "abs(render_diameter-target_diameter)/target_diameter; not evaluated until manual module annotation exists",
        "TorsoWidthError": "abs(render_width-target_width)/character_height; not evaluated until manual torso annotation exists",
        "HandScaleError": "mean absolute relative error of target/render hand bbox width and height",
        "ThighWidthError": "abs(render_width-target_width)/character_height; not evaluated until manual thigh annotation exists",
        "FootWidthError": "abs(render_width-target_width)/character_height; not evaluated until manual foot annotation exists",
        "SilhouetteIoU": "intersection(TargetMask, RenderMask) / union(TargetMask, RenderMask)",
    },
}
with open(GEOMETRY_PATH, "w", encoding="utf-8") as handle:
    json.dump(geometry_v11, handle, indent=2)

shutil.copyfile(FIT_RENDER, REEVAL_RENDER)
render_image = Image.open(REEVAL_RENDER).convert("RGB")
render_mask, render_segmentation = derive_silhouette(render_image)
save_mask(render_mask, REEVAL_MASK)
render_analysis = analyze_raster(render_image, render_mask, render_segmentation)
Image.blend(target_image, render_image, 0.5).save(REEVAL_OVERLAY, optimize=True)
ImageEnhance.Contrast(ImageChops.difference(target_image, render_image)).enhance(2.4).save(REEVAL_DIFFERENCE, optimize=True)

intersection = 0
union = 0
comparison = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
comparison_pixels = comparison.load()
for y in range(HEIGHT):
    for x in range(WIDTH):
        target_value = bool(target_mask[y][x])
        render_value = bool(render_mask[y][x])
        intersection += target_value and render_value
        union += target_value or render_value
        if target_value and render_value:
            comparison_pixels[x, y] = (255, 255, 255)
        elif target_value:
            comparison_pixels[x, y] = (255, 70, 70)
        elif render_value:
            comparison_pixels[x, y] = (0, 200, 255)
comparison.save(REEVAL_MASK_COMPARISON, optimize=True)
iou = intersection / union if union else 0.0

target_ratio = target_analysis["head"]["canonical_heads_tall"]["pixel_value"]
render_ratio = render_analysis["head"]["canonical_heads_tall"]["pixel_value"]
ratio_error = abs(render_ratio - target_ratio) / target_ratio

eye_center_errors = []
eye_size_errors = []
for side in ["left", "right"]:
    target_eye = target_analysis["eyes"][side]
    render_eye = render_analysis["eyes"][side]
    target_center = target_eye["eye_center"]["pixel_value"]
    render_center = render_eye["eye_center"]["pixel_value"]
    eye_center_errors.append(math.dist(target_center, render_center) / target_analysis["head"]["max_width_row"]["pixel_value"]["width"])
    target_box = target_eye["eye_bounding_box"]["pixel_value"]
    render_box = render_eye["eye_bounding_box"]["pixel_value"]
    target_width = target_box["xmax"] - target_box["xmin"] + 1
    target_height = target_box["ymax"] - target_box["ymin"] + 1
    render_width = render_box["xmax"] - render_box["xmin"] + 1
    render_height = render_box["ymax"] - render_box["ymin"] + 1
    eye_size_errors.append((abs(render_width - target_width) / target_width + abs(render_height - target_height) / target_height) / 2)

target_hands = target_analysis["arms_hands"]["hand_bounding_boxes"]
render_hands = render_analysis["arms_hands"]["hand_bounding_boxes"]
hand_errors = []
for side in ["left", "right"]:
    if measured(target_hands[side]) and measured(render_hands[side]):
        tb = target_hands[side]["pixel_value"]
        rb = render_hands[side]["pixel_value"]
        tw, th = tb["xmax"] - tb["xmin"] + 1, tb["ymax"] - tb["ymin"] + 1
        rw, rh = rb["xmax"] - rb["xmin"] + 1, rb["ymax"] - rb["ymin"] + 1
        hand_errors.append((abs(rw - tw) / tw + abs(rh - th) / th) / 2)

metrics = {
    "schema": "Ava_Front_vFit01_Reevaluation_v1.1",
    "status": "REVIEW_REQUIRED",
    "geometry_lock": "Ava_Geometry_Lock_v1.1.json",
    "target_mask": "Ava_Target_Front_Mask.png",
    "render_mask": "Front_vFit01_Reeval_RenderMask.png",
    "metrics": {
        "HeadBodyRatioError": metric("calculated", "abs(render-target)/target", target_ratio, render_ratio, ratio_error, 0.02, ratio_error <= 0.02),
        "EyeCenterError": metric("calculated", "mean Euclidean eye-center distance / target head width", [target_analysis["eyes"][s]["eye_center"]["pixel_value"] for s in ["left", "right"]], [render_analysis["eyes"][s]["eye_center"]["pixel_value"] for s in ["left", "right"]], sum(eye_center_errors) / len(eye_center_errors), 0.02, max(eye_center_errors) <= 0.02),
        "EyeSizeError": metric("calculated", "mean relative bbox width/height error", [target_analysis["eyes"][s]["eye_bounding_box"]["pixel_value"] for s in ["left", "right"]], [render_analysis["eyes"][s]["eye_bounding_box"]["pixel_value"] for s in ["left", "right"]], sum(eye_size_errors) / len(eye_size_errors), 0.03, max(eye_size_errors) <= 0.03),
        "ListeningModuleCenterError": metric("manual_review_required", "Euclidean module-center distance / target head width", None, None, None, 0.03, note="Full target circles are occluded by hair."),
        "ListeningModuleDiameterError": metric("manual_review_required", "abs(render-target)/target", None, None, None, 0.03, note="Full target outer diameters are occluded by hair."),
        "TorsoWidthError": metric("manual_review_required", "abs(render-target)/character_height", None, None, None, 0.03, note="Target torso and arm shells touch."),
        "HandScaleError": metric("calculated" if hand_errors else "manual_review_required", "mean relative hand-bbox width/height error", [bbox_value(target_hands[s]) for s in ["left", "right"]], [bbox_value(render_hands[s]) for s in ["left", "right"]], (sum(hand_errors) / len(hand_errors)) if hand_errors else None, 0.03, max(hand_errors) <= 0.03 if hand_errors else None),
        "ThighWidthError": metric("manual_review_required", "abs(render-target)/character_height", None, None, None, 0.03, note="Target thigh/pelvis boundary is occluded."),
        "FootWidthError": metric("manual_review_required", "abs(render-target)/character_height", None, None, None, 0.03, note="Target foot/shin boundary requires human annotation."),
        "SilhouetteIoU": metric("calculated", "intersection(TargetMask,RenderMask)/union(TargetMask,RenderMask)", target_segmentation["foreground_pixel_count"], render_segmentation["foreground_pixel_count"], iou, 0.90, iou >= 0.90),
    },
    "target_segmentation": target_segmentation,
    "render_segmentation": render_segmentation,
    "manual_review_required": target_analysis["manual_review_required"],
    "lock_integrity": {
        "target_sha256_before": target_hash_before,
        "target_sha256_after": sha256(TARGET),
        "target_unchanged": target_hash_before == sha256(TARGET),
    },
    "geometry_modified": False,
    "rig_modified": False,
    "animation_modified": False,
}
with open(REEVAL_METRICS, "w", encoding="utf-8") as handle:
    json.dump(metrics, handle, indent=2)

old_geometry = json.load(open(os.path.join(LOCK_DIR, "Ava_Geometry_Lock_v1.0.json"), encoding="utf-8"))
new_head_height = target_analysis["head"]["height"]["normalized_value"]
new_heads_tall = target_ratio
new_eye_centers = [target_analysis["eyes"][side]["eye_center"]["normalized_value"] for side in ["left", "right"]]
new_eye_boxes = [target_analysis["eyes"][side]["eye_bounding_box"]["normalized_value"] for side in ["left", "right"]]
changelog = f"""# Ava Geometry Lock v1.0 → v1.1 Changes

## Authority repair

Version 1.1 is derived directly from `Ava_Target_Front.png`. It does not reuse conflicting v1.0 numeric geometry. The canonical raster now overrides v1.0, the approximate `~2.5 heads` prose, and the Blender implementation.

The canonical image SHA-256 remains `{target_hash_before}`.

## Replaced values

| Measurement | v1.0 value | v1.1 raster-derived value | Resolution |
|---|---:|---:|---|
| Head height / character height | `{old_geometry['proportion_lock']['head_height']}` | `{new_head_height:.9f}` ({target_analysis['head']['height']['pixel_value']} px) | Replaced with mask-derived head contraction boundary. |
| Heads tall | `{old_geometry['proportion_lock']['target_heads_tall']}` | `{new_heads_tall:.9f}` | Exact raster ratio replaces approximate prose. |
| Image-left eye center | `{old_geometry['face']['eye_center_L']}` | `{new_eye_centers[0]}` | Replaced with local eye-feature bbox center. |
| Image-right eye center | `{old_geometry['face']['eye_center_R']}` | `{new_eye_centers[1]}` | Replaced with local eye-feature bbox center. |
| Eye bounds | width `{old_geometry['face']['eye_width']}`, height `{old_geometry['face']['eye_height']}` | left `{new_eye_boxes[0]}`, right `{new_eye_boxes[1]}` | Replaced with raster feature bounds. |
| Listening-module center/diameter | centers `{old_geometry['listening_modules']['center_L']}`, `{old_geometry['listening_modules']['center_R']}`; diameter `{old_geometry['listening_modules']['outer_diameter']}` | `manual_review_required` | Full circles are occluded by hair; v1.0 exact values were unsupported. |
| Torso/waist/pelvis exact widths | v1.0 numeric estimates | `manual_review_required` | Touching/overlapping raster shells prevent unambiguous isolation. |
| Joint centers and segment lengths | v1.0 numeric estimates | `manual_review_required` | Joint centers are visually occluded and cannot be stored as exact raster measurements. |
| Foot dimensions | v1.0 numeric estimates | `manual_review_required` | Foot/shin boundary and floor contact require human annotation. |

## Metric changes

- Silhouette comparison now uses `Ava_Target_Front_Mask.png` against `Front_vFit01_Reeval_RenderMask.png`; RGB difference is not used for IoU.
- Eye-center error is normalized by raster-derived head width.
- Eye-size error is normalized independently by target eye width and height.
- Body landmark errors use canonical character height.
- Ambiguous targets have no pass/fail result.

## Remaining human review

""" + "\n".join(f"- `{item}`" for item in target_analysis["manual_review_required"]) + "\n"
with open(CHANGELOG_PATH, "w", encoding="utf-8") as handle:
    handle.write(changelog)

print(json.dumps({
    "geometry_lock": GEOMETRY_PATH,
    "target_mask": TARGET_MASK_PATH,
    "landmarks": LANDMARK_PATH,
    "changelog": CHANGELOG_PATH,
    "reeval_metrics": REEVAL_METRICS,
    "silhouette_iou": iou,
    "target_unchanged": target_hash_before == sha256(TARGET),
    "manual_review_count": len(target_analysis["manual_review_required"]),
}, indent=2))
