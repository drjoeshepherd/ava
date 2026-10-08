"""Canonical-vs-render regional crops for human visual review.

Created by AVA-FIT-FRONT-02.

    py 02_Production/Visual_Lock/Tools/Ava_RegionCompare.py --render <png> --out <dir> [--prefix Canon_vs_Render_]

LEFT = canonical raster (Targets/Ava_Target_Front.png, checksum-verified), RIGHT = the supplied
CAM_CANON_FRONT render. Both images share the locked 600x800 camera framing, so each region uses the
same pixel box on both sides (same scale and framing). Crops are enlarged with nearest-neighbour
resampling only; no image content is regenerated or retouched.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Ava_VisualLock_Common as common  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

# Pixel boxes (x0, y0, x1, y1) in the locked 600x800 front frame.
REGIONS = {
    "Hair": (55, 25, 535, 365),
    "Eyes": (165, 185, 435, 325),
    "Face": (150, 110, 450, 365),
    "ListeningModule": (50, 150, 200, 330),
    "Torso": (180, 325, 420, 565),
    "Hand": (45, 470, 175, 605),
    "Hip": (150, 430, 450, 630),
    "Foot": (135, 575, 465, 755),
}
TARGET_WIDTH = 900


def font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def compare(target, render, box, title):
    a, b = target.crop(box), render.crop(box)
    scale = max(1, round(TARGET_WIDTH / 2 / a.width))
    a = a.resize((a.width * scale, a.height * scale), Image.NEAREST)
    b = b.resize((b.width * scale, b.height * scale), Image.NEAREST)
    gap, header = 12, 34
    canvas = Image.new("RGB", (a.width * 2 + gap, a.height + header), (255, 255, 255))
    canvas.paste(a, (0, header))
    canvas.paste(b, (a.width + gap, header))
    draw = ImageDraw.Draw(canvas)
    f = font(16)
    draw.text((8, 8), "LEFT: canonical raster", fill=(0, 0, 0), font=f)
    draw.text((a.width + gap + 8, 8), "RIGHT: Blender render", fill=(0, 0, 0), font=f)
    draw.text((canvas.width - 8 - draw.textlength(title, font=f), 8), title, fill=(110, 110, 110), font=f)
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prefix", default="Canon_vs_Render_")
    parser.add_argument("--regions", default=",".join(REGIONS))
    args = parser.parse_args()
    root = common.find_repo_root()
    paths = common.repo_paths(root)
    common.verify_manifest(paths)
    target = Image.open(paths["target_front"]).convert("RGB")
    render = Image.open(args.render).convert("RGB")
    if render.size != target.size:
        sys.exit("Render size %s differs from canonical %s." % (render.size, target.size))
    os.makedirs(args.out, exist_ok=True)
    for name in args.regions.split(","):
        path = os.path.join(args.out, "%s%s.png" % (args.prefix, name))
        compare(target, render, REGIONS[name], name).save(path, optimize=True)
        print(path)


if __name__ == "__main__":
    main()
