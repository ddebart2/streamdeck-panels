"""Builders for Stream Deck (7.x profile format) actions using the PilotsDeck plugin."""
import copy
import uuid

# PilotsDeck SimCommandType values
LVAR, VJOYDRV, CALC, LUA, KVAR = 3, 7, 9, 14, 16

PLUGIN = {"Name": "PilotsDeck", "UUID": "com.extension.pilotsdeck", "Version": "0.9.1.0"}
NS = uuid.UUID("6f1c4a52-5f0e-4b55-9a7e-737737737737")

# defaults of PilotsDeck's SettingsModelSimple (BUILD_VERSION 10 = PilotsDeck 0.9.x)
BASE_SETTINGS = {
    "ActionType": CALC, "ActionTypeGuard": CALC, "ActionTypeLeft": CALC, "ActionTypeLong": CALC,
    "ActionTypeRight": CALC, "ActionTypeTouch": CALC,
    "Address": "", "Address2": "", "AddressAction": "", "AddressActionGuard": "",
    "AddressActionGuardOff": "", "AddressActionLeft": "", "AddressActionLong": "",
    "AddressActionOff": "", "AddressActionRight": "", "AddressActionTouch": "", "AddressBot": "",
    "AddressColorOff": "", "AddressGuardActive": "", "AddressMonitor": "", "AddressRadioActiv": "",
    "AddressRadioStandby": "", "AddressTop": "",
    "BUILD_VERSION": 10, "BarOrientation": 0,
    "BotImage": "Images/korry/A-ON-Blue.png", "BotRect": "9; 45; 54; 20", "BotState": "",
    "BoxColor": "#ffffff", "BoxRect": "9; 21; 54; 44", "BoxSize": "2",
    "CenterLine": False, "CenterLineColor": "#ffffff", "CenterLineThickness": "2",
    "CriticalColor": "#8b0000", "CriticalRange": "0; 10",
    "DecodeBCD": False, "DecodeBCDStby": False,
    "DefaultImage": "Images/Switch.png", "DefaultRect": "72; 72", "DoNotRequestBvar": True,
    "DrawArc": False, "DrawBox": False, "DrawWarnRange": False,
    "FontColor": "#ffffff", "FontColorStby": "#e0e0e0", "FontInherit": True, "FontName": "Arial",
    "FontSize": "12", "FontStyle": 0, "Format": "", "FormatStby": "",
    "GaugeColor": "#006400", "GaugeColorOff": "#636363", "GaugeSize": "58; 10",
    "GuardActiveValue": "", "GuardRect": "0; 0; 72; 72",
    "HasAction": True, "HasIndication": False, "HasLongPress": False, "HoldSwitch": False,
    "ImageGuard": "Images/GuardCross.png", "ImageGuardMap": "", "ImageMap": "", "ImageMapBot": "",
    "IndicationColor": "#ffcc00", "IndicationHideValue": False, "IndicationImage": "",
    "IndicationTime": "1500", "IndicationUseColor": False, "IndicationValue": "0",
    "IndicationValueAny": False, "IndicatorColor": "#c7c7c7", "IndicatorFlip": False,
    "IndicatorSize": "10", "IsEncoder": False, "IsGuarded": False, "IsNewModel": False,
    "MaximumValue": "100", "MinimumValue": "0",
    "OffImage": "Images/KorryOffWhiteBottom.png", "OffState": "", "Offset": "0; 0",
    "OnImage": "Images/KorryOnBlueTop.png", "OnState": "",
    "RectCoord": "-1; 0; 0; 0", "RectCoord2": "6; 6; 60; 21", "RectCoordStby": "3; 42; 64; 31",
    "Scalar": "1", "ScalarStby": "1", "ShowBotImage": True, "ShowBotNonZero": False,
    "ShowText": True, "ShowTopImage": True, "ShowTopNonZero": False,
    "StartAngle": "135", "StateColorOff": "", "StbyHasDiffFormat": False, "SweepAngle": "180",
    "SwitchOffState": "0", "SwitchOffStateGuard": "", "SwitchOffStateLeft": "",
    "SwitchOffStateLong": "0", "SwitchOffStateRight": "", "SwitchOffStateTouch": "",
    "SwitchOnCurrentValue": False, "SwitchOnState": "0", "SwitchOnStateGuard": "",
    "SwitchOnStateLeft": "", "SwitchOnStateLong": "0", "SwitchOnStateRight": "",
    "SwitchOnStateTouch": "", "SymmRange": False, "ToggleSwitch": False,
    "TopImage": "Images/korry/A-FAULT.png", "TopRect": "9; 21; 54; 20", "TopState": "",
    "UseColorSwitching": False, "UseControlDelay": False, "UseImageGuardMapping": False,
    "UseImageMapping": False, "UseLvarReset": False, "UseOnlyTopAddr": False,
    "UseWarnColors": True, "UseXpCommandOnce": True, "ValueMappings": "",
    "WarnColor": "#ff8c00", "WarnRange": "10; 20",
}

