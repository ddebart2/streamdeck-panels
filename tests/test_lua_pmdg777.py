"""Unit tests for pmdg777/package/Scripts/PMDG777.lua with mocked PilotsDeck globals (needs lupa)."""
import os
import sys

from lupa import LuaRuntime

SRC = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "pmdg777", "package", "Scripts", "PMDG777.lua")).read()


def run(vals):
    lua = LuaRuntime()
    g = lua.globals()
    calls, state = [], dict(vals)

    def simcalc(code):
        calls.append(code)
        if code.startswith("307"):
            state["L:switch_03_a"] = min(state.get("L:switch_03_a", 0) + 10, 20)
        if code.startswith("308"):
            state["L:switch_03_a"] = max(state.get("L:switch_03_a", 0) - 10, 0)

    g.SimVar = lambda a: None
    g.SimRead = lambda a: state.get(a, 0)
    g.SimCalculator = simcalc
    g.Sleep = lambda ms: None
    lua.execute(SRC)
    return lua, calls, state


SPD, MACH, MM = ("(A:AUTOPILOT AIRSPEED HOLD VAR, knots)", "(A:AUTOPILOT MACH HOLD VAR, number)",
                 "(A:AUTOPILOT MANAGED SPEED IN MACH, bool)")
G = ["(A:GEAR CENTER POSITION, percent)", "(A:GEAR LEFT POSITION, percent)", "(A:GEAR RIGHT POSITION, percent)"]
cases = [
    ({SPD: 250}, "MCP_SPD", "250"),
    ({MACH: 0.84, MM: 1}, "MCP_SPD", ".840"),
    ({"(A:AUTOPILOT HEADING LOCK DIR, degrees)": 359.6}, "MCP_HDG", "000"),
    ({"(A:AUTOPILOT ALTITUDE LOCK VAR, feet)": 35000}, "MCP_ALT", "35000"),
    ({"(A:AUTOPILOT VERTICAL HOLD VAR, feet per minute)": -1500}, "MCP_VS", "-1500"),
    ({g: 100 for g in G}, "GEAR_STATE", 2),
    ({G[0]: 50}, "GEAR_STATE", 1),
    ({}, "GEAR_STATE", 0),
]
ok = True
for vals, fn, exp in cases:
    lua, _, _ = run(vals)
    got = lua.globals()[fn]()
    ok &= got == exp
    print("PASS" if got == exp else "FAIL", fn, repr(got))
for start, end in [(0, 10), (10, 0), (20, 0)]:
    lua, calls, st = run({"L:switch_03_a": start})
    lua.globals().APU_START()
    ok &= st["L:switch_03_a"] == end
    print("PASS" if st["L:switch_03_a"] == end else "FAIL", "APU_START", start, "->", st["L:switch_03_a"], calls)
sys.exit(0 if ok else 1)
