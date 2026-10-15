import sys
from lupa import LuaRuntime
import os
src = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pmdg737", "package", "Scripts", "PMDG737.lua")).read()
def run(vals):
    lua = LuaRuntime()
    g = lua.globals()
    calls = []
    state = dict(vals)
    def simread(a): return state.get(a, 0)
    def simcalc(code):
        calls.append(code)
        if code.startswith("11801"): state["L:switch_118_73X"] = state.get("L:switch_118_73X",0)+50
        if code.startswith("11802"): state["L:switch_118_73X"] = state.get("L:switch_118_73X",0)-50
    g.SimVar = lambda a: None
    g.SimRead = simread
    g.SimCalculator = simcalc
    g.Sleep = lambda ms: None
    lua.execute(src)
    return lua, calls, state
cases = [
 ({"L:ngx_SPDwindow":250}, "MCP_SPD", "250"),
 ({"L:ngx_SPDwindow":0.78}, "MCP_SPD", ".78"),
 ({"L:ngx_HDGwindow":360}, "MCP_HDG", "000"),
 ({"L:ngx_HDGwindow":5}, "MCP_HDG", "005"),
 ({"L:ngx_ALTwindow":3000}, "MCP_ALT", "03000"),
 ({"L:ngx_VSwindow":-1200}, "MCP_VS", "-1200"),
 ({"L:ngx_VSwindow":800}, "MCP_VS", "+0800"),
 ({"L:ngx_VSwindow":0}, "MCP_VS", "-----"),
 ({"L:ngx_VSwindow":0,"L:switch_3951_73X":1}, "MCP_VS", "0"),
 ({"L:switch_450_73X":1,"L:switch_453_73X":1,"L:switch_454_73X":1}, "GEAR_STATE", 2),
 ({"L:switch_451_73X":1}, "GEAR_STATE", 1),
 ({}, "GEAR_STATE", 0),
 ({"(E:ZULU TIME, number)":3600*13+60*7+5}, "ZULU_CLOCK", "13:07Z"),
]
ok=True
for vals, fn, exp in cases:
    lua, calls, _ = run(vals)
    got = lua.globals()[fn]()
    flag = got == exp
    ok &= flag
    print(("PASS" if flag else "FAIL"), fn, vals, repr(got))
for start, exp_end in [(0, 50), (50, 0), (100, 0)]:
    lua, calls, st = run({"L:switch_118_73X": start})
    lua.globals().APU_START()
    flag = st["L:switch_118_73X"] == exp_end
    ok &= flag
    print(("PASS" if flag else "FAIL"), "APU_START from", start, "->", st["L:switch_118_73X"], calls)
sys.exit(0 if ok else 1)
