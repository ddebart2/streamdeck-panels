# PMDG 777 (MSFS) – Stream Deck XL profile for PilotsDeck

**Early version.** This uses the same layout and tools as the [737 profile](../pmdg737/README.md): PilotsDeck plus
the MobiFlight WASM module, a main page with camera views, Gate/Taxi/Flight/Cruise pages and system
folders. It rests on less verified data than the 737, so read [What is and isn't verified](#what-is-and-isnt-verified) first.

Download: [`dist/PMDG 777 XL.ppp`](../dist/PMDG%20777%20XL.ppp). Page previews: [`dist/previews/pmdg777`](../dist/previews/pmdg777).

## Install

Same as the 737: drop the `.ppp` on the PilotsDeck Profile Manager, install the profile to your XL,
and optionally map it to the aircraft string `PMDG 777`. Camera keys use vJoy device 1, buttons 1–12.
See the [737 README](../pmdg737/README.md#install) for details.

## Layout

| Page | Contents |
| --- | --- |
| **Main** | 12 camera views · Master warning/caution reset · EICAS CANC/RCL · Park brake · Gear · phase folders · Lights, MCP, EFIS, GSX, Overhead, MIP, Pedestal, CDU · UTC · VHF L · XPDR · TCAS mode |
| **Gate** | Battery, APU, APU GEN, EXT PWR PRI/SEC, ADIRU, packs, bleeds, main tank pumps, beacon/nav/logo/wing, belts, no smoking, GEN 1/2, doors 1L/2L/1R/2R, cargo doors, park brake |
| **Taxi** | Taxi/turnoff/landing lights, strobe, beacon, engine start, autostart, fuel control switches, APU and bleed, packs, flaps, autobrake, TCAS, anti-ice, EICAS ENG/CHKL/FCTL/STAT |
| **Flight** | Gear, flaps, speedbrake arm, autobrake, lights, belts, TO/GA, A/T and A/P disconnect, A/P, A/T ARM, CLB/CON, A/T, FLCH, VNAV, LNAV, LOC, APP, HDG HOLD, MCP windows |
| **Cruise** | Belts, center pumps, crossfeeds, anti-ice, LAND ALT, EICAS FUEL/STAT/CANC-RCL, EFIS range/mode/WXR/TERR/TFC, VHF L, XPDR, MCP windows, ALT knob |
| **Overhead** | Battery, APU GEN, APU selector, bus ties, external power, GENs and backup GENs, fuel pumps, crossfeeds, primary and demand hydraulic pumps, equipment cooling, recirc fans → **Overhead 2** |
| **Overhead 2** | Engine start, autostart, EEC, wipers, window heat, wing/engine anti-ice, ADIRU, packs, trim air, bleeds, gasper, isolation valves, outflow valves, LAND ALT, thrust asymmetry compensation |
| **Lights** | L/nose/R landing, turnoff, taxi, beacon, nav, logo, wing, strobe, storm, all landing/turnoff/cockpit/panel/flood light shortcuts, belts, no smoking, emergency lights, dome, indicator lights test |
| **MCP** | All MCP buttons, SPD/HDG/ALT/V/S windows with +/- keys, F/D switches, bank limit, A/P disengage bar, TO/GA, disconnects |
| **EFIS** | Captain EFIS, display select (L/R inboard, lower center), G/S inhibit, nav source, chrono |
| **MIP** | Gear, autobrake, park brake, flaps, speedbrake, disconnects, all EICAS display-select keys (ENG, STAT, ELEC, HYD, FUEL, AIR, DOOR, GEAR, FCTL, CAM, CHKL, COMM, NAV, CANC/RCL), UTC |
| **Pedestal** | VHF L/R (display, press to swap, MHz/kHz keys), transponder and TCAS, fuel control switches, rudder/aileron trim, fire/overheat test, cargo fire arm, TCAS test |
| **CDU** | Left CDU with 0-9 and A-Z pages |
| **GSX** | Fragtality's GSX Pro menu |

Window keys: on SPD a short press = speed knob push (intervention) and a long press = IAS/MACH. On HDG, short = HDG SEL and long = HDG/TRK. On ALT, short = altitude knob push and long = AUTO/1000 increment. On V/S, short = V/S mode and long = V/S-FPA.

## What is and isn't verified

Nothing has been tested in the sim. Offline checks pass:
- every control ID used appears in PMDG's 777 event list
- all 467 calculator commands run in an RPN interpreter
- the Lua script passes its unit tests
- the page files match the schema used by the 737 profile

| Status | Items |
| --- | --- |
| **Likely to work** | Button presses on the overhead, MCP, EFIS, EICAS display select, CDU, pedestal and lights. They use PMDG's own control IDs (event ID − 69632) with the same `ROTOR_BRAKE` scheme that works on the 737. One forum report confirms the beacon (ID 114, code `11401`). |
| **Unverified – readouts** | Switch-position readouts (the "ON" / OFF / AUTO text) assume the L-Var name `L:switch_<ID>_a`. That comes from a single forum post about the beacon. Value scales (0/100, 0/10/20…) and the text mappings are carried over from the 737. Alternate-action push buttons may report "pressed", not ON/OFF. |
| **Unverified – MCP windows** | Read from the simulator's standard autopilot variables (`AUTOPILOT AIRSPEED HOLD VAR`, `HEADING LOCK DIR`, `ALTITUDE LOCK VAR`, `VERTICAL HOLD VAR`). The PMDG 777 may not keep these in sync. |
| **Unverified – commands** | Controls with 4-digit IDs: MCP knobs and knob pushes (2100, 2180, 2181, 2250, 2251), yoke A/P disconnect (1084), TCAS test (7491). Standard sim events for flaps, gear, park brake and speedbrake arm. Door and light-shortcut custom events. The APU selector start sequence. |
| **Not included** | Annunciator lights. I have no verified light variables for the 777, so keys show switch position only and MCP buttons have no lit bar. |

### What would fix the gaps

Send the 777's **L-Var list**. One way is FSUIPC7 → Add-ons → WASM → List Lvars with the 777 loaded; the list goes to the FSUIPC7 log. Another is LORBY AAO's L-Var CSV export. With that list I can confirm the switch-variable names and value scales, and add the MCP windows and annunciator lights. If only the suffix is wrong, it's a one-line fix in `build.py` (`P = Pmdg("a")`).

## Rebuilding

```
python3 pmdg777/build.py
python3 common/preview.py pmdg777 <path-to-PilotsDeck>/Plugin   # optional previews
python3 tests/test_profiles.py && python3 tests/test_lua_pmdg777.py
```
