"""Builds the PMDG 737 Stream Deck XL profile package (.ppp) for PilotsDeck.

    python3 pmdg737/build.py            -> dist/PMDG 737 XL.ppp

Layout is modeled after Fragtality's Fenix A320 PilotsDeck profile: a main page with
camera views, flight-phase pages (Gate/Taxi/Flight/Cruise) and system folders.
"""
import io
import json
import os
import random
import shutil
import uuid
import zipfile

import images
import sd
from pmdg import click, custom_event, goto, lvar, rb, toggle
from sd import CALC, KVAR, LUA

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PKG_SRC = os.path.join(HERE, "package")
DIST = os.path.join(ROOT, "dist")

PROFILE_NAME = "PMDG 737 XL"
PACKAGE_NAME = "PMDG 737 XL.ppp"
XL_MODEL = "20GAT9901"
A = "Images/pmdg737/"   # annunciator images shipped with the package

random.seed(737)


# --------------------------------------------------------------------------------------------
# RPN helpers built on pmdg.py
# --------------------------------------------------------------------------------------------
def L(sid):
    return f"({lvar(sid)}, number)"


def goto_rpn(sid, target_rpn, step, inc, dec):
    """Like pmdg.goto but the target is computed by RPN at runtime."""
    return (f"{target_rpn} {L(sid)} - {step} div near s0 "
            f":1 l0 0 > if{{ {rb(sid, inc)} l0 -- s0 g1 }} "
            f"l0 0 < if{{ {rb(sid, dec)} l0 ++ s0 g1 }}")


def cycle(sid, step, maxval, inc, dec, minval=0):
    """Next position, wrapping from the last back to the first."""
    tgt = f"{L(sid)} {maxval - step / 2:g} < if{{ {L(sid)} {step} + near }} els{{ {minval} }}"
    return goto_rpn(sid, tgt, step, inc, dec)


def step_down(sid, step, minval, inc, dec):
    tgt = f"{L(sid)} {minval + step / 2:g} > if{{ {L(sid)} {step} - near }} els{{ {minval} }}"
    return goto_rpn(sid, tgt, step, inc, dec)


def toggle_between(sid, a, b, step, inc, dec):
    """Go to b when the switch is at a, otherwise go to a."""
    tgt = f"{L(sid)} near {a} == if{{ {b} }} els{{ {a} }}"
    return goto_rpn(sid, tgt, step, inc, dec)


def times(code, n):
    return " ".join([code] * n)


# --------------------------------------------------------------------------------------------
# Control factories (each call returns a new Stream Deck action)
# --------------------------------------------------------------------------------------------
def light_img(name):
    return A + name + ".png"


def sw(title, sid, light=None, light_img_name=None, on_img="ON-WHITE", cmd=None, light_state=">0"):
    """2-position switch shown as Korry: top = switch ON, bottom = associated annunciator."""
    return sd.korry(title, cmd or toggle(sid),
                    top=(lvar(sid), ">=50", light_img(on_img)) if on_img else None,
                    bot=(lvar(light), light_state, light_img(light_img_name)) if light else None)


def light_sw(title, sid):
    """Exterior light switches: a left click toggles them (as used by CoreFlightTech)."""
    return sd.korry(title, click(sid, 1), top=(lvar(sid), ">=50", light_img("ON-WHITE")))


def multi(title, sid, mappings, step, maxval, inc, dec, short=None, long=None, special=None):
    """Multi-position switch as Display Value: short press = next (wraps), long = previous."""
    return sd.display(title, lvar(sid),
                      cmd=short or cycle(sid, step, maxval, inc, dec),
                      long=long or step_down(sid, step, 0, inc, dec),
                      mappings=mappings, fmt="0", special=special, font_size="13")


def rotary(title, sid, mappings, maxval):
    """Rotary selector (positions 0,10,20..): 07 = clockwise, 08 = counter-clockwise."""
    return multi(title, sid, mappings, 10, maxval, 7, 8)


def three_pos(title, sid, mappings):
    """3-position toggle (0/50/100): 01 increases, 02 decreases."""
    return multi(title, sid, mappings, 50, 100, 1, 2)


def push(title, sid, action=1, image="Images/Switch.png", size=11):
    return sd.button(title, click(sid, action), image=image, size=size)


def knob(title, sid, inc=True, fast=10):
    """Knob step: short press = 1 click, long press = `fast` clicks."""
    a = 7 if inc else 8
    return sd.button(title, rb(sid, a), long=times(rb(sid, a), fast), image="Images/SwitchBlack.png",
                     size=14)


def mcp_btn(title, sid):
    """MCP push button with its green bar light (switch_<ID>1_73X)."""
    return sd.dynamic(title, lvar(sid * 10 + 1), ">0", "0", "Images/FCUButton_on.png",
                      "Images/FCUButton_off.png", cmd=click(sid, 1), size=11)


