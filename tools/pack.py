"""Packs every PixelLab frame in art/raw/ into one atlas: game/atlas.png + game/atlas.json.

Each animation is trimmed to the union of its frames, and each frame keeps its offset from the sprite's anchor
(feet for bodies, the water line for a swimming head, the pivot for effects), so the game draws every frame at
x + ox, y + oy and nothing jitters.
"""
import json, os, glob, re
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RAW = os.path.join(ROOT, "art", "raw")


SHRINK = {"gull_flap": 0.6,  # the flying gull came out bigger than the perched one; bring it to the same size
          "chipper": 0.85, "drone_fly": 0.85,  # small enough that a drone can drop a seal in without leaving the screen
          "ball_red": 0.84, "gundrone": 0.7}


def drop_edge_scraps(im):
    """An edited animation is drawn as one grid, so a weapon that pokes past its cell leaves a sliver in the next one,
    or a cut-off scrap floating at the edge. Drop any piece not joined to the hunter that touches the left or right edge."""
    w, h = im.size
    a = im.getchannel("A").load()
    seen, pieces = set(), []
    for y in range(h):
        for x in range(w):
            if a[x, y] and (x, y) not in seen:
                stack, px = [(x, y)], []
                seen.add((x, y))
                while stack:
                    cx, cy = stack.pop()
                    px.append((cx, cy))
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and a[nx, ny]:
                                seen.add((nx, ny))
                                stack.append((nx, ny))
                pieces.append(px)
    pieces.sort(key=len, reverse=True)
    out = im.copy()
    for px in pieces[1:]:
        xs = [p[0] for p in px]
        if len(px) < 120 and (min(xs) <= 1 or max(xs) >= w - 2):
            for p in px:
                out.putpixel(p, (0, 0, 0, 0))
    return out


def frames_of(name):
    out = [Image.open(p).convert("RGBA") for p in sorted(glob.glob(os.path.join(RAW, name, "[0-9][0-9].png")))]
    if name.startswith("hw_"):
        out = [drop_edge_scraps(f) for f in out[:9]]   # an edited animation comes back twice; the second copy is identical
    k = SHRINK.get(name)
    if k:
        out = [f.resize((round(f.width * k), round(f.height * k)), Image.NEAREST) for f in out]
    return out


def vfx_frames(name):
    sheet = Image.open(os.path.join(RAW, name, "01.png")).convert("RGBA")
    meta = json.load(open(os.path.join(RAW, name, "02.json")))
    out, durs = [], []
    for f in meta["frames"]:
        r = f["frame"]
        out.append(sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])))
        durs.append(f.get("duration", 83))
    if name == "vfx_flamejet":   # it came with a black smoke ball on the end that reads as a cannonball; burn it off
        for im in out:
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    r, g, b, a = px[x, y]
                    if a and r * .3 + g * .59 + b * .11 < 90:
                        px[x, y] = (0, 0, 0, 0)
    piv = meta["frames"][0].get("pivot", {"x": 0.5, "y": 0.5})
    return out, (round(piv["x"] * out[0].width), round(piv["y"] * out[0].height)), durs