_counter = [0]


def _uid(*parts):
    _counter[0] += 1
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts) + f"#{_counter[0]}"))


def _state(title, align="middle", size=11, style="Bold", color="#ffffff", image=None, show=True):
    st = {
        "FontFamily": "Arial", "FontSize": size, "FontStyle": style, "FontUnderline": False,
        "OutlineThickness": 2, "ShowTitle": show, "Title": title,
        "TitleAlignment": align, "TitleColor": color,
    }
    if image:
        st["Image"] = image
    return st


def _pd_action(uuid_, name, settings, state):
    return {
        "ActionID": _uid(uuid_, name, state.get("Title", "")),
        "LinkedTitle": False,
        "Name": name,
        "Plugin": dict(PLUGIN),
        "Resources": None,
        "Settings": {"settingsModel": settings},
        "State": 0,
        "States": [state],
        "UUID": uuid_,
    }


def _settings(cmd, cmd_type=CALC, long=None, long_type=None, **kw):
    s = copy.deepcopy(BASE_SETTINGS)
    if cmd:
        s["AddressAction"] = cmd
        s["ActionType"] = cmd_type
    else:
        s["HasAction"] = False
    if long:
        s["HasLongPress"] = True
        s["AddressActionLong"] = long
        s["ActionTypeLong"] = long_type if long_type is not None else cmd_type
    s.update(kw)
    return s


def button(title, cmd, cmd_type=CALC, long=None, long_type=None, image="Images/Switch.png",
           size=11, color="#ffffff"):
    """Simple Button: runs `cmd` on press (and `long` on press >= 500ms)."""
    s = _settings(cmd, cmd_type, long, long_type, DefaultImage=image)
    return _pd_action("com.extension.pilotsdeck.action.switch", "Simple Button", s,
                      _state(title, "middle", size, color=color))


def hold_button(title, cmd_down, cmd_up, cmd_type=CALC, image="Images/Switch.png", size=11):
    """Simple Button with Hold Switch: `cmd_down` on key down, `cmd_up` on key up."""
    s = _settings(cmd_down, cmd_type, HoldSwitch=True, AddressActionOff=cmd_up, DefaultImage=image)
    return _pd_action("com.extension.pilotsdeck.action.switch", "Simple Button", s,
                      _state(title, "middle", size))


def vjoy(title, joystick, btn):
    s = _settings(f"{joystick}:{btn}", VJOYDRV, DefaultImage="Images/View.png",
                  SwitchOnState="", SwitchOffState="", SwitchOnStateLong="", SwitchOffStateLong="")
    return _pd_action("com.extension.pilotsdeck.action.switch", "Simple Button", s,
                      _state(title, "middle", 11))


def korry(title, cmd, top=None, bot=None, long=None, cmd_type=CALC, long_type=None,
          image="Images/SwitchBlack.png", size=10):
    """Korry Button: `top` / `bot` are (address, state, image) tuples or None.
    The sub-image is shown while the value of address matches state (comparisons allowed)."""
    kw = {"DefaultImage": image, "DefaultRect": "72; 72"}
    if top:
        kw.update(AddressTop=top[0], TopState=top[1], TopImage=top[2])
    else:
        kw.update(ShowTopImage=False)
    if bot:
        kw.update(AddressBot=bot[0], BotState=bot[1], BotImage=bot[2])
    else:
        kw.update(ShowBotImage=False)
    s = _settings(cmd, cmd_type, long, long_type, **kw)
    return _pd_action("com.extension.pilotsdeck.action.switch.korry", "Korry Button", s,
                      _state(title, "top", size))