def mcp_disp(title, func, cmd=None, long=None):
    return sd.display(title, f"lua:PMDG737:{func}", cmd=cmd, long=long, box=False,
                      font="Consolas", font_size="17", color="#ffb000",
                      image="Images/SwitchBlack.png", title_size=10, rect="-1; 16; 72; 52")


def annun(title, sid, img, state=">0"):
    """Read-only annunciator."""
    return sd.korry(title, None, bot=(lvar(sid), state, light_img(img)))


def master_caution():
    return sd.dynamic("", lvar(3481), ">0", "0", "Images/MasterCaution.png", "Images/SwitchBlack.png",
                      cmd=click(348), long=click(349), size=9)


def fire_warn():
    return sd.dynamic("", lvar(3471), ">0", "0", "Images/MasterWarning.png", "Images/SwitchBlack.png",
                      cmd=click(347), size=9)


def park_brake():
    return sd.korry("PARK BRK", "K:PARKING_BRAKES", cmd_type=KVAR,
                    bot=(lvar(692), ">0", light_img("PARK-BRAKE")))


def gear_ind():
    return sd.dynamic("GEAR", "lua:PMDG737:GEAR_STATE", "2", "0", "Images/GearLocked.png",
                      "Images/Gear.png", special="1", special_img="Images/GearTransit.png",
                      align="top", size=10)


def gear_up():
    return sd.button("GEAR\nUP", "K:GEAR_UP", cmd_type=KVAR)


def gear_off():
    return sd.button("GEAR\nOFF", "30 (L:switch_455_73X, number) - 10 div s0 :1 "
                                  "l0 0 > if{ 45501 (>K:ROTOR_BRAKE) l0 -- s0 g1 } "
                                  "l0 0 < if{ 45502 (>K:ROTOR_BRAKE) l0 ++ s0 g1 }")


def gear_dn():
    return sd.button("GEAR\nDOWN", "K:GEAR_DOWN", cmd_type=KVAR)


def flaps_disp():
    return sd.display("FLAPS", "(A:FLAPS HANDLE INDEX, number)", cmd="K:FLAPS_INCR",
                      long="K:FLAPS_DECR", cmd_type=KVAR,
                      mappings="0=UP:1=1:2=2:3=5:4=10:5=15:6=25:7=30:8=40", fmt="0", font_size="16")


def flaps_ext():
    return sd.button("FLAPS\n▼", "K:FLAPS_INCR", cmd_type=KVAR)


def flaps_ret():
    return sd.button("FLAPS\n▲", "K:FLAPS_DECR", cmd_type=KVAR)


def speedbrake_arm():
    return sd.korry("SPD BRK", "K:SPOILERS_ARM_TOGGLE", cmd_type=KVAR,
                    top=(lvar(343), ">0", light_img("ARMED")),
                    bot=(lvar(447), ">0", light_img("SPDBRK-EXT")))


def autobrake():
    return rotary("AUTOBRAKE", 460, "0=RTO:10=OFF:20=1:30=2:40=3:50=MAX", 50)


def apu():
    return sd.korry("APU", "lua:PMDG737:APU_START", cmd_type=LUA,
                    top=(lvar(118), ">=50", light_img("ON-WHITE")),
                    bot=(lvar(33), ">0", light_img("APU-FAULT")))


def bat():
    return sd.korry("BAT", click(1), top=(lvar(1), ">0", light_img("ON-WHITE")))


def grd_pwr():
    return sd.korry("GRD PWR", click(17, 1), long=click(17, 2),
                    bot=(lvar(16), ">0", light_img("GRD-AVAIL")))


def gen(title, sid, light):
    return sd.korry(title, click(sid, 1), long=click(sid, 2),
                    bot=(lvar(light), ">0", light_img("OFF-BUS")))


def pump(title, sid, light):
    return sw(title, sid, light, "LOW-PRESS")


def pack(title, sid, light):
    return multi(title, sid, "0=OFF:50=AUTO:100=HIGH", 50, 100, 1, 2,
                 short=cycle(sid, 50, 100, 1, 2), special=None)


def isol():
    return three_pos("ISOLATION", 202, "0=CLOSE:50=AUTO:100=OPEN")


def bleed(title, sid, light=None):
    return sw(title, sid, light, "TRIP-OFF") if light else sw(title, sid)


def irs(title, sid):
    return multi(title, sid, "0=OFF:10=ALIGN:20=NAV:30=ATT", 10, 30, 7, 8,
                 short=toggle_between(sid, 0, 20, 10, 7, 8),
                 long=cycle(sid, 10, 30, 7, 8))


def eng_start(title, sid):
    # short: OFF <-> GRD, long: CONT <-> FLT
    return multi(title, sid, "0=GRD:10=OFF:20=CONT:30=FLT", 10, 30, 7, 8,
                 short=toggle_between(sid, 10, 0, 10, 7, 8),
                 long=toggle_between(sid, 20, 30, 10, 7, 8))