def bottom_center(im):
    b = im.getbbox()
    return ((b[0] + b[2]) // 2, b[3] - 1)


# name: (raw folder, anchor or None for bottom-centre of the first frame, kind)
ANIMS = {
    "seal_idle": ("seal_idle", (32, 53)), "seal_scoot": ("seal_scoot", (32, 53)), "seal_hop": ("seal_hop", (32, 53)),
    "seal_hurt": ("seal_hurt", (32, 53)), "seal_ko": ("seal_ko", (32, 53)), "seal_roll": ("seal_roll", (32, 53)),
    "seal_look": ("seal_look", (32, 53)), "seal_swim": ("seal_swim", (24, 26)),
    "hunter_idle": ("hunter_idle", (35, 81)), "hunter_walk": ("hunter_walk", (35, 81)),
    "hunter_swing": ("hunter_swing", (35, 81)), "hunter_cheer": ("hunter_cheer", (35, 81)),
    "gull_idle": ("gull_idle", (24, 46)), "gull_fly": ("gull_flap", (24, 26)),
    "husky_idle": ("husky_idle", (24, 45)), "husky_run": ("husky_run", (24, 40)),
    "drone": ("drone_fly", (24, 40)),
    # the mutants and the two bosses stand on their feet (None: the bottom centre of the first frame)
    "mut_frog": ("a_frog", None), "mut_bat": ("a_bat", None), "mut_bloat": ("a_bloat", None),
    "mut_kraken": ("a_kraken", None), "mut_mama": ("a_mama2", None), "mut_thulu": ("a_thulu", None),
    "hunter_idle_empty": ("hw_empty_idle", (35, 77)), "hunter_walk_empty": ("hw_empty_walk", (35, 77)),   # hands free for a gun that turns
}
for w in ("salmon", "bone", "anchor", "tusk"):   # the hunter with each club, cut from 80x80 crops of the 96x84 frames
    ANIMS[f"hunter_idle_{w}"] = (f"hw_{w}_idle", (35, 77))
    ANIMS[f"hunter_walk_{w}"] = (f"hw_{w}_walk", (35, 77))
    ANIMS[f"hunter_swing_{w}"] = (f"hw_{w}_swing", (26, 77))
for w in ("harpoon", "flamer"):                    # and with each gun, for the sealocalypse
    ANIMS[f"hunter_idle_{w}"] = (f"hw_{w}_idle", (35, 77))
    ANIMS[f"hunter_walk_{w}"] = (f"hw_{w}_walk", (35, 77))
STILLS = {
    "sled": "sled_iso", "pelt": "pelt", "husky": "husky", "splat": "splat_b", "drop": "splat_d", "pool": "pool2",
    "gull": "gull_iso", "chipper": "chipper", "hook": "hook", "decoy": "decoy2",
    "contraption1": "contraption1", "contraption2": "contraption2", "contraption3": "contraption3",
    "ball_red": "ball_red", "ball_cream": "ball_cream", "nozzle": "nozzle", "sludge": "sludge", "deadfish": "deadfish",
    "barrel": "barrel", "heart_full": "heart_full", "heart_empty": "heart_empty", "harpoon": "harpoon_bolt",
    "orb": "boss_orb", "tongue": "tongue2", "gundrone": "gundrone",
    "gun_harpoon": "gun_harpoon", "gun_flamer": "gun_flamer", "wreck": "wreck",
}
# where each machine stands or hangs from: the factory and chipper by their feet, the hook by its eye
ANCHOR = {"factory": (48, 89), "chipper": (30, 59), "hook": (8, 1), "contraption1": (48, 90), "contraption2": (48, 90), "contraption3": (48, 90),
          "gun_harpoon": (10, 18), "gun_flamer": (11, 19)}   # each gun turns about its grip
ICONS = ["icon_seal", "icon_club", "icon_sled2", "icon_decoy3", "icon_bucket", "icon_sun", "icon_moon", "icon_fish",
         "icon_coin", "icon_drone", "icon_factory3", "icon_husky", "icon_salmon", "icon_bone2", "icon_anchor", "icon_tusk2",
         "icon_harpoon", "icon_flamer", "icon_gundrone", "icon_heartup", "icon_parka", "icon_goo"]
VFX = ["vfx_blood", "vfx_bonk", "vfx_splash", "vfx_poof", "vfx_sparkle", "vfx_flame", "vfx_toxic", "vfx_acid", "vfx_flamejet"]


def main():
    entries = {}  # name -> list of (image, ox, oy), extra
    for name, (folder, anchor) in ANIMS.items():
        fr = frames_of(folder)
        if not fr:
            print("missing", folder)
            continue
        k = SHRINK.get(folder, 1)
        if anchor is None:
            anchor = bottom_center(fr[0]); k = 1
        entries[name] = ([(f, (round(anchor[0] * k), round(anchor[1] * k))) for f in fr], {})
    for name, folder in STILLS.items():
        fr = frames_of(folder)[:1]
        if not fr:
            print("missing", folder)
            continue
        im = fr[0]
        b = im.getbbox()
        k = SHRINK.get(folder, 1)
        anchor = tuple(round(v * k) for v in ANCHOR[name]) if name in ANCHOR else (bottom_center(im) if name in ("sled", "husky", "gull", "decoy", "nozzle", "barrel", "gundrone", "wreck") else ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2))
        entries[name] = ([(im, anchor)], {})
    for name in ICONS:
        fr = frames_of(name)[:1]
        if fr:
            entries[re.sub(r"\d+$", "", name.replace("icon_", "i_"))] = ([(fr[0], (0, 0))], {"icon": True})
    for name in VFX:
        if not os.path.exists(os.path.join(RAW, name, "02.json")):
            print("missing", name)
            continue
        fr, piv, durs = vfx_frames(name)
        entries[name.replace("vfx_", "fx_")] = ([(f, piv) for f in fr], {"dur": durs})

    # trim each animation to the union bbox of its frames
    pieces, meta = [], {}
    for name, (frames, extra) in entries.items():
        if extra.get("icon"):
            box = (0, 0) + frames[0][0].size
        else:
            box = None
            for im, _ in frames:
                b = im.getbbox()
                if b:
                    box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        ax, ay = frames[0][1]
        meta[name] = {"ox": box[0] - ax, "oy": box[1] - ay, "w": box[2] - box[0], "h": box[3] - box[1], "f": []}
        meta[name].update({k: v for k, v in extra.items() if k != "icon"})
        for im, _ in frames:
            pieces.append((name, im.crop(box)))

    # shelf pack, tallest first
    W = 512
    order = sorted(range(len(pieces)), key=lambda i: -pieces[i][1].height)
    x = y = shelf = 0
    places = {}
    for i in order:
        im = pieces[i][1]
        if x + im.width > W:
            x, y, shelf = 0, y + shelf + 1, 0
        places[i] = (x, y)
        x += im.width + 1
        shelf = max(shelf, im.height)
    H = y + shelf + 1
    atlas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, (name, im) in enumerate(pieces):
        px, py = places[i]
        atlas.alpha_composite(im, (px, py))
        meta[name]["f"].append([px, py])
    os.makedirs(os.path.join(ROOT, "game"), exist_ok=True)
    atlas.save(os.path.join(ROOT, "game", "atlas.png"), optimize=True)
    json.dump(meta, open(os.path.join(ROOT, "game", "atlas.json"), "w"), separators=(",", ":"))
    print("atlas %dx%d, %d sprites, %d frames" % (W, H, len(meta), len(pieces)))


if __name__ == "__main__":
    main()
