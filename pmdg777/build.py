"""Builds the PMDG 777 Stream Deck XL profile package (.ppp) for PilotsDeck.

    python3 pmdg777/build.py            -> dist/PMDG 777 XL.ppp

Same structure as the 737 profile (modeled after Fragtality's Fenix A320 profile).
Control IDs come from the PMDG 777 event list in the MobiFlight-Connector repository
(presets_eventids_pmdg_777.cip). Position L-Vars are assumed to be L:switch_<ID>_a and
annunciator lights are not shown (no verified 777 light IDs) - see README.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "common"))

import builder  # noqa: E402
import sd  # noqa: E402
from pmdg import Pmdg  # noqa: E402
from sd import KVAR, LUA  # noqa: E402

PKG_SRC = os.path.join(HERE, "package")
DIST = builder.DIST

PROFILE_NAME = "PMDG 777 XL"
PACKAGE_NAME = "PMDG 777 XL.ppp"
A = "Images/pmdg777/"   # annunciator images shipped with the package
ID_PREFIX = "777/"

random.seed(777)
sd.set_id_prefix(ID_PREFIX)

# L-Var suffix for switch positions. Change here if your 777 uses a different name.
P = Pmdg("a")
lvar, rb, click, toggle, times = P.lvar, P.rb, P.click, P.toggle, P.times
cycle, step_down, toggle_between, custom_event = P.cycle, P.step_down, P.toggle_between, P.custom_event


# --------------------------------------------------------------------------------------------
# Control factories
# --------------------------------------------------------------------------------------------
def img(name):
    return A + name + ".png"


def pb(title, sid, on_state=">0"):
    """Alternate-action push button (most of the 777 overhead): a left click toggles it.
    Shows ON while its position L-Var is > 0."""
    return sd.korry(title, click(sid), top=(lvar(sid), on_state, img("ON-WHITE")))


def sw(title, sid):
    """2-position toggle switch: 01 = on, 02 = off."""
    return sd.korry(title, toggle(sid), top=(lvar(sid), ">=50", img("ON-WHITE")))


def light_sw(title, sid):
    return sd.korry(title, click(sid), top=(lvar(sid), ">=50", img("ON-WHITE")))


def multi(title, sid, mappings, step, maxval, inc, dec, short=None, long=None):
    return sd.display(title, lvar(sid), cmd=short or cycle(sid, step, maxval, inc, dec),
                      long=long or step_down(sid, step, 0, inc, dec),
                      mappings=mappings, fmt="0", font_size="13")


def rotary(title, sid, mappings, maxval):
    return multi(title, sid, mappings, 10, maxval, 7, 8)


def three_pos(title, sid, mappings):
    return multi(title, sid, mappings, 50, 100, 1, 2)


def push(title, sid, action=1, size=11):
    return sd.button(title, click(sid, action), size=size)


def knob(title, sid, inc=True, fast=10):
    a = 7 if inc else 8
    return sd.button(title, rb(sid, a), long=times(rb(sid, a), fast), image="Images/SwitchBlack.png",
                     size=14)


def mcp_btn(title, sid):
    # no verified light variables for the 777 MCP: plain button
    return sd.button(title, click(sid), image="Images/FCUButton_off.png", size=11)


def mcp_disp(title, func, cmd=None, long=None):
    return sd.display(title, f"lua:PMDG777:{func}", cmd=cmd, long=long, box=False,
                      font="Consolas", font_size="17", color="#ffb000",
                      image="Images/SwitchBlack.png", title_size=10, rect="-1; 16; 72; 52")


def mstr_warn():
    return sd.button("MASTER\nWARN/CAUT\nRESET", click(177), image="Images/SwitchBlack.png", size=9)


def park_brake():
    return sd.korry("PARK BRK", "K:PARKING_BRAKES", cmd_type=KVAR,
                    bot=("(A:BRAKE PARKING POSITION, bool)", ">0", img("PARK-BRAKE")))


def gear_ind():
    return sd.dynamic("GEAR", "lua:PMDG777:GEAR_STATE", "2", "0", "Images/GearLocked.png",
                      "Images/Gear.png", special="1", special_img="Images/GearTransit.png",
                      align="top", size=10)


def gear_up():
    return sd.button("GEAR\nUP", "K:GEAR_UP", cmd_type=KVAR)


def gear_dn():
    return sd.button("GEAR\nDOWN", "K:GEAR_DOWN", cmd_type=KVAR)


def flaps_disp():
    return sd.display("FLAPS", "(A:FLAPS HANDLE INDEX, number)", cmd="K:FLAPS_INCR",
                      long="K:FLAPS_DECR", cmd_type=KVAR,
                      mappings="0=UP:1=1:2=5:3=15:4=20:5=25:6=30", fmt="0", font_size="16")


def flaps_ext():
    return sd.button("FLAPS\n▼", "K:FLAPS_INCR", cmd_type=KVAR)


def flaps_ret():
    return sd.button("FLAPS\n▲", "K:FLAPS_DECR", cmd_type=KVAR)


def speedbrake_arm():
    return sd.korry("SPD BRK", "K:SPOILERS_ARM_TOGGLE", cmd_type=KVAR,
                    top=("(A:SPOILERS ARMED, bool)", ">0", img("ARMED")))


def autobrake():
    return rotary("AUTOBRAKE", 292, "0=RTO:10=OFF:20=DISARM:30=1:40=2:50=3:60=4:70=MAX", 70)


def apu():
    return sd.display("APU", lvar(3), cmd="lua:PMDG777:APU_START", cmd_type=LUA,
                      mappings="0=OFF:10=ON:20=START", fmt="0", font_size="13")


def adiru():
    return pb("ADIRU", 59)


def eng_start(title, sid):
    # 777 engine start selector: pulled to START / NORM. Click pulls it.
    return sd.button(title, click(sid), long=click(sid, 2), size=10)


def fuel_ctrl(title, sid):
    return sd.display(title, lvar(sid), cmd=toggle(sid), mappings="0=CUTOFF:100=RUN", fmt="0",
                      font_size="12")


def door(title, offset):
    return sd.button(title, custom_event(offset), cmd_type=KVAR, size=10)


def seatbelt():
    return three_pos("BELTS", 30, "0=OFF:50=AUTO:100=ON")


def nosmoke():
    return three_pos("NO SMOKE", 29, "0=OFF:50=AUTO:100=ON")


def com(title, n, xfr):
    return sd.radio(title, f"(A:COM ACTIVE FREQUENCY:{n}, KHz)", f"(A:COM STANDBY FREQUENCY:{n}, KHz)",
                    cmd=click(xfr), scalar="0.001", fmt="3")


def xpdr_code():
    return sd.display("XPDR", "(A:TRANSPONDER CODE:1, number)", cmd=click(746), fmt="4.0",
                      font="Consolas", font_size="17", color="#ffb000", box=False,
                      image="Images/SwitchBlack.png", rect="-1; 16; 72; 52")


def xpdr_mode():
    return rotary("TCAS", 749, "0=STBY:10=ALT OFF:20=XPNDR:30=TA:40=TA/RA", 40)


def utc_clock():
    return sd.display("UTC", "lua:PMDG777:ZULU_CLOCK", box=False, font="Consolas", font_size="15",
                      color="#33dd55", image="Images/SwitchBlack.png", rect="-1; 18; 72; 50")


def efis_range():
    return rotary("RANGE", 187, "0=10:10=20:20=40:30=80:40=160:50=320:60=640", 60)


def efis_mode():
    return rotary("MODE", 185, "0=APP:10=VOR:20=MAP:30=PLN", 30)


def mcp_spd():
    return mcp_disp("IAS/MACH", "MCP_SPD", cmd=click(2100), long=click(208))


def mcp_hdg():
    return mcp_disp("HDG/TRK", "MCP_HDG", cmd=click(218), long=click(216))


def mcp_alt():
    return mcp_disp("ALT", "MCP_ALT", cmd=click(2251), long=click(225))


def mcp_vs():
    return mcp_disp("V/S", "MCP_VS", cmd=click(223), long=click(220))


def ldg_all():
    return sd.button("ALL\nLDG LT", custom_event(14000), cmd_type=KVAR)


def turnoff_all():
    return sd.button("RWY\nTURNOFF", custom_event(14001), cmd_type=KVAR)


def dsp(title, sid):
    return sd.button(title, click(sid), image="Images/SwitchBlack.png", size=11)


# --------------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------------
def build_pages():
    pages = []

    def page(name, parent):
        p = builder.Page(name, parent, ID_PREFIX)
        pages.append(p)
        return p

    main = page("MAIN", None)

    # ---------------- Overhead ----------------
    ovhd = page("OVERHEAD", main)
    ovhd.grid([
        ["back", pb("BATTERY", 1), pb("APU GEN", 2), apu(), pb("BUS TIE 1", 5), pb("BUS TIE 2", 6),
         pb("EXT PWR\nPRI", 8), pb("EXT PWR\nSEC", 7)],
        [pb("GEN 1", 9), pb("GEN 2", 10), pb("BACKUP\nGEN 1", 11), pb("BACKUP\nGEN 2", 12),
         pb("FWD L", 103), pb("AFT L", 105), pb("CTR L", 109), pb("CTR R", 110)],
        [pb("FWD R", 104), pb("AFT R", 106), pb("XFEED FWD", 107), pb("XFEED AFT", 108),
         pb("ENG 1 PRI", 39), pb("ELEC C1", 40), pb("ELEC C2", 41), pb("ENG 2 PRI", 42)],
        [rotary("DEM ELEC 1", 35, "0=OFF:10=AUTO:20=ON", 20), rotary("DEM AIR C1", 36, "0=OFF:10=AUTO:20=ON", 20),
         rotary("DEM AIR C2", 37, "0=OFF:10=AUTO:20=ON", 20), rotary("DEM ELEC 2", 38, "0=OFF:10=AUTO:20=ON", 20),
         pb("EQUIP\nCOOLING", 144), pb("RECIRC\nUPPER", 142), pb("RECIRC\nLOWER", 143), None],
    ])
    ovhd2 = page("OVERHEAD 2", ovhd)
    ovhd.link(7, 3, "OVHD 2", ovhd2)
    ovhd2.grid([
        ["back", eng_start("L ENG\nSTART", 94), pb("AUTOSTART", 96), eng_start("R ENG\nSTART", 95),
         pb("EEC L", 90), pb("EEC R", 92),
         rotary("WIPER L", 20, "0=OFF:10=INT:20=LOW:30=HIGH", 30),
         rotary("WIPER R", 123, "0=OFF:10=INT:20=LOW:30=HIGH", 30)],
        [pb("WDO HEAT\nL SIDE", 45), pb("WDO HEAT\nL FWD", 46), pb("WDO HEAT\nR FWD", 47),
         pb("WDO HEAT\nR SIDE", 48), rotary("WING A/I", 111, "0=OFF:10=AUTO:20=ON", 20),
         rotary("ENG A/I L", 112, "0=OFF:10=AUTO:20=ON", 20), rotary("ENG A/I R", 113, "0=OFF:10=AUTO:20=ON", 20),
         adiru()],
        [pb("L PACK", 135), pb("R PACK", 136), pb("TRIM AIR\nL", 137), pb("TRIM AIR\nR", 138),
         pb("L ENG\nBLEED", 129), pb("APU\nBLEED", 131), pb("R ENG\nBLEED", 130), pb("GASPER", 145)],
        [pb("ISLN L", 132), pb("ISLN C", 133), pb("ISLN R", 134), pb("OUTFLOW\nAUTO 1", 127),
         pb("OUTFLOW\nAUTO 2", 128), knob("LAND ALT\n▲", 126, True), knob("LAND ALT\n▼", 126, False),
         pb("THRUST\nASYM", 54)],
    ])

    # ---------------- Lights & Signs ----------------
    lights = page("LIGHTS", main)
    lights.grid([
        ["back", light_sw("L LDG", 22), light_sw("NOSE LDG", 23), light_sw("R LDG", 24),
         light_sw("L TURNOFF", 119), light_sw("R TURNOFF", 120), light_sw("TAXI", 121), ldg_all()],
        [light_sw("BEACON", 114), light_sw("NAV", 115), light_sw("LOGO", 116), light_sw("WING", 117),
         light_sw("STROBE", 122), light_sw("STORM", 27), turnoff_all(),
         sd.button("CKPT\nLIGHTS", custom_event(14002), cmd_type=KVAR)],
        [nosmoke(), seatbelt(), three_pos("EMER LTS", 49, "0=OFF:50=ARMED:100=ON"),
         three_pos("DOME", 26, "0=OFF:50=DIM:100=BRT"),
         three_pos("IND LTS", 118, "0=TEST:50=BRT:100=DIM"),
         sd.button("PANEL\nLIGHTS", custom_event(14003), cmd_type=KVAR),
         sd.button("FLOOD\nLIGHTS", custom_event(14004), cmd_type=KVAR), None],
        [None] * 8,
    ])

    # ---------------- MCP ----------------
    mcp = page("MCP", main)
    mcp.grid([
        ["back", sw("F/D L", 202), sd.button("A/T ARM\nL+R", custom_event(14027), cmd_type=KVAR, size=10),
         mcp_btn("CLB/CON", 206), mcp_btn("A/T", 207), mcp_btn("LNAV", 211), mcp_btn("VNAV", 212),
         sw("F/D R", 230)],
        [mcp_btn("A/P L", 203), knob("SPD\n+", 210, True), knob("HDG\n+", 2180, True),
         knob("ALT\n+", 2250, True), knob("V/S\n▲", 222, False, 5), mcp_btn("FLCH", 213),
         mcp_btn("LOC", 227), mcp_btn("A/P R", 229)],
        [sd.button("BANK\nLIMIT", rb(2181, 7), long=rb(2181, 8), image="Images/SwitchBlack.png", size=11),
         mcp_spd(), mcp_hdg(), mcp_alt(), mcp_vs(), mcp_btn("HDG\nHOLD", 219), mcp_btn("APP", 228),
         mcp_btn("ALT\nHOLD", 226)],
        [push("A/P\nDISENGAGE", 214, size=9), knob("SPD\n-", 210, False), knob("HDG\n-", 2180, False),
         knob("ALT\n-", 2250, False), knob("V/S\n▼", 222, True, 5), push("YOKE A/P\nDISC", 1084, size=9),
         push("TO/GA", 500), push("A/T\nDISC", 502)],
    ])

    # ---------------- EFIS (Captain) ----------------
    efis = page("EFIS", main)
    efis.grid([
        ["back", push("MINS\nRAD/BARO", 181, size=9), knob("MINS\n+", 182, True),
         knob("MINS\n-", 182, False), push("MINS\nRST", 183), push("BARO\nIN/HPA", 190, size=9),
         push("BARO\nSTD", 192), push("FPV", 193)],
        [three_pos("VOR/ADF L", 184, "0=VOR:50=OFF:100=ADF"), efis_mode(), push("CTR", 186),
         efis_range(), push("TFC", 188),
         sd.display("BARO", "(A:KOHLSMAN SETTING HG:1, inHg)", fmt="2", font_size="14",
                    color="#33dd55", box=False, image="Images/SwitchBlack.png", rect="-1; 18; 72; 50"),
         knob("BARO\n+", 191, True, 5), knob("BARO\n-", 191, False, 5)],
        [three_pos("VOR/ADF R", 189, "0=VOR:50=OFF:100=ADF"), push("WXR", 195), push("STA", 196),
         push("WPT", 197), push("ARPT", 198), push("DATA", 199), push("POS", 200), push("TERR", 201)],
        [push("MTRS", 194), push("L INBD\nDSPL", 231, size=9), push("R INBD\nDSPL", 232, size=9),
         push("LWR CTR\nDSPL", 233, size=9), push("G/S\nINHIBIT", 303, size=9),
         rotary("NAV SRC L", 168, "0=FMC L:10=CDU:20=FMC R", 20), push("CHRONO", 171), None],
    ])

    # ---------------- MIP / Display select ----------------
    mip = page("MIP", main)
    mip.grid([
        ["back", gear_ind(), gear_up(), gear_dn(), autobrake(), park_brake(), mstr_warn(), flaps_disp()],
        [flaps_ext(), flaps_ret(), speedbrake_arm(), push("TO/GA", 500), push("A/T\nDISC", 502),
         push("A/P\nDISC", 1084), push("CHRONO", 171), push("G/S\nINHIBIT", 303, size=9)],
        [dsp("ENG", 234), dsp("STAT", 235), dsp("ELEC", 236), dsp("HYD", 237), dsp("FUEL", 238),
         dsp("AIR", 239), dsp("DOOR", 240), dsp("GEAR", 241)],
        [dsp("FCTL", 242), dsp("CAM", 243), dsp("CHKL", 244), dsp("COMM", 245), dsp("NAV", 246),
         dsp("CANC/\nRCL", 247), None, utc_clock()],
    ])

    # ---------------- Pedestal ----------------
    ped = page("PEDESTAL", main)
    ped.grid([
        ["back", com("VHF L", 1, 526), knob("VHF L\nMHz +", 527, True, 5), knob("VHF L\nMHz -", 527, False, 5),
         knob("VHF L\nkHz +", 528, True, 5), knob("VHF L\nkHz -", 528, False, 5), com("VHF R", 2, 801),
         knob("VHF R\nMHz +", 800, True, 5)],
        [knob("VHF R\nMHz -", 800, False, 5), knob("VHF R\nkHz +", 799, True, 5),
         knob("VHF R\nkHz -", 799, False, 5), xpdr_code(), xpdr_mode(),
         sd.button("XPDR\n1st ±", rb(744, 7), long=rb(744, 8), image="Images/SwitchBlack.png", size=10),
         sd.button("XPDR\n2nd ±", rb(745, 7), long=rb(745, 8), image="Images/SwitchBlack.png", size=10),
         sd.button("XPDR\n3rd ±", rb(747, 7), long=rb(747, 8), image="Images/SwitchBlack.png", size=10)],
        [sd.button("XPDR\n4th ±", rb(748, 7), long=rb(748, 8), image="Images/SwitchBlack.png", size=10),
         fuel_ctrl("FUEL CTRL\nL", 520), fuel_ctrl("FUEL CTRL\nR", 521),
         sd.button("RUDDER\nTRIM L", rb(728, 8), long=times(rb(728, 8), 5), size=10),
         sd.button("RUDDER\nTRIM R", rb(728, 7), long=times(rb(728, 7), 5), size=10),
         push("RUD TRIM\nCANCEL", 729, size=9),
         sd.button("AIL\nTRIM L", rb(727, 8), long=times(rb(727, 8), 5), size=10),
         sd.button("AIL\nTRIM R", rb(727, 7), long=times(rb(727, 7), 5), size=10)],
        [sd.hold_button("FIRE/OVHT\nTEST", rb(89, 1), rb(89, 2), size=9), pb("CARGO\nARM FWD", 85),
         pb("CARGO\nARM AFT", 86), push("TCAS\nTEST", 7491, size=10), None, None, None, None],
    ])

    # ---------------- CDU (left) ----------------
    cdu = page("CDU", main)
    cdu_num = page("CDU 0-9", cdu)
    cdu_alpha = page("CDU A-Z", cdu)

    def k(title, sid, size=11):
        return sd.button(title, click(sid), image="Images/SwitchBlack.png", size=size)

    def cdu_lsk(pg):
        for i in range(4):
            pg.put(1, i, k(f"L{i + 1}", 328 + i))
            pg.put(6, i, k(f"R{i + 1}", 334 + i))
        pg.put(0, 2, k("L5", 332))
        pg.put(0, 3, k("L6", 333))
        pg.put(7, 2, k("R5", 338))
        pg.put(7, 3, k("R6", 339))

    cdu_lsk(cdu)
    cdu.grid([
        ["back", None, k("INIT\nREF", 340, 10), k("RTE", 341), k("DEP\nARR", 342, 10), k("ALTN", 343), None,
         k("PREV\nPAGE", 352, 10)],
        [k("MENU", 350), None, k("VNAV", 344), k("FIX", 345), k("LEGS", 346), k("HOLD", 347), None,
         k("NEXT\nPAGE", 353, 10)],
        [None, None, k("PROG", 348), k("NAV\nRAD", 351, 10), k("CLR", 395), k("EXEC", 349), None, None],
        [None, None, k("DEL", 393), None, None, None, None, None],
    ])
    cdu.link(3, 3, "0-9", cdu_num)
    cdu.link(4, 3, "A-Z", cdu_alpha)
    digits = {str(d): 354 + (d - 1) for d in range(1, 10)}
    digits["0"] = 364
    cdu_lsk(cdu_num)
    cdu_num.grid([
        ["back", None, k("1", digits["1"], 16), k("2", digits["2"], 16), k("3", digits["3"], 16),
         k("CLR", 395), None, k("EXEC", 349)],
        [k("SP", 392), None, k("4", digits["4"], 16), k("5", digits["5"], 16), k("6", digits["6"], 16),
         k("DEL", 393), None, k("/", 394, 16)],
        [None, None, k("7", digits["7"], 16), k("8", digits["8"], 16), k("9", digits["9"], 16),
         k("PREV\nPAGE", 352, 10), None, None],
        [None, None, k(".", 363, 16), k("0", digits["0"], 16), k("+/-", 365, 14),
         k("NEXT\nPAGE", 353, 10), None, None],
    ])
    letters = [chr(ord("A") + i) for i in range(26)]
    keys = [k(ch, 366 + i, 16) for i, ch in enumerate(letters)]
    keys += [k("SP", 392), k("DEL", 393), k("/", 394, 16), k("CLR", 395), k("EXEC", 349)]
    slots = [(c, r) for r in range(4) for c in range(8) if (c, r) != (0, 0)]
    for (c, r), action in zip(slots, keys):
        cdu_alpha.put(c, r, action)

    # ---------------- GSX (Fragtality's GSX Pro menu, MIT) ----------------
    gsx = page("GSX", main)
    gsx_src = os.path.join(os.path.dirname(HERE), "pmdg737", "third_party", "gsx_xl_page.json")
    with open(gsx_src, encoding="utf-8") as f:
        gsx_actions = json.load(f)
    for key, action in gsx_actions.items():
        if key != "0,0":
            action = dict(action, ActionID=sd._uid("gsx", key))
            gsx.actions[key] = action

    # ---------------- Flight phase pages ----------------
    gate = page("GATE", main)
    gate.grid([
        ["back", pb("BATTERY", 1), apu(), pb("APU GEN", 2), pb("EXT PWR\nPRI", 8), pb("EXT PWR\nSEC", 7),
         adiru(), park_brake()],
        [pb("L PACK", 135), pb("R PACK", 136), pb("APU\nBLEED", 131), pb("L ENG\nBLEED", 129),
         pb("R ENG\nBLEED", 130), pb("FWD L", 103), pb("AFT L", 105), pb("FWD R", 104)],
        [pb("AFT R", 106), light_sw("BEACON", 114), light_sw("NAV", 115), light_sw("LOGO", 116),
         light_sw("WING", 117), seatbelt(), nosmoke(), pb("GEN 1", 9)],
        [door("DOOR\n1L", 14011), door("DOOR\n2L", 14013), door("DOOR\n1R", 14012), door("DOOR\n2R", 14014),
         door("FWD\nCARGO", 14021), door("AFT\nCARGO", 14022), door("BULK\nCARGO", 14023), pb("GEN 2", 10)],
    ])

    taxi = page("TAXI", main)
    taxi.grid([
        ["back", light_sw("TAXI", 121), light_sw("L TURNOFF", 119), light_sw("R TURNOFF", 120),
         ldg_all(), light_sw("STROBE", 122), light_sw("BEACON", 114), light_sw("WING", 117)],
        [eng_start("L ENG\nSTART", 94), pb("AUTOSTART", 96), eng_start("R ENG\nSTART", 95),
         fuel_ctrl("FUEL CTRL\nL", 520), fuel_ctrl("FUEL CTRL\nR", 521), apu(), pb("APU\nBLEED", 131),
         light_sw("LOGO", 116)],
        [pb("L PACK", 135), pb("R PACK", 136), flaps_disp(), flaps_ext(), flaps_ret(), autobrake(),
         xpdr_mode(), park_brake()],
        [mstr_warn(), rotary("WING A/I", 111, "0=OFF:10=AUTO:20=ON", 20),
         rotary("ENG A/I L", 112, "0=OFF:10=AUTO:20=ON", 20), rotary("ENG A/I R", 113, "0=OFF:10=AUTO:20=ON", 20),
         dsp("ENG", 234), dsp("CHKL", 244), dsp("FCTL", 242), dsp("STAT", 235)],
    ])

    flight = page("FLIGHT", main)
    flight.grid([
        ["back", gear_ind(), gear_up(), gear_dn(), flaps_disp(), flaps_ext(), flaps_ret(), speedbrake_arm()],
        [autobrake(), ldg_all(), turnoff_all(), light_sw("TAXI", 121), light_sw("STROBE", 122), seatbelt(),
         mstr_warn(), mcp_btn("HDG\nHOLD", 219)],
        [push("TO/GA", 500), push("A/T\nDISC", 502), push("A/P\nDISC", 1084), mcp_btn("A/P L", 203),
         sd.button("A/T ARM\nL+R", custom_event(14027), cmd_type=KVAR, size=10), mcp_btn("CLB/CON", 206),
         mcp_btn("A/T", 207), mcp_btn("FLCH", 213)],
        [mcp_spd(), mcp_hdg(), mcp_alt(), mcp_vs(), mcp_btn("VNAV", 212), mcp_btn("LNAV", 211),
         mcp_btn("LOC", 227), mcp_btn("APP", 228)],
    ])

    cruise = page("CRUISE", main)
    cruise.grid([
        ["back", seatbelt(), nosmoke(), pb("CTR L", 109), pb("CTR R", 110), pb("XFEED FWD", 107),
         pb("XFEED AFT", 108), mstr_warn()],
        [rotary("WING A/I", 111, "0=OFF:10=AUTO:20=ON", 20), rotary("ENG A/I L", 112, "0=OFF:10=AUTO:20=ON", 20),
         rotary("ENG A/I R", 113, "0=OFF:10=AUTO:20=ON", 20), knob("LAND ALT\n▲", 126, True),
         knob("LAND ALT\n▼", 126, False), dsp("FUEL", 238), dsp("CANC/\nRCL", 247), dsp("STAT", 235)],
        [efis_range(), efis_mode(), push("WXR", 195), push("TERR", 201), push("TFC", 188),
         com("VHF L", 1, 526), xpdr_code(), utc_clock()],
        [mcp_spd(), mcp_hdg(), mcp_alt(), mcp_vs(), knob("ALT\n+", 2250, True), knob("ALT\n-", 2250, False),
         mcp_btn("FLCH", 213), mcp_btn("VNAV", 212)],
    ])

    # ---------------- Main page ----------------
    views = ["CAPT", "OVHD", "PED", "MAIN\nPANEL", "CDU", "EFB", "ENG L", "ENG R", "F/O", "PAX L",
             "PAX R", "EXT"]
    for i, title in enumerate(views):
        main.put(i % 3, i // 3, sd.vjoy(title, 1, i + 1))
    main.put(3, 0, mstr_warn())
    main.put(3, 1, dsp("CANC/\nRCL", 247))
    main.put(3, 2, park_brake())
    main.put(3, 3, gear_ind())
    for row, (title, pg) in enumerate([("GATE", gate), ("TAXI", taxi), ("FLIGHT", flight),
                                       ("CRUISE", cruise)]):
        main.link(4, row, title, pg, kind="phase")
    for row, (title, pg) in enumerate([("LIGHTS", lights), ("MCP", mcp), ("EFIS", efis), ("GSX", gsx)]):
        main.link(5, row, title, pg)
    for row, (title, pg) in enumerate([("OVHD", ovhd), ("MIP", mip), ("PEDESTAL", ped), ("CDU", cdu)]):
        main.link(6, row, title, pg)
    main.put(7, 0, utc_clock())
    main.put(7, 1, com("VHF L", 1, 526))
    main.put(7, 2, xpdr_code())
    main.put(7, 3, xpdr_mode())
    return main, pages


def main():
    main_page, pages = build_pages()
    builder.write_package(PROFILE_NAME, PACKAGE_NAME, PKG_SRC, "pmdg777", main_page, pages, ID_PREFIX)


if __name__ == "__main__":
    main()
