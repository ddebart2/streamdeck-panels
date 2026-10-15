# streamdeck-panels

Stream Deck XL profiles for flight simulation, built for PilotsDeck + the MobiFlight WASM module.

| Aircraft | Package | Status |
| --- | --- | --- |
| PMDG 737 (MSFS) | [`dist/PMDG 737 XL.ppp`](dist/PMDG%20737%20XL.ppp) · [README](pmdg737/README.md) | Most controls and lights come from tested community configs. Not yet tested in the sim. |
| PMDG 777 (MSFS) | [`dist/PMDG 777 XL.ppp`](dist/PMDG%20777%20XL.ppp) · [README](pmdg777/README.md) | Early version: buttons follow PMDG's event IDs. Readouts unverified, no annunciator lights. |

Layout: `<aircraft>/build.py` defines the pages, `common/` holds the shared generator, `tests/` holds
offline checks, and `dist/` holds the built packages and page previews.
