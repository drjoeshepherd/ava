"""PROPOSED eye-anatomy measurement (EyeMeasurement vNext). Created by AVA-FIT-FRONT-03.

Status: PROPOSAL. It does not replace Ava_ValidateFront.py or Ava_Front_Acceptance_Gates_v1.0.json,
which stay unchanged and keep reporting the v1.0 EyeSize/EyeCenter results.

    py 02_Production/Visual_Lock/Tools/Ava_EyeAnatomy_vNext.py --render <png> [--render <png> ...]
        [--label <name> ...] --out <json> [--viz-dir <dir>]

Measures the SAME features, with the SAME code, on the canonical raster and on each render:

  iris        connected amber component (detector shared with Ava_VisualLock_Common.analyze_raster)
              - diameter = horizontal width of the amber component (the upper iris is lid-occluded in
                the canonical raster, so its vertical extent is not an anatomical measurement)
              - centre   = centre of a circle of that diameter tangent to the lowest amber row
  pupil       centroid of pixels with luminance < 70 inside the amber bounding box
  upper lash  dark pixels (luminance < 95) above the iris centre and outside the fitted iris circle,
              connected, area >= 20, within +/- 2 iris diameters -> bounding box
  opening     x from the lash bounds, y from the lash top to the lowest amber row (the canonical iris
              meets the lower lid; the canonical lower lid is skin-toned, so it is deliberately not read)
  symmetry    left/right iris-diameter ratio

None of these features reads skin colour, blush, cheek warmth, under-eye shading or a socket outline:
skin pixels are never classified as eye features (amber/dark/neutral-grey tests only, with chroma caps).
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Ava_VisualLock_Common as common  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

VERSION = "vNext-0.1-PROPOSED"
GATES = "Ava_Front_EyeAnatomy_Gates_vNext_PROPOSED.json"


def lum(c):
    return common.luminance(c)


def components(points, min_area):
    pts = set(points)
    out = []
    while pts:
        seed = pts.pop()
        stack, comp = [seed], [seed]
        while stack:
            x, y = stack.pop()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1), (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
                if n in pts:
                    pts.remove(n)
                    stack.append(n)
                    comp.append(n)
        if len(comp) >= min_area:
            out.append(comp)
    return out


def bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def measure(path):
    image = Image.open(path).convert("RGB")
    px = image.load()
    mask, seg = common.derive_silhouette(image)
    analysis = common.analyze_raster(image, mask, seg)
    head = analysis["head"]
    head_width = head["max_width_row"]["pixel_value"]["width"]
    eyes = {}
    for side in ("left", "right"):
        e = analysis["eyes"][side]
        iris_box = e["iris_diameter"]  # width/height of the amber component
        cx_c, cy_c = e["iris_center"]["pixel_value"]
        w = iris_box["pixel_value"]["width"]
        # amber bounding box from the old analysis record
        # recompute the amber component bounds directly (same detector as common.analyze_raster)
        ax0, ax1 = round(cx_c - w), round(cx_c + w)
        amber = [(x, y) for y in range(max(0, round(cy_c) - 60), min(799, round(cy_c) + 60))
                 for x in range(max(0, ax0 - 10), min(599, ax1 + 10))
                 if (lambda c: c[0] > 112 and 38 < c[1] < 210 and c[2] < 122 and c[0] > c[1] * 1.12 and c[1] > max(1, c[2]) * 1.15)(px[x, y])]
        comps = components(amber, 20)
        comp = max(comps, key=lambda c: (len(c) if any(abs(p[0] - cx_c) < 3 and abs(p[1] - cy_c) < 3 for p in c) else 0, len(c)))
        a0x, a0y, a1x, a1y = bbox(comp)
        diam = a1x - a0x + 1
        icx, icy = (a0x + a1x) / 2, a1y - diam / 2 + 0.5
        pupil = [(x, y) for y in range(a0y, a1y + 1) for x in range(a0x, a1x + 1) if lum(px[x, y]) < 70]
        pupil_c = [sum(p[0] for p in pupil) / len(pupil), sum(p[1] for p in pupil) / len(pupil)] if pupil else None
        # upper lash: dark pixels above the iris centre and outside the fitted iris circle (so the dark
        # upper iris and pupil are never counted), within +/- 2 iris diameters horizontally
        r = diam / 2
        wx0, wx1, wy0 = round(icx - 2 * r), round(icx + 2 * r), round(icy - 2.2 * r)
        dark = [(x, y) for y in range(max(0, wy0), round(icy) + 1) for x in range(max(0, wx0), min(599, wx1) + 1)
                if lum(px[x, y]) < 95 and math.dist((x, y), (icx, icy)) > r + 1.5]
        lash_comps = [c for c in components(dark, 20)]
        lash = bbox([p for c in lash_comps for p in c]) if lash_comps else None
        # opening: lash corners and lash top down to the lowest iris row (the iris meets the lower lid in
        # the canonical raster; the lid itself is skin-toned there, so it is deliberately not read)
        opening = [lash[0], lash[1], lash[2], a1y] if lash else None
        eyes[side] = {
            "iris_amber_bbox": [a0x, a0y, a1x, a1y],
            "iris_diameter_px": diam,
            "iris_center_px": [icx, icy],
            "pupil_center_px": pupil_c,
            "upper_lash_bbox": lash,
            "opening_bbox": opening,
        }
    return {"image": path, "head_width_px": head_width, "head_height_px": head["height"]["pixel_value"], "eyes": eyes,
            "old_eye_bounding_box": {s: analysis["eyes"][s]["eye_bounding_box"]["pixel_value"] for s in ("left", "right")}}


def wh(b):
    return b[2] - b[0] + 1, b[3] - b[1] + 1


def compare(target, render, gates):
    hw = target["head_width_px"]
    per = {}
    for side in ("left", "right"):
        t, r = target["eyes"][side], render["eyes"][side]
        m = {}
        m["IrisCenterError"] = math.dist(t["iris_center_px"], r["iris_center_px"]) / hw
        m["IrisDiameterError"] = abs(r["iris_diameter_px"] - t["iris_diameter_px"]) / t["iris_diameter_px"]
        m["PupilCenterError"] = math.dist(t["pupil_center_px"], r["pupil_center_px"]) / hw if t["pupil_center_px"] and r["pupil_center_px"] else None
        if t["upper_lash_bbox"] and r["upper_lash_bbox"]:
            tw, th = wh(t["upper_lash_bbox"]); rw, rh = wh(r["upper_lash_bbox"])
            m["UpperLashSpanError"] = abs(rw - tw) / tw
            m["UpperLashTopError"] = abs(r["upper_lash_bbox"][1] - t["upper_lash_bbox"][1]) / hw
        else:
            m["UpperLashSpanError"] = m["UpperLashTopError"] = None
        if t["opening_bbox"] and r["opening_bbox"]:
            tw, th = wh(t["opening_bbox"]); rw, rh = wh(r["opening_bbox"])
            m["EyeOpeningSizeError"] = (abs(rw - tw) / tw + abs(rh - th) / th) / 2
            tc = [(t["opening_bbox"][0] + t["opening_bbox"][2]) / 2, (t["opening_bbox"][1] + t["opening_bbox"][3]) / 2]
            rc = [(r["opening_bbox"][0] + r["opening_bbox"][2]) / 2, (r["opening_bbox"][1] + r["opening_bbox"][3]) / 2]
            m["EyeOpeningCenterError"] = math.dist(tc, rc) / hw
        else:
            m["EyeOpeningSizeError"] = m["EyeOpeningCenterError"] = None
        per[side] = m
    tr = target["eyes"]["left"]["iris_diameter_px"] / target["eyes"]["right"]["iris_diameter_px"]
    rr = render["eyes"]["left"]["iris_diameter_px"] / render["eyes"]["right"]["iris_diameter_px"]
    results = {}
    for name, g in gates["gates"].items():
        if name == "IrisSymmetryError":
            value = abs(rr - tr) / tr
            results[name] = {"value": value, "threshold": g["threshold"], "pass": value <= g["threshold"], "target_ratio": tr, "render_ratio": rr}
            continue
        vals = [per[s][name] for s in ("left", "right")]
        if any(v is None for v in vals):
            results[name] = {"value": None, "pass": False, "note": "feature not detected"}
            continue
        results[name] = {"per_eye": dict(zip(("left", "right"), vals)), "value": max(vals), "threshold": g["threshold"],
                         "pass": max(vals) <= g["threshold"]}
    return results, all(r["pass"] for r in results.values())


def visualize(meas, path):
    im = Image.open(meas["image"]).convert("RGB")
    d = ImageDraw.Draw(im)
    for e in meas["eyes"].values():
        if e["opening_bbox"]:
            d.rectangle(e["opening_bbox"], outline=(0, 160, 255), width=1)
        if e["upper_lash_bbox"]:
            d.rectangle(e["upper_lash_bbox"], outline=(255, 0, 200), width=1)
        cx, cy = e["iris_center_px"]; rr = e["iris_diameter_px"] / 2
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(0, 220, 0), width=1)
        if e["pupil_center_px"]:
            x, y = e["pupil_center_px"]; d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 0, 0))
    im.crop((160, 180, 440, 330)).resize((840, 450), Image.NEAREST).save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="append", required=True)
    parser.add_argument("--label", action="append")
    parser.add_argument("--out", required=True)
    parser.add_argument("--viz-dir")
    args = parser.parse_args()
    root = common.find_repo_root()
    paths = common.repo_paths(root)
    manifest = common.verify_manifest(paths)
    gates = common.load_json(os.path.join(paths["visual_lock"], GATES))
    target = measure(paths["target_front"])
    out = {"schema": "Ava_EyeAnatomy_Measurement", "version": VERSION, "status": "PROPOSAL_NOT_APPROVED",
           "gate_file": {"file": GATES, "sha256": common.file_sha256(os.path.join(paths["visual_lock"], GATES))},
           "tool_sha256": common.file_sha256(os.path.abspath(__file__)),
           "canonical_raster_sha256": common.file_sha256(paths["target_front"]), "manifest_all_match": manifest["all_match"],
           "target": target, "renders": {}}
    labels = args.label or [os.path.basename(p) for p in args.render]
    if args.viz_dir:
        os.makedirs(args.viz_dir, exist_ok=True)
        visualize(target, os.path.join(args.viz_dir, "EyeAnatomy_canonical.png"))
    for label, render in zip(labels, args.render):
        meas = measure(render)
        results, ok = compare(target, meas, gates)
        out["renders"][label] = {"measurement": meas, "results": results, "all_pass": ok}
        if args.viz_dir:
            visualize(meas, os.path.join(args.viz_dir, "EyeAnatomy_%s.png" % label))
        print(label, "ALL_PASS" if ok else "FAIL", {k: round(v["value"], 4) if v.get("value") is not None else None for k, v in results.items()})
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2)


if __name__ == "__main__":
    main()
