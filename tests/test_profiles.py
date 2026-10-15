"""Checks every profile without a simulator.

    python3 tests/test_profiles.py [<PilotsDeck>/Plugin]

- every generated calculator (RPN) command runs and terminates in a small RPN interpreter
- multi-position switch helpers move switches to the expected positions
- every PilotsDeck action uses the full settings schema, and every referenced image exists
  (built-in images are only checked when the PilotsDeck Plugin folder is passed)
- no page uses a key twice, page/action IDs are unique across all profiles
"""
import collections
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "common"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import images  # noqa: E402
import sd  # noqa: E402
from pmdg import Pmdg  # noqa: E402
from rpn import run  # noqa: E402

AIRCRAFT = ["pmdg737", "pmdg777"]
PD_PLUGIN = sys.argv[1] if len(sys.argv) > 1 else None
fails = 0


def check(label, ok, detail=""):
    global fails
    if not ok:
        fails += 1
        print("FAIL", label, detail)


def load(aircraft):
    spec = importlib.util.spec_from_file_location(f"build_{aircraft}", os.path.join(ROOT, aircraft, "build.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- RPN helper semantics ----------------------------------------------------------------
P = Pmdg("X")


def moved(code, sid, val, inc, dec, step):
    out, _ = run(code, {P.lvar(sid): val})
    for name, p in out:
        assert name == "ROTOR_BRAKE" and p // 100 == sid, (name, p)
        a = p % 100
        val += step if a == inc else -step if a == dec else 0
    return val


check("toggle on", run(P.toggle(63), {P.lvar(63): 0})[0] == [("ROTOR_BRAKE", 6301)])
check("toggle off", run(P.toggle(63), {P.lvar(63): 100})[0] == [("ROTOR_BRAKE", 6302)])
for v, e in [(0, 50), (50, 100), (100, 0)]:
    check(f"cycle3 {v}", moved(P.cycle(200, 50, 100, 1, 2), 200, v, 1, 2, 50) == e)
for v, e in [(100, 50), (50, 0), (0, 0)]:
    check(f"step_down {v}", moved(P.step_down(200, 50, 0, 1, 2), 200, v, 1, 2, 50) == e)
for v, e in [(0, 10), (60, 70), (70, 0)]:
    check(f"rotary cycle {v}", moved(P.cycle(361, 10, 70, 7, 8), 361, v, 7, 8, 10) == e)
for v, e in [(0, 20), (10, 0), (20, 0), (30, 0)]:
    check(f"toggle_between {v}", moved(P.toggle_between(255, 0, 20, 10, 7, 8), 255, v, 7, 8, 10) == e)
for v, e in [(0, 100), (100, 0)]:
    check(f"goto {v}", moved(P.goto(118, 100 - v, 50), 118, v, 1, 2, 50) == e)

# ---- profiles ----------------------------------------------------------------------------
builtin = set()
if PD_PLUGIN:
    for r, _, fs in os.walk(os.path.join(PD_PLUGIN, "Images")):
        for f in fs:
            builtin.add(os.path.relpath(os.path.join(r, f), PD_PLUGIN).replace(os.sep, "/"))
generated = {n for n in images.ANNUNCIATORS}
keys = set(sd.BASE_SETTINGS)
all_page_ids, all_action_ids = collections.Counter(), collections.Counter()
for aircraft in AIRCRAFT:
    if not os.path.exists(os.path.join(ROOT, aircraft, "build.py")):
        continue
    mod = load(aircraft)
    main, pages = mod.build_pages()
    n_calc = 0
    for p in pages:
        all_page_ids[p.id] += 1
        for pos, a in p.actions.items():
            all_action_ids[a["ActionID"]] += 1
            s = (a.get("Settings") or {}).get("settingsModel")
            if not s:
                continue
            check(f"{aircraft}/{p.name}/{pos} schema", set(s) == keys, set(s) ^ keys)
            for k, v in s.items():
                if isinstance(v, str) and v.startswith("Images/"):
                    if v.startswith(mod.A):
                        check(f"{aircraft}/{p.name}/{pos} {k}", os.path.basename(v)[:-4] in generated, v)
                    elif builtin:
                        check(f"{aircraft}/{p.name}/{pos} {k}", v in builtin, v)
            for f, t in [("AddressAction", "ActionType"), ("AddressActionLong", "ActionTypeLong"),
                         ("AddressActionOff", "ActionType")]:
                code = s.get(f)
                if code and s.get(t) == sd.CALC:
                    for v in (0, 10, 50, 100):
                        try:
                            out, _ = run(code, collections.defaultdict(lambda: v))
                            check(f"{aircraft}/{p.name}/{pos} {f} clicks", len(out) <= 10 or
                                  code.count("ROTOR_BRAKE") >= 5, (code, v, out))
                        except Exception as e:  # noqa: BLE001
                            check(f"{aircraft}/{p.name}/{pos} {f} runs", False, (code, v, e))
                    n_calc += 1
    print(f"{aircraft}: {len(pages)} pages, {sum(len(p.actions) for p in pages)} keys, "
          f"{n_calc} calculator commands executed")
check("unique page ids", all(c == 1 for c in all_page_ids.values()),
      [k for k, c in all_page_ids.items() if c > 1])
check("unique action ids", all(c == 1 for c in all_action_ids.values()),
      [k for k, c in all_action_ids.items() if c > 1][:5])
print("FAILURES:", fails)
sys.exit(1 if fails else 0)
