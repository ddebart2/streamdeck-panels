"""Generates the annunciator sub-images and folder icons used by the profile."""
import os
import random
import string

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

AMBER, BLUE, GREEN, WHITE, RED = "#ffb000", "#3fa9f5", "#33dd55", "#f0f0f0", "#ff3030"

# name: (text, color)  - 54x20 sub-images for the Korry Button (plus @2x)
ANNUNCIATORS = {
    "LOW-PRESS": ("LOW\nPRESSURE", AMBER),
    "OFF-BUS": ("OFF BUS", BLUE),
    "SOURCE-OFF": ("SOURCE\nOFF", BLUE),
    "XFR-BUS-OFF": ("TRANSFER\nBUS OFF", AMBER),
    "VALVE-OPEN": ("VALVE\nOPEN", BLUE),
    "COWL-VALVE": ("COWL\nVALVE OPEN", BLUE),
    "OVERHEAT": ("OVERHEAT", AMBER),
    "ON-GREEN": ("ON", GREEN),
    "MA": ("MA", GREEN),
    "ON-WHITE": ("ON", WHITE),
    "OFF-AMBER": ("OFF", AMBER),
    "TRIP-OFF": ("TRIP OFF", AMBER),
    "GRD-AVAIL": ("GRD POWER\nAVAILABLE", BLUE),
    "APU-FAULT": ("FAULT", AMBER),
    "STBY-OFF": ("STBY PWR\nOFF", AMBER),
    "YAW-DAMPER": ("YAW\nDAMPER", AMBER),
    "ARMED": ("ARMED", GREEN),
    "PARK-BRAKE": ("PARK\nBRAKE", RED),
    "DOOR-OPEN": ("OPEN", AMBER),
    "AP-DISC": ("A/P", RED),
    "AT-DISC": ("A/T", RED),
    "FMC": ("FMC", AMBER),
    "LOW-QTY": ("LOW\nQUANTITY", AMBER),
    "ALIGN": ("ALIGN", WHITE),
    "FAULT": ("FAULT", AMBER),
    "ON-DC": ("ON DC", AMBER),
    "TAKEOFF-CFG": ("TAKEOFF\nCONFIG", RED),
    "CAB-ALT": ("CABIN\nALTITUDE", RED),
    "BELOW-GS": ("BELOW\nG/S", AMBER),
    "EXTENDED": ("EXTENDED", GREEN),
    "FIRE": ("FIRE", RED),
    "SPDBRK-EXT": ("SPEED BRAKE\nEXTENDED", AMBER),
    "SPDBRK-DNA": ("DO NOT\nARM", AMBER),
    "AUTOBRK-DISARM": ("AUTO BRAKE\nDISARM", AMBER),
    "NOT-ARMED": ("NOT\nARMED", AMBER),
}


def _fit_font(draw, text, w, h, max_size):
    size = max_size
    while size > 5:
        font = ImageFont.truetype(FONT, size)
        box = draw.multiline_textbbox((0, 0), text, font=font, spacing=1, align="center")
        if box[2] - box[0] <= w and box[3] - box[1] <= h:
            return font, box
        size -= 1
    return font, box


def annunciator(text, color, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines = text.count("\n") + 1
    font, box = _fit_font(d, text, w - 2, h - 2, int(h * (0.8 if lines == 1 else 0.45)))
    x = (w - (box[2] - box[0])) / 2 - box[0]
    y = (h - (box[3] - box[1])) / 2 - box[1]
    d.multiline_text((x, y), text, font=font, fill=color, spacing=1, align="center")
    return im


def write_annunciators(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, (text, color) in ANNUNCIATORS.items():
        annunciator(text, color, 54, 20).save(os.path.join(out_dir, f"{name}.png"))
        annunciator(text, color, 108, 40).save(os.path.join(out_dir, f"{name}@2x.png"))


def folder_icon(kind="folder", size=144):
    """Dark tile with a blue outline glyph (title is drawn by the Stream Deck)."""
    im = Image.new("RGBA", (size, size), (14, 22, 44, 255))
    d = ImageDraw.Draw(im)
    blue = (70, 140, 255, 255)
    s = size / 144
    d.rounded_rectangle([2 * s, 2 * s, size - 3 * s, size - 3 * s], radius=18 * s,
                        outline=(40, 60, 100, 255), width=int(3 * s))
    if kind == "folder":
        d.rectangle([44 * s, 30 * s, 104 * s, 80 * s], outline=blue, width=int(5 * s))
        d.rectangle([34 * s, 40 * s, 94 * s, 90 * s], fill=(14, 22, 44, 255), outline=blue,
                    width=int(5 * s))
        for i in range(3):
            d.rectangle([(48 + i * 14) * s, 74 * s, (56 + i * 14) * s, 82 * s], fill=blue)
    else:  # phase tile
        d.ellipse([46 * s, 22 * s, 98 * s, 74 * s], outline=blue, width=int(5 * s))
        d.line([72 * s, 48 * s, 72 * s, 30 * s], fill=blue, width=int(5 * s))
        d.line([72 * s, 48 * s, 86 * s, 56 * s], fill=blue, width=int(5 * s))
    return im


def sd_image_name():
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(26)) + "Z.png"
