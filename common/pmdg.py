"""PMDG (MSFS) control helpers, shared by the 737 and 777 profiles.

Every PMDG cockpit control has an ID (= PMDG SDK event ID - 69632).
  * position is readable through the L-Var  (L:switch_<ID>_<SUFFIX>)   737: 73X, 777: a
  * it is moved with calculator code         <ID><ACTION> (>K:ROTOR_BRAKE)
      ACTION 01 = left click, 02 = right click, 07 = wheel up, 08 = wheel down
On the 737, annunciator lights are also exposed as (L:switch_<N>_73X) and are lit when > 0.

Sources: MobiFlight HubHop PMDG presets, the PMDG event ID lists in the MobiFlight-Connector
repository, and the CoreFlightTech PMDG 737 MobiFlight configs.
"""

PMDG_EVENT_BASE = 69632


class Pmdg:
    def __init__(self, suffix):
        self.suffix = suffix

    def lvar(self, sw_id):
        return f"L:switch_{sw_id:02d}_{self.suffix}"

    def L(self, sw_id):
        return f"({self.lvar(sw_id)}, number)"

    @staticmethod
    def rb(sw_id, action):
        return f"{sw_id * 100 + action} (>K:ROTOR_BRAKE)"

    @staticmethod
    def click(sw_id, action=1, times=1):
        return " ".join([Pmdg.rb(sw_id, action)] * times)

    @staticmethod
    def times(code, n):
        return " ".join([code] * n)

    def toggle(self, sw_id):
        """2-position switch (0 = OFF / 100 = ON): 01 moves it on, 02 moves it off."""
        return (f"{self.L(sw_id)} 50 < if{{ {self.rb(sw_id, 1)} }} "
                f"els{{ {self.rb(sw_id, 2)} }}")

    def goto_rpn(self, sw_id, target_rpn, step, inc, dec):
        """Move a multi-position switch to the position computed by `target_rpn`.
        `inc` is the action that increases the L-Var value, `dec` decreases it."""
        return (f"{target_rpn} {self.L(sw_id)} - {step} div near s0 "
                f":1 l0 0 > if{{ {self.rb(sw_id, inc)} l0 -- s0 g1 }} "
                f"l0 0 < if{{ {self.rb(sw_id, dec)} l0 ++ s0 g1 }}")

    def goto(self, sw_id, target, step, inc=1, dec=2):
        return self.goto_rpn(sw_id, str(target), step, inc, dec)

    def cycle(self, sw_id, step, maxval, inc, dec, minval=0):
        """Next position, wrapping from the last back to the first."""
        L = self.L(sw_id)
        tgt = f"{L} {maxval - step / 2:g} < if{{ {L} {step} + near }} els{{ {minval} }}"
        return self.goto_rpn(sw_id, tgt, step, inc, dec)

    def step_down(self, sw_id, step, minval, inc, dec):
        L = self.L(sw_id)
        tgt = f"{L} {minval + step / 2:g} > if{{ {L} {step} - near }} els{{ {minval} }}"
        return self.goto_rpn(sw_id, tgt, step, inc, dec)

    def toggle_between(self, sw_id, a, b, step, inc, dec):
        """Go to b when the switch is at a, otherwise go to a."""
        tgt = f"{self.L(sw_id)} near {a} == if{{ {b} }} els{{ {a} }}"
        return self.goto_rpn(sw_id, tgt, step, inc, dec)

    @staticmethod
    def custom_event(offset):
        """PMDG custom (shortcut) event, sent as SimConnect event with left-click flag."""
        return f"K:#{PMDG_EVENT_BASE + offset}:0x20000000"
