"""Renders approximate previews of every page (annunciators shown lit).

    python3 common/preview.py pmdg737 [<PilotsDeck>/Plugin]   -> dist/previews/pmdg737/*.png
"""
import importlib.util
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import images

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIRCRAFT = sys.argv[1]
PD_IMAGES = sys.argv[2] if len(sys.argv) > 2 else None   # path to PilotsDeck Plugin folder (optional)
_spec = importlib.util.spec_from_file_location("build", os.path.join(ROOT, AIRCRAFT, "build.py"))
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)
OUT = os.path.join(build.DIST, "previews", AIRCRAFT)
IMG_DIR = build.A.strip("/").split("/")[-1]
K, GAP = 96, 8
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def load(path, gen_dir):
    if path.startswith(f"Images/{IMG_DIR}/"):
        p = os.path.join(gen_dir, os.path.basename(path))
    elif PD_IMAGES:
        p = os.path.join(PD_IMAGES, path)
    else:
        return None
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


def rect(r):
    x, y, w, h = [float(v) for v in r.split(";")]
    s = K / 72
    return int(x * s), int(y * s), int(w * s), int(h * s)


def text(d, xy, t, size, color, font=FB, anchor="mm"):
    f = ImageFont.truetype(font, size)
    d.multiline_text(xy, t, font=f, fill=color, anchor=anchor, align="center", spacing=1)


def render_key(a, page_imgs, gen_dir):
    tile = Image.new("RGBA", (K, K), (0, 0, 0, 255))
    d = ImageDraw.Draw(tile)
    st = (a.get("States") or [{}])[0]
    uuid_ = a["UUID"]
    title = st.get("Title", "")
    if uuid_.endswith("backtoparent"):
        text(d, (K / 2, K / 2), "◄ BACK", 14, "#ffffff")
        return tile
    if uuid_.endswith("openchild"):
        img = page_imgs.get(st.get("Image", "").replace("Images/", ""))
        if img:
            tile.alpha_composite(img.resize((K, K)))
        text(d, (K / 2, K - 14), title, 13, "#ffffff")
        return tile
    s = a["Settings"].get("settingsModel")
    if s is None:  # composite action (GSX)
        text(d, (K / 2, K / 2), title or "GSX", 11, "#ffffff")
        return tile
    bg = load(s["DefaultImage"], gen_dir)
    if bg:
        tile.alpha_composite(bg.resize((K, K)))
    if uuid_.endswith("switch.korry"):
        for show, img, r in ((s["ShowTopImage"], s["TopImage"], s["TopRect"]),
                             (s["ShowBotImage"], s["BotImage"], s["BotRect"])):
            if show:
                im = load(img, gen_dir)
                if im:
                    x, y, w, h = rect(r)
                    tile.alpha_composite(im.resize((w, h)), (x, y))
    elif uuid_.endswith("switch.display"):
        im = load(s["OnImage"], gen_dir)
        if im:
            tile.alpha_composite(im.resize((K, K)))
    elif uuid_.endswith("display.switch"):
        sample = s["ValueMappings"].split(":")[0].split("=")[-1] if s["ValueMappings"] else "888"
        if s["Address"].startswith("lua:") or "FREQ" in s["Address"] or "TRANSPONDER" in s["Address"]:
            sample = {"ZULU_CLOCK": "13:07Z", "MCP_ALT": "10000", "MCP_VS": "-1200", "MCP_SPD": "250"}.get(
                s["Address"].split(":")[-1], "7000" if "TRANSPONDER" in s["Address"] else "000")
        if "KOHLSMAN" in s["Address"]:
            sample = "29.92"
        if s["DrawBox"]:
            d.rectangle([12, 30, K - 12, K - 10], outline="#ffffff", width=2)
            text(d, (K / 2, 52 + 8), sample, 16, s["FontColor"])
        else:
            text(d, (K / 2, 58), sample, 20, s["FontColor"], font=FM)
    elif uuid_.endswith("display.radio"):
        text(d, (K / 2, 24), "118.000", 17, "#ffb000", font=FM)
        text(d, (K / 2, 72), "121.500", 15, "#e0e0e0", font=FM)
        return tile
    if st.get("ShowTitle", True) and title:
        align = st.get("TitleAlignment", "middle")
        y = {"top": 10 + 6 * title.count("\n"), "middle": K / 2, "bottom": K - 12 - 6 * title.count("\n")}[align]
        text(d, (K / 2, y), title, max(9, int(st.get("FontSize", 11) * 1.25)), "#ffffff")
    return tile


def main():
    gen_dir = os.path.join(build.DIST, "_gen_" + AIRCRAFT)
    images.write_annunciators(gen_dir)
    main_page, pages = build.build_pages()
    os.makedirs(OUT, exist_ok=True)
    for p in pages:
        W, H = 8 * K + 9 * GAP, 4 * K + 5 * GAP + 30
        sheet = Image.new("RGBA", (W, H), (45, 45, 48, 255))
        d = ImageDraw.Draw(sheet)
        text(d, (GAP, 16), p.name, 16, "#ffffff", anchor="lm")
        for r in range(4):
            for c in range(8):
                x, y = GAP + c * (K + GAP), 30 + GAP + r * (K + GAP)
                a = p.actions.get(f"{c},{r}")
                tile = render_key(a, p.images, gen_dir) if a else Image.new("RGBA", (K, K), (20, 20, 20, 255))
                mask = Image.new("L", (K, K), 0)
                ImageDraw.Draw(mask).rounded_rectangle([0, 0, K - 1, K - 1], 12, fill=255)
                sheet.paste(tile, (x, y), mask)
        sheet.convert("RGB").save(os.path.join(OUT, f"{p.name.replace(' ', '_')}.png"))
    import shutil
    shutil.rmtree(gen_dir)
    print("previews ->", OUT)


if __name__ == "__main__":
    main()
