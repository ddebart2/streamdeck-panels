"""PMDG 737 (MSFS) control definitions.

Every PMDG 737 cockpit control has an ID (= PMDG SDK event ID - 69632).
  * position is readable through the L-Var  (L:switch_<ID>_73X)
  * it is moved with calculator code         <ID><ACTION> (>K:ROTOR_BRAKE)
      ACTION 01 = left click, 02 = right click, 07 = wheel up, 08 = wheel down
Annunciator lights are also exposed as (L:switch_<N>_73X) and are lit when > 0.

Sources: MobiFlight HubHop PMDG 737 presets and the CoreFlightTech PMDG 737
MobiFlight configs (MobiFlight-Connector repository).
"""

PMDG_EVENT_BASE = 69632


def lvar(sw_id):
    return f"L:switch_{sw_id:02d}_73X"


def rb(sw_id, action):
    return f"{sw_id * 100 + action} (>K:ROTOR_BRAKE)"


def click(sw_id, action=1, times=1):
    return " ".join([rb(sw_id, action)] * times)


def toggle(sw_id):
    """2-position switch (0 = OFF / 100 = ON): 01 moves it on, 02 moves it off."""
    return (f"({lvar(sw_id)}, number) 50 < if{{ {rb(sw_id, 1)} }} "
            f"els{{ {rb(sw_id, 2)} }}")


def goto(sw_id, target, step, inc=1, dec=2):
    """Move a multi-position switch to `target` (positions are multiples of `step`).
    `inc` is the action that increases the L-Var value, `dec` decreases it."""
    return (f"{target} ({lvar(sw_id)}, number) - {step} div near s0 "
            f":1 l0 0 > if{{ {rb(sw_id, inc)} l0 -- s0 g1 }} "
            f"l0 0 < if{{ {rb(sw_id, dec)} l0 ++ s0 g1 }}")


def custom_event(offset):
    """PMDG custom (shortcut) event, sent as SimConnect event with left-click flag."""
    return f"K:#{PMDG_EVENT_BASE + offset}:0x20000000"
