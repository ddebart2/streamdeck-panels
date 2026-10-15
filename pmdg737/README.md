# PMDG 737 (MSFS) – Stream Deck XL profile for PilotsDeck

A PilotsDeck profile package for the PMDG 737 (-600/-700/-800/-900, MSFS 2020/2024) on a
Stream Deck XL. It is modeled on Fragtality's Fenix A320 PilotsDeck profile: a main page with
camera views, four flight-phase pages, and one folder per cockpit area. It uses the same tools:
PilotsDeck for the Stream Deck side and the MobiFlight WASM module for reading and moving the
PMDG switches. FSUIPC is not needed.

Download: [`dist/PMDG 737 XL.ppp`](../dist/PMDG%20737%20XL.ppp). Previews of every page are in
[`dist/previews`](../dist/previews).

## Requirements

- PMDG 737 for MSFS
- PilotsDeck **0.9.1 or newer** (its installer also installs the MobiFlight WASM module)
- Stream Deck software 7.1 or newer, Stream Deck XL
- Optional: the [vJoy driver](https://github.com/BrunnerInnovation/vJoy/releases) for the camera keys
- Optional: GSX Pro for the GSX folder

## Install

1. Open the PilotsDeck **Profile Manager** from its tray icon and drop `PMDG 737 XL.ppp` on it.
   It copies the scripts (`Scripts/PMDG737.lua`, `Scripts/global/GSX.lua`) and the annunciator images
   (`Images/pmdg737/`) into the plugin folder.
2. Click the profile link it shows, and install the profile to your **XL** in the Stream Deck app.
3. Optional: in Profile Manager → Profile Mapping, enable `PMDG 737 XL` for switching and add the
   search string `PMDG 737`, so the profile loads automatically with the aircraft.
4. Camera keys: these press vJoy device 1, buttons 1-12 (CAPT, OVHD, PED, MAIN PANEL, CDU, EFB,
   ENG L, ENG R, F/O, PAX L, PAX R, EXT). In the MSFS controls, bind those vJoy buttons to
   "Load Custom Camera 1…12" and save your custom cameras. MSFS only lets custom cameras be triggered
   by joystick or keyboard, so this is the same approach the PilotsDeck author recommends. If you
   don't use vJoy, delete or reassign those keys.

## Layout

| Page | Contents |
| --- | --- |
| **Main** | 12 camera views · Master Caution / Fire Warning · Park Brake · Gear lights · phase folders (Gate, Taxi, Flight, Cruise) · Lights, MCP, EFIS, GSX, Overhead, MIP, Pedestal, CDU folders · UTC clock · COM1 · XPDR code · TCAS mode |
| **Gate** | BAT, GRD PWR, APU, APU GENs, APU bleed, IRS, packs, main tank pumps, beacon/position/logo/wing lights, belts, no smoking, GEN 1/2, six doors (with OPEN annunciation), engine bleeds, park brake |
| **Taxi** | Taxi/turnoff/landing lights, strobe, beacon, engine start switches and start levers, APU and bleeds, packs, flaps, autobrake, TCAS mode, probe heat and anti-ice, master caution |
| **Flight** | Gear (lights, UP/OFF/DOWN), flaps, speedbrake arm, autobrake, lights, TO/GA, A/T and A/P disconnect, main MCP modes, SPD/HDG/ALT windows |
| **Cruise** | Belts, center pumps, crossfeed, anti-ice, cabin pressure FLT/LAND ALT, EFIS range/mode, WXR/TERR/TFC, COM1, XPDR, MCP windows, ALT knob |
| **Overhead** | Electrical (BAT, STBY PWR, GRD PWR, GENs), APU, fuel pumps and crossfeed, hydraulic pumps, packs, isolation valve, bleeds, recirc fan, yaw damper, trip reset, pressurization mode → **Overhead 2** |
| **Overhead 2** | Engine start and ignition, IRS, wipers, window heat, probe heat, wing/engine anti-ice, emergency exit lights, flight controls A/B, spoilers A/B, equipment cooling, FLT ALT / LAND ALT knobs, altitude horn cutout, trim air |
| **Lights** | Retractable, fixed and turnoff landing lights, taxi, "all landing lights", "all turnoff", logo, position/strobe, anti-collision, wing, wheel well, cockpit lights, belts, no smoking, emergency exit, dome, master lights test, attendant/ground call |
| **MCP** | All MCP buttons with their lights, SPD/HDG/ALT/V/S windows with +/- keys, CRS L/R, F/D switches with MA lights |
| **EFIS** | Captain EFIS (minimums, baro, mode, range, map buttons, VOR/ADF), MFD ENG/SYS, Below G/S, A/P, A/T, FMC P/RST, master lights test |
| **MIP** | Gear, autobrake, park brake, flaps, speedbrake, LE flaps, autobrake disarm, recall, TO/GA, disconnects, chrono, GPWS test, takeoff config / cabin altitude, MFD, UTC |
| **Pedestal** | COM1/COM2/NAV1 (active/standby display, press to swap) with MHz/kHz keys, transponder code and digits, TCAS mode, start levers, fire and extinguisher tests, bell cutout, rudder trim, fire light |
| **CDU** | Left CDU: line select keys, function keys, EXEC, CLR, DEL → **0-9** and **A-Z** pages |
| **GSX** | Fragtality's GSX Pro menu page (from the PilotsDeck GSX package, MIT licensed) |

Key behavior:
- **Short press / long press (≥ 0.5 s):** multi-position switches step forward on a short press and
  back on a long press. Knob keys (+/-) move one click on a short press and 5–10 clicks on a long press.
  The SPD window is SPD INTV on a short press and C/O on a long press. HDG = bank angle, ALT = ALT INTV,
  V/S = V/S mode, CRS = +1/−1.
- **IRS:** short press toggles OFF ↔ NAV, long press steps through ALIGN/NAV/ATT.
- **Engine start:** short press toggles OFF ↔ GRD, long press toggles CONT ↔ FLT.
- **APU:** a press from OFF goes to START and drops back to ON after 2.5 s. A press while running turns it OFF.
- **Master Caution:** short press resets, long press is six-pack RECALL.

## How it works

- Switch positions and annunciators are read from the PMDG L-Vars `L:switch_<ID>_73X`
  (`<ID>` = PMDG SDK event ID − 69632). Switches are 0/100, 3-position switches 0/50/100, rotaries
  0/10/20…, and annunciators are lit when the value is > 0.
- Controls are moved with calculator code `<ID><ACTION> (>K:ROTOR_BRAKE)`:
  01/02 = left/right click, 07/08 = wheel up/down. Multi-position keys compute the number of clicks in RPN.
- MCP windows come from `L:ngx_SPDwindow`, `ngx_HDGwindow`, `ngx_ALTwindow`, `ngx_VSwindow`,
  `ngx_CRSwindowL/R` and are formatted by `Scripts/PMDG737.lua`.
- IDs, L-Vars and click codes were taken from MobiFlight's HubHop PMDG 737 presets and from the
  CoreFlightTech PMDG 737 MobiFlight configs in the MobiFlight-Connector repository.

## Verification status

This was built without access to MSFS or a Stream Deck, so **nothing has been tested in the sim**.
Here is what was checked:
- Every page's JSON uses the same settings schema as the PilotsDeck author's own XL profiles (GSX Pro package), and every referenced image exists.
- All 492 calculator commands run and terminate in an RPN interpreter. Click sequences for the toggles, 3-position switches, rotaries, IRS and engine start keys were checked against expected positions.
- The Lua script passes `load()`, and every display and command function was unit-tested with mocked PilotsDeck globals.

The table below separates what comes from a working, community-tested config from what is a best guess:

| Status | Items |
| --- | --- |
| From working configs | Fuel pumps, crossfeed, hyd pumps, GENs, GRD PWR, BAT, APU switch, packs, isolation valve, bleeds, wing/engine anti-ice, window/probe heat, yaw damper, all exterior lights and position/strobe, IRS, engine start switches, ignition select, wipers, EFIS buttons/mode/range/minimums/baro knobs, TCAS mode and knobs, XPDR ident, COM/NAV knobs and transfer, FLT/LAND ALT knobs, gear lights, gear DOWN, overhead annunciators |
| From HubHop presets only | MCP button lights (`switch_<ID>1_73X`), MCP window L-Vars, master caution/fire warning lights, six-pack, door annunciators, speedbrake/LE flaps/autobrake lights |
| Best guess, verify | Value-to-text mappings for **belts, no smoking, emergency exit, dome, master lights, retractable landing lights, FLT CTRL A/B, VOR/ADF, start levers (CUTOFF/IDLE), autobrake, pressurization mode**. Direction of **fire test / extinguisher test** keys. **V/S wheel** direction. Custom events for **doors, "all landing lights", "all turnoff", cockpit lights** (`K:#<event>:0x20000000`). Standard events for **flaps, speedbrake arm, park brake, gear up**. **ALT INTV** (885), **TO/GA** (684), **A/T disconnect** (682). Baro display from the sim's Kohlsman setting. Flap display from `FLAPS HANDLE INDEX`. |

If a key does the wrong thing, open it in the Stream Deck app and edit the command or the mapping in the
PilotsDeck property inspector. Or change it in `build.py` and rebuild.

## Rebuilding

```
pip install pillow
python3 pmdg737/build.py      # -> dist/PMDG 737 XL.ppp and dist/PMDG 737 XL.streamDeckProfile
python3 pmdg737/preview.py <path-to-PilotsDeck>/Plugin   # optional: dist/previews/*.png
```

`pmdg.py` has the PMDG ID/RPN helpers, `sd.py` the PilotsDeck action builders, `build.py` the page layouts.