def ign_sel():
    return three_pos("IGN", 120, "0=L:50=BOTH:100=R")


def start_lever(title, sid):
    return sd.display(title, lvar(sid), cmd=toggle(sid), mappings="0=CUTOFF:100=IDLE", fmt="0",
                      font_size="12")


def wheat(title, sid, on_light, ovht_light):
    return sd.korry(title, toggle(sid), top=(lvar(on_light), ">0", light_img("ON-GREEN")),
                    bot=(lvar(ovht_light), ">0", light_img("OVERHEAT")))


def door(title, offset, light):
    return sd.korry(title, custom_event(offset), cmd_type=KVAR,
                    bot=(lvar(light), ">0", light_img("DOOR-OPEN")))


def strobe():
    return three_pos("POSITION", 123, "0=STRB:50=OFF:100=STDY")


def seatbelt():
    return three_pos("BELTS", 104, "0=OFF:50=AUTO:100=ON")


def nosmoke():
    return three_pos("NO SMOKE", 103, "0=OFF:50=AUTO:100=ON")


def com1():
    return sd.radio("COM1", "(A:COM ACTIVE FREQUENCY:1, KHz)", "(A:COM STANDBY FREQUENCY:1, KHz)",
                    cmd=click(721), scalar="0.001", fmt="3")


def com2():
    return sd.radio("COM2", "(A:COM ACTIVE FREQUENCY:2, KHz)", "(A:COM STANDBY FREQUENCY:2, KHz)",
                    cmd=click(837), scalar="0.001", fmt="3")


def nav1():
    return sd.radio("NAV1", "(A:NAV ACTIVE FREQUENCY:1, MHz)", "(A:NAV STANDBY FREQUENCY:1, MHz)",
                    cmd=click(729), fmt="2")


def xpdr_code():
    return sd.display("XPDR", "(A:TRANSPONDER CODE:1, number)", cmd=click(806), fmt="4.0",
                      font="Consolas", font_size="17", color="#ffb000", box=False,
                      image="Images/SwitchBlack.png", rect="-1; 16; 72; 52")


def xpdr_mode():
    return rotary("TCAS", 800, "0=STBY:10=ALT OFF:20=XPNDR:30=TA:40=TA/RA", 40)


def utc_clock():
    return sd.display("UTC", "lua:PMDG737:ZULU_CLOCK", box=False, font="Consolas", font_size="15",
                      color="#33dd55", image="Images/SwitchBlack.png", rect="-1; 18; 72; 50")


def efis_range():
    return rotary("RANGE", 361, "0=5:10=10:20=20:30=40:40=80:50=160:60=320:70=640", 70)


def efis_mode():
    return rotary("MODE", 359, "0=APP:10=VOR:20=MAP:30=PLN", 30)


def mcp_spd():
    return mcp_disp("IAS/MACH", "MCP_SPD", cmd=click(387), long=click(383))


def mcp_hdg():
    return mcp_disp("HDG", "MCP_HDG", cmd=click(392))


def mcp_alt():
    return mcp_disp("ALT", "MCP_ALT", cmd=click(885))


def mcp_vs():
    return mcp_disp("V/S", "MCP_VS", cmd=click(395))


def ldg_all():
    return sd.button("ALL\nLDG LT", custom_event(14000), cmd_type=KVAR)


def turnoff_all():
    return sd.button("RWY\nTURNOFF", custom_event(14001), cmd_type=KVAR)


# --------------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------------
class Page:
    def __init__(self, name, parent=None):
        self.name = name
        self.id = str(uuid.uuid5(sd.NS, "page/" + name))
        self.actions = {}
        self.images = {}
        if parent is not None:
            self.actions["0,0"] = sd.back()

    def put(self, col, row, action):
        key = f"{col},{row}"
        assert key not in self.actions, f"{self.name}: {key} used twice"
        assert 0 <= col < 8 and 0 <= row < 4, f"{self.name}: {key} out of XL range"
        self.actions[key] = action

    def link(self, col, row, title, child, kind="folder"):
        img = images.sd_image_name()
        self.images[img] = images.folder_icon(kind)
        self.put(col, row, sd.folder(title, child.id, "Images/" + img, size=12))

    def grid(self, rows):
        """rows: list of 4 lists with up to 8 entries (None = empty, 'back' slot skipped)."""
        for r, row in enumerate(rows):
            for c, action in enumerate(row):
                if action is not None and action != "back":
                    self.put(c, r, action)

    def manifest(self):
        return {"Controllers": [{"Actions": self.actions or None, "Type": "Keypad"}],
                "Icon": "", "Name": ""}