def display(title, address, cmd=None, long=None, mappings="", fmt="", cmd_type=CALC,
            long_type=None, box=True, font="Arial", font_size="12", color="#ffffff",
            style=1, scalar="1", special=None, image="Images/Empty.png", title_size=10,
            rect=None):
    """Display Value (with Switch): draws the value of `address`, optional mapping value=Text.
    `special` = (value/comparison, color) draws the text in another color in that state."""
    kw = {
        "Address": address, "ValueMappings": mappings, "Format": format_str(fmt),
        "DrawBox": box, "DefaultImage": image, "DefaultRect": "0; 0", "Scalar": scalar,
        "FontInherit": False, "FontName": font, "FontSize": font_size, "FontColor": color,
        "FontStyle": style, "IndicationImage": "Images/Empty.png",
        "RectCoord": "-1; 0; 0; 0" if box else (rect or "-1; 14; 72; 58"),
    }
    if special:
        kw.update(HasIndication=True, IndicationValue=special[0], IndicationUseColor=True,
                  IndicationColor=special[1])
    s = _settings(cmd, cmd_type, long, long_type, **kw)
    return _pd_action("com.extension.pilotsdeck.action.display.switch", "Display Value", s,
                      _state(title, "top", title_size))


def format_str(fmt):
    return fmt or ""


def dynamic(title, address, on_state, off_state, on_img, off_img, cmd=None, long=None,
            cmd_type=CALC, long_type=None, special=None, special_img=None, image="Images/Empty.png",
            align="bottom", size=11, any_special=False):
    """Dynamic Button: shows on_img/off_img (and optional special image) depending on address."""
    kw = {"Address": address, "OnState": on_state, "OffState": off_state, "OnImage": on_img,
          "OffImage": off_img, "DefaultImage": image}
    if special is not None or any_special:
        kw.update(HasIndication=True, IndicationValue=special or "", IndicationImage=special_img,
                  IndicationValueAny=any_special)
    s = _settings(cmd, cmd_type, long, long_type, **kw)
    return _pd_action("com.extension.pilotsdeck.action.switch.display", "Dynamic Button", s,
                      _state(title, align, size))


def radio(title, active, standby, cmd=None, scalar="1", fmt="", cmd_type=CALC, long=None,
          font_size="11"):
    kw = {"AddressRadioActiv": active, "AddressRadioStandby": standby, "Scalar": scalar,
          "Format": fmt, "DefaultImage": "Images/Arrow.png", "IndicationImage": "Images/ArrowBright.png",
          "FontInherit": False, "FontName": "Arial", "FontSize": font_size, "FontColor": "#ffb000",
          "FontColorStby": "#e0e0e0", "FontStyle": 1, "RectCoord": "3; 1; 64; 31",
          "RectCoordStby": "3; 42; 64; 31", "DefaultRect": "0; 0"}
    s = _settings(cmd, cmd_type, long, None, **kw)
    return _pd_action("com.extension.pilotsdeck.action.display.radio", "COM Radio", s,
                      _state(title, "middle", 9, show=False))


def folder(title, page_id, image=None, size=11):
    return {
        "ActionID": _uid("folder", title),
        "LinkedTitle": False,
        "Name": "Create Folder",
        "Plugin": {"Name": "Create Folder", "UUID": "com.elgato.streamdeck.profile.openchild",
                   "Version": "1.0"},
        "Resources": None,
        "Settings": {"ProfileUUID": page_id},
        "State": 0,
        "States": [_state(title, "bottom" if image else "middle", size, image=image)],
        "UUID": "com.elgato.streamdeck.profile.openchild",
    }


def back():
    return {
        "ActionID": _uid("back"),
        "LinkedTitle": True,
        "Name": "Parent Folder",
        "Plugin": {"Name": "Open Parent Folder", "UUID": "com.elgato.streamdeck.profile.backtoparent",
                   "Version": "1.0"},
        "Resources": None,
        "Settings": {},
        "State": 0,
        "States": [{}],
        "UUID": "com.elgato.streamdeck.profile.backtoparent",
    }