def build_pages():
    pages = []

    def page(name, parent):
        p = Page(name, parent)
        pages.append(p)
        return p

    main = page("MAIN", None)

    # ---------------- Overhead ----------------
    ovhd = page("OVERHEAD", main)
    ovhd.grid([
        ["back", bat(), annun("STBY PWR", 8, "OFF-AMBER"), grd_pwr(),
         gen("GEN 1", 27, 24), gen("APU GEN 1", 28, 25), gen("APU GEN 2", 29, 25), gen("GEN 2", 30, 26)],
        [apu(), pump("L AFT", 37, 41), pump("L FWD", 38, 42), pump("CTR L", 45, 47),
         sw("X FEED", 49, 51, "VALVE-OPEN", on_img=None),
         pump("CTR R", 46, 48), pump("R FWD", 39, 43), pump("R AFT", 40, 44)],
        [sw("ENG 1 HYD", 165, 161, "LOW-PRESS"), sw("ELEC 2 HYD", 167, 163, "LOW-PRESS"),
         sw("ELEC 1 HYD", 168, 164, "LOW-PRESS"), sw("ENG 2 HYD", 166, 162, "LOW-PRESS"),
         pack("L PACK", 200, 203), isol(), pack("R PACK", 201, 206), sw("RECIRC FAN", 196)],
        [bleed("ENG 1 BLEED", 210, 205), bleed("APU BLEED", 211), bleed("ENG 2 BLEED", 212, 208),
         sw("YAW DAMPER", 63, 64, "YAW-DAMPER"), push("TRIP\nRESET", 209),
         rotary("PRESS MODE", 223, "0=AUTO:10=ALTN:20=MAN", 20), None, None],
    ])
    ovhd2 = page("OVERHEAD 2", ovhd)
    ovhd.link(7, 3, "OVHD 2", ovhd2)
    ovhd2.grid([
        ["back", eng_start("ENG START L", 119), ign_sel(), eng_start("ENG START R", 121),
         irs("IRS L", 255), irs("IRS R", 256),
         rotary("WIPER L", 36, "0=PARK:10=INT:20=LOW:30=HIGH", 30),
         rotary("WIPER R", 109, "0=PARK:10=INT:20=LOW:30=HIGH", 30)],
        [wheat("WDO L SIDE", 135, 131, 127), wheat("WDO L FWD", 136, 132, 128),
         wheat("WDO R FWD", 138, 133, 129), wheat("WDO R SIDE", 139, 134, 130),
         sw("PROBE A", 140), sw("PROBE B", 141),
         sw("WING A/I", 156, 152, "VALVE-OPEN", on_img="ON-WHITE"),
         three_pos("EMER EXIT", 100, "0=OFF:50=ARMED:100=ON")],
        [sw("ENG 1 A/I", 157, 154, "COWL-VALVE"), sw("ENG 2 A/I", 158, 155, "COWL-VALVE"),
         three_pos("FLT CTRL A", 78, "0=STBY:50=OFF:100=ON"),
         three_pos("FLT CTRL B", 80, "0=STBY:50=OFF:100=ON"),
         sw("SPOILER A", 65), sw("SPOILER B", 67),
         sw("EQUIP SUP", 96, on_img="ON-WHITE"), sw("EQUIP EXH", 97, on_img="ON-WHITE")],
        [rotary("PRESS MODE", 223, "0=AUTO:10=ALTN:20=MAN", 20),
         knob("FLT ALT\n▲", 218, True, 10), knob("FLT ALT\n▼", 218, False, 10),
         knob("LAND ALT\n▲", 220, True, 10), knob("LAND ALT\n▼", 220, False, 10),
         push("ALT HORN\nCUTOUT", 183, size=9), push("TRIP\nRESET", 209),
         sw("TRIM AIR", 311)],
    ])

    # ---------------- Lights & Signs ----------------
    lights = page("LIGHTS", main)
    lights.grid([
        ["back", three_pos("L RETRACT", 111, "0=RET:50=EXT:100=ON"),
         three_pos("R RETRACT", 112, "0=RET:50=EXT:100=ON"), light_sw("L FIXED", 113),
         light_sw("R FIXED", 114), light_sw("L TURNOFF", 115), light_sw("R TURNOFF", 116),
         light_sw("TAXI", 117)],
        [ldg_all(), turnoff_all(), light_sw("LOGO", 122), strobe(), light_sw("ANTI COLL", 124),
         light_sw("WING", 125), light_sw("WHEEL WELL", 126),
         sd.button("CKPT\nLIGHTS", custom_event(14002), cmd_type=KVAR)],
        [nosmoke(), seatbelt(), three_pos("EMER EXIT", 100, "0=OFF:50=ARMED:100=ON"),
         three_pos("DOME", 258, "0=DIM:50=OFF:100=BRT"),
         three_pos("MASTER LTS", 346, "0=TEST:50=BRT:100=DIM"),
         push("ATTEND\nCALL", 105), push("GRD\nCALL", 106), None],
        [None, None, None, None, None, None, None, None],
    ])

    # ---------------- MCP ----------------
    mcp = page("MCP", main)
    mcp.grid([
        ["back", mcp_btn("A/T ARM", 380), mcp_btn("N1", 381), mcp_btn("SPEED", 382),
         mcp_btn("VNAV", 386), mcp_btn("LVL CHG", 391), mcp_btn("CMD A", 402), mcp_btn("CMD B", 403)],
        [sw("F/D L", 378, 379, "MA", on_img="ON-WHITE"), knob("SPD\n+", 384, True),
         knob("HDG\n+", 390, True), knob("ALT\n+", 400, True), knob("V/S\n▲", 401, False, 5),
         mcp_btn("LNAV", 397), mcp_btn("VOR LOC", 396), mcp_btn("APP", 393)],
        [mcp_disp("CRS L", "MCP_CRS_L", cmd=rb(376, 7), long=rb(376, 8)), mcp_spd(),
         mcp_disp("HDG", "MCP_HDG", cmd=rb(389, 7), long=rb(389, 8)), mcp_alt(),
         mcp_disp("V/S", "MCP_VS"), mcp_btn("HDG SEL", 392), mcp_btn("ALT HLD", 394), mcp_btn("V/S", 395)],
        [sw("F/D R", 407, 408, "MA", on_img="ON-WHITE"), knob("SPD\n-", 384, False),
         knob("HDG\n-", 390, False), knob("ALT\n-", 400, False), knob("V/S\n▼", 401, True, 5),
         mcp_btn("CWS A", 404), mcp_btn("CWS B", 405),
         mcp_disp("CRS R", "MCP_CRS_R", cmd=rb(409, 7), long=rb(409, 8))],
    ])

    # ---------------- EFIS (Captain) ----------------
    efis = page("EFIS", main)
    efis.grid([
        ["back", push("MINS\nRAD/BARO", 356, size=9), knob("MINS\n+", 355, True),
         knob("MINS\n-", 355, False), push("MINS\nRST", 357), push("BARO\nIN/HPA", 366, size=9),
         push("BARO\nSTD", 367), push("FPV", 363)],
        [three_pos("VOR/ADF L", 358, "0=VOR:50=OFF:100=ADF"), efis_mode(), push("CTR", 360),
         efis_range(), push("TFC", 362),
         sd.display("BARO", "(A:KOHLSMAN SETTING HG:1, inHg)", fmt="2", font_size="14",
                    color="#33dd55", box=False, image="Images/SwitchBlack.png", rect="-1; 18; 72; 50"),
         knob("BARO\n+", 365, True, 5), knob("BARO\n-", 365, False, 5)],
        [three_pos("VOR/ADF R", 368, "0=VOR:50=OFF:100=ADF"), push("WXR", 369), push("STA", 370),
         push("WPT", 371), push("ARPT", 372), push("DATA", 373), push("POS", 374), push("TERR", 375)],
        [push("MTRS", 364), push("ENG", 463), push("SYS", 462),
         sd.korry("BELOW G/S", click(327), bot=(lvar(4461), ">0", light_img("BELOW-GS"))),
         sd.korry("A/P P/RST", click(339), bot=(lvar(3392), ">0", light_img("AP-DISC"))),
         sd.korry("A/T P/RST", click(340), bot=(lvar(3402), ">0", light_img("AT-DISC"))),
         sd.korry("FMC P/RST", click(341), bot=(lvar(3411), ">0", light_img("FMC"))),
         three_pos("MASTER LTS", 346, "0=TEST:50=BRT:100=DIM")],
    ])

    # ---------------- MIP ----------------
    mip = page("MIP", main)
    mip.grid([
        ["back", gear_ind(), gear_up(), gear_off(), gear_dn(), autobrake(), park_brake(),
         master_caution()],
        [flaps_disp(), flaps_ext(), flaps_ret(), speedbrake_arm(),
         sd.korry("LE FLAPS", None, top=(lvar(457), ">0", light_img("ARMED")),
                  bot=(lvar(456), ">0", light_img("EXTENDED"))),
         annun("AUTOBRAKE", 459, "AUTOBRK-DISARM"), push("RECALL", 349), fire_warn()],
        [push("TO/GA", 684), push("A/T\nDISC", 682), push("A/P\nDISC", 406), push("CHRONO", 314),
         push("GPWS\nTEST", 500), sd.korry("T/O CONFIG", None, top=(lvar(4471), ">0", light_img("TAKEOFF-CFG")),
                                           bot=(lvar(4472), ">0", light_img("CAB-ALT"))),
         push("MFD\nENG", 463), push("MFD\nSYS", 462)],
        [None, None, None, None, None, None, None, utc_clock()],
    ])

    # ---------------- Pedestal (radios, transponder, fire) ----------------
    ped = page("PEDESTAL", main)
    ped.grid([
        ["back", com1(), knob("COM1\nMHz +", 726, True, 5), knob("COM1\nMHz -", 726, False, 5),
         knob("COM1\nkHz +", 727, True, 5), knob("COM1\nkHz -", 727, False, 5), nav1(),
         knob("NAV1\nMHz +", 733, True, 5)],
        [knob("NAV1\nMHz -", 733, False, 5), knob("NAV1\nkHz +", 732, True, 5),
         knob("NAV1\nkHz -", 732, False, 5), com2(), knob("COM2\nMHz +", 842, True, 5),
         knob("COM2\nMHz -", 842, False, 5), knob("COM2\nkHz +", 843, True, 5),
         knob("COM2\nkHz -", 843, False, 5)],
        [xpdr_code(), xpdr_mode(),
         sd.button("XPDR\n1st ±", rb(804, 7), long=rb(804, 8), image="Images/SwitchBlack.png", size=10),
         sd.button("XPDR\n2nd ±", rb(805, 7), long=rb(805, 8), image="Images/SwitchBlack.png", size=10),
         sd.button("XPDR\n3rd ±", rb(807, 7), long=rb(807, 8), image="Images/SwitchBlack.png", size=10),
         sd.button("XPDR\n4th ±", rb(808, 7), long=rb(808, 8), image="Images/SwitchBlack.png", size=10),
         start_lever("ENG 1\nLEVER", 688), start_lever("ENG 2\nLEVER", 689)],
        [sd.hold_button("FIRE TEST\nFAULT/INOP", rb(696, 1), rb(696, 2), size=8),
         sd.hold_button("FIRE TEST\nOVHT/FIRE", rb(696, 2), rb(696, 1), size=8),
         sd.hold_button("EXT TEST\n1", rb(715, 1), rb(715, 2), size=9),
         sd.hold_button("EXT TEST\n2", rb(715, 2), rb(715, 1), size=9),
         push("BELL\nCUTOUT", 704),
         sd.button("RUDDER\nTRIM L", rb(811, 8), long=times(rb(811, 8), 5), size=10),
         sd.button("RUDDER\nTRIM R", rb(811, 7), long=times(rb(811, 7), 5), size=10),
         annun("FIRE", 6972, "FIRE")],
    ])

    # ---------------- CDU (left) ----------------
    cdu = page("CDU", main)
    cdu_num = page("CDU 0-9", cdu)
    cdu_alpha = page("CDU A-Z", cdu)
    k = lambda title, sid, size=11: sd.button(title, click(sid), image="Images/SwitchBlack.png", size=size)
    def cdu_lsk(pg):
        """Line select keys like the real CDU: L1-L4 / R1-R4 in a column, L5/L6 and R5/R6 outside."""
        for i in range(4):
            pg.put(1, i, k(f"L{i + 1}", 534 + i))
            pg.put(6, i, k(f"R{i + 1}", 540 + i))
        pg.put(0, 2, k("L5", 538))
        pg.put(0, 3, k("L6", 539))
        pg.put(7, 2, k("R5", 544))
        pg.put(7, 3, k("R6", 545))

    cdu_lsk(cdu)
    cdu.grid([
        ["back", None, k("INIT\nREF", 546, 10), k("RTE", 547), k("CLB", 548), k("CRZ", 549), None,
         k("PREV\nPAGE", 559, 10)],
        [k("MENU", 551), None, k("DES", 550), k("LEGS", 552), k("DEP\nARR", 553, 10), k("HOLD", 554),
         None, k("NEXT\nPAGE", 560, 10)],
        [None, None, k("PROG", 555), k("N1\nLIMIT", 557, 10), k("FIX", 558), k("EXEC", 556), None, None],
        [None, None, k("CLR", 602), k("DEL", 600), None, None, None, None],
    ])
    cdu.link(4, 3, "0-9", cdu_num)
    cdu.link(5, 3, "A-Z", cdu_alpha)
    digits = {str(d): 561 + (d - 1) for d in range(1, 10)}
    digits["0"] = 571
    cdu_lsk(cdu_num)
    cdu_num.grid([
        ["back", None, k("1", digits["1"], 16), k("2", digits["2"], 16), k("3", digits["3"], 16),
         k("CLR", 602), None, k("EXEC", 556)],
        [k("SP", 599), None, k("4", digits["4"], 16), k("5", digits["5"], 16), k("6", digits["6"], 16),
         k("DEL", 600), None, k("/", 601, 16)],
        [None, None, k("7", digits["7"], 16), k("8", digits["8"], 16), k("9", digits["9"], 16),
         k("PREV\nPAGE", 559, 10), None, None],
        [None, None, k(".", 570, 16), k("0", digits["0"], 16), k("+/-", 572, 14),
         k("NEXT\nPAGE", 560, 10), None, None],
    ])
    letters = [chr(ord("A") + i) for i in range(26)]
    keys = [k(ch, 573 + i, 16) for i, ch in enumerate(letters)]
    keys += [k("SP", 599), k("DEL", 600), k("/", 601, 16), k("CLR", 602), k("EXEC", 556)]
    slots = [(c, r) for r in range(4) for c in range(8) if (c, r) != (0, 0)]
    for (c, r), action in zip(slots, keys):
        cdu_alpha.put(c, r, action)

    # ---------------- GSX (Fragtality's GSX Pro menu, MIT) ----------------
    gsx = page("GSX", main)
    gsx_src = os.path.join(HERE, "third_party", "gsx_xl_page.json")
    with open(gsx_src, encoding="utf-8") as f:
        gsx_actions = json.load(f)
    for key, action in gsx_actions.items():
        if key != "0,0":
            gsx.actions[key] = action

    # ---------------- Flight phase pages ----------------
    gate = page("GATE", main)
    gate.grid([
        ["back", bat(), grd_pwr(), apu(), gen("APU GEN 1", 28, 25), gen("APU GEN 2", 29, 25),
         bleed("APU BLEED", 211), park_brake()],
        [irs("IRS L", 255), irs("IRS R", 256), pack("L PACK", 200, 203), pack("R PACK", 201, 206),
         pump("L AFT", 37, 41), pump("L FWD", 38, 42), pump("R FWD", 39, 43), pump("R AFT", 40, 44)],
        [light_sw("ANTI COLL", 124), strobe(), light_sw("LOGO", 122), light_sw("WING", 125),
         seatbelt(), nosmoke(), gen("GEN 1", 27, 24), gen("GEN 2", 30, 26)],
        [door("FWD L\nDOOR", 14005, 169), door("AFT L\nDOOR", 14007, 176), door("FWD R\nDOOR", 14006, 170),
         door("AFT R\nDOOR", 14008, 177), door("FWD\nCARGO", 14013, 171), door("AFT\nCARGO", 14014, 175),
         bleed("ENG 1 BLEED", 210, 205), bleed("ENG 2 BLEED", 212, 208)],
    ])

    taxi = page("TAXI", main)
    taxi.grid([
        ["back", light_sw("TAXI", 117), light_sw("L TURNOFF", 115), light_sw("R TURNOFF", 116),
         ldg_all(), strobe(), light_sw("ANTI COLL", 124), light_sw("WING", 125)],
        [eng_start("ENG START L", 119), eng_start("ENG START R", 121), start_lever("ENG 1\nLEVER", 688),
         start_lever("ENG 2\nLEVER", 689), apu(), bleed("APU BLEED", 211),
         bleed("ENG 1 BLEED", 210, 205), bleed("ENG 2 BLEED", 212, 208)],
        [pack("L PACK", 200, 203), pack("R PACK", 201, 206), flaps_disp(), flaps_ext(), flaps_ret(),
         autobrake(), xpdr_mode(), park_brake()],
        [master_caution(), fire_warn(), sw("PROBE A", 140), sw("PROBE B", 141),
         sw("WING A/I", 156, 152, "VALVE-OPEN"), sw("ENG 1 A/I", 157, 154, "COWL-VALVE"),
         sw("ENG 2 A/I", 158, 155, "COWL-VALVE"), light_sw("LOGO", 122)],
    ])

    flight = page("FLIGHT", main)
    flight.grid([
        ["back", gear_ind(), gear_up(), gear_off(), gear_dn(), flaps_disp(), flaps_ext(), flaps_ret()],
        [speedbrake_arm(), autobrake(), ldg_all(), turnoff_all(), light_sw("TAXI", 117), strobe(),
         seatbelt(), master_caution()],
        [push("TO/GA", 684), push("A/T\nDISC", 682), push("A/P\nDISC", 406), mcp_btn("CMD A", 402),
         mcp_btn("A/T ARM", 380), mcp_btn("N1", 381), mcp_btn("SPEED", 382), fire_warn()],
        [mcp_spd(), mcp_hdg(), mcp_alt(), mcp_btn("LVL CHG", 391), mcp_btn("VNAV", 386),
         mcp_btn("LNAV", 397), mcp_btn("VOR LOC", 396), mcp_btn("APP", 393)],
    ])

    cruise = page("CRUISE", main)
    cruise.grid([
        ["back", seatbelt(), nosmoke(), pump("CTR L", 45, 47), sw("X FEED", 49, 51, "VALVE-OPEN", on_img=None),
         pump("CTR R", 46, 48), push("RECALL", 349), master_caution()],
        [sw("WING A/I", 156, 152, "VALVE-OPEN"), sw("ENG 1 A/I", 157, 154, "COWL-VALVE"),
         sw("ENG 2 A/I", 158, 155, "COWL-VALVE"), knob("FLT ALT\n▲", 218, True, 10),
         knob("FLT ALT\n▼", 218, False, 10), knob("LAND ALT\n▲", 220, True, 10),
         knob("LAND ALT\n▼", 220, False, 10), fire_warn()],
        [efis_range(), efis_mode(), push("WXR", 369), push("TERR", 375), push("TFC", 362),
         com1(), xpdr_code(), utc_clock()],
        [mcp_spd(), mcp_hdg(), mcp_alt(), mcp_vs(), knob("ALT\n+", 400, True), knob("ALT\n-", 400, False),
         mcp_btn("LVL CHG", 391), mcp_btn("VNAV", 386)],
    ])

    # ---------------- Main page ----------------
    views = ["CAPT", "OVHD", "PED", "MAIN\nPANEL", "CDU", "EFB", "ENG L", "ENG R", "F/O", "PAX L",
             "PAX R", "EXT"]
    for i, title in enumerate(views):
        main.put(i % 3, i // 3, sd.vjoy(title, 1, i + 1))
    main.put(3, 0, master_caution())
    main.put(3, 1, fire_warn())
    main.put(3, 2, park_brake())
    main.put(3, 3, gear_ind())
    for row, (title, pg) in enumerate([("GATE", gate), ("TAXI", taxi), ("FLIGHT", flight),
                                       ("CRUISE", cruise)]):
        main.link(4, row, title, pg, kind="phase")
    for row, (title, pg) in enumerate([("LIGHTS", lights), ("MCP", mcp), ("EFIS", efis), ("GSX", gsx)]):
        main.link(5, row, title, pg)
    for row, (title, pg) in enumerate([("OVHD", ovhd), ("MIP", mip), ("PEDESTAL", ped), ("CDU", cdu)]):
        main.link(6, row, title, pg, )
    main.put(7, 0, utc_clock())
    main.put(7, 1, com1())
    main.put(7, 2, xpdr_code())
    main.put(7, 3, xpdr_mode())
    return main, pages


# --------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------
def build_profile_zip(main, pages):
    profile_uuid = str(uuid.uuid5(sd.NS, "profile/" + PROFILE_NAME)).upper()
    default_page = str(uuid.uuid5(sd.NS, "page/default"))
    base = f"Profiles/{profile_uuid}.sdProfile"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("package.json", json.dumps({
            "AppVersion": "7.1.0.0", "DeviceModel": XL_MODEL, "DeviceSettings": None,
            "FormatVersion": 1, "OSType": "Windows", "OSVersion": "10.0.19045",
            "RequiredPlugins": ["com.extension.pilotsdeck", "com.elgato.streamdeck.profile.backtoparent",
                                "com.elgato.streamdeck.profile.openchild"]}))
        z.writestr(f"{base}/manifest.json", json.dumps({
            "Device": {"Model": XL_MODEL, "UUID": ""},
            "Name": PROFILE_NAME,
            "Pages": {"Current": "00000000-0000-0000-0000-000000000000", "Default": default_page,
                      "Pages": [main.id]},
            "Version": "3.0"}))
        z.writestr(f"{base}/Profiles/{default_page.upper()}/manifest.json",
                   json.dumps({"Controllers": [{"Actions": None, "Type": "Keypad"}], "Icon": "", "Name": ""}))
        for p in pages:
            pdir = f"{base}/Profiles/{p.id.upper()}"
            z.writestr(f"{pdir}/manifest.json", json.dumps(p.manifest(), ensure_ascii=False))
            for name, im in p.images.items():
                b = io.BytesIO()
                im.save(b, "PNG")
                z.writestr(f"{pdir}/Images/{name}", b.getvalue())
    return buf.getvalue()


def main():
    main_page, pages = build_pages()
    profile = build_profile_zip(main_page, pages)

    staging = os.path.join(DIST, "_staging")
    shutil.rmtree(staging, ignore_errors=True)
    shutil.copytree(PKG_SRC, staging)
    images.write_annunciators(os.path.join(staging, "Images", "pmdg737"))
    os.makedirs(os.path.join(staging, "Profiles"), exist_ok=True)
    with open(os.path.join(staging, "Profiles", f"{PROFILE_NAME}.streamDeckProfile"), "wb") as f:
        f.write(profile)

    out = os.path.join(DIST, PACKAGE_NAME)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(staging):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, staging).replace(os.sep, "/"))
    shutil.copy(os.path.join(staging, "Profiles", f"{PROFILE_NAME}.streamDeckProfile"),
                os.path.join(DIST, f"{PROFILE_NAME}.streamDeckProfile"))
    shutil.rmtree(staging)

    total = sum(len(p.actions) for p in pages)
    print(f"{len(pages)} pages, {total} keys -> {out}")


if __name__ == "__main__":
    main()
