"""Page model and .ppp packaging shared by all profiles."""
import io
import json
import os
import shutil
import uuid
import zipfile

import images
import sd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
XL_MODEL = "20GAT9901"


class Page:
    def __init__(self, name, parent=None, id_prefix=""):
        self.name = name
        self.id = str(uuid.uuid5(sd.NS, id_prefix + "page/" + name))
        self.actions = {}
        self.images = {}
        if parent is not None:
            self.actions["0,0"] = sd.back()

    def put(self, col, row, action):
        key = f"{col},{row}"
        assert key not in self.actions, f"{self.name}: {key} used twice"
        assert 0 <= col < 8 and 0 <= row < 4, f"{self.name}: {key} out of XL range"
        self.actions[key] = action

    def link(self, col, row, title, child, kind="folder"):
        img = images.sd_image_name()
        self.images[img] = images.folder_icon(kind)
        self.put(col, row, sd.folder(title, child.id, "Images/" + img, size=12))

    def grid(self, rows):
        """rows: list of 4 lists with up to 8 entries (None = empty, 'back' slot skipped)."""
        for r, row in enumerate(rows):
            for c, action in enumerate(row):
                if action is not None and action != "back":
                    self.put(c, r, action)

    def manifest(self):
        return {"Controllers": [{"Actions": self.actions or None, "Type": "Keypad"}],
                "Icon": "", "Name": ""}


def build_profile_zip(profile_name, main, pages, id_prefix=""):
    profile_uuid = str(uuid.uuid5(sd.NS, id_prefix + "profile/" + profile_name)).upper()
    default_page = str(uuid.uuid5(sd.NS, id_prefix + "page/default"))
    base = f"Profiles/{profile_uuid}.sdProfile"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("package.json", json.dumps({
            "AppVersion": "7.1.0.0", "DeviceModel": XL_MODEL, "DeviceSettings": None,
            "FormatVersion": 1, "OSType": "Windows", "OSVersion": "10.0.19045",
            "RequiredPlugins": ["com.extension.pilotsdeck", "com.elgato.streamdeck.profile.backtoparent",
                                "com.elgato.streamdeck.profile.openchild"]}))
        z.writestr(f"{base}/manifest.json", json.dumps({
            "Device": {"Model": XL_MODEL, "UUID": ""},
            "Name": profile_name,
            "Pages": {"Current": "00000000-0000-0000-0000-000000000000", "Default": default_page,
                      "Pages": [main.id]},
            "Version": "3.0"}))
        z.writestr(f"{base}/Profiles/{default_page.upper()}/manifest.json",
                   json.dumps({"Controllers": [{"Actions": None, "Type": "Keypad"}], "Icon": "", "Name": ""}))
        for p in pages:
            pdir = f"{base}/Profiles/{p.id.upper()}"
            z.writestr(f"{pdir}/manifest.json", json.dumps(p.manifest(), ensure_ascii=False))
            for name, im in p.images.items():
                b = io.BytesIO()
                im.save(b, "PNG")
                z.writestr(f"{pdir}/Images/{name}", b.getvalue())
    return buf.getvalue()


def write_package(profile_name, package_name, pkg_src, image_dir, main, pages, id_prefix=""):
    """Writes dist/<package_name> (.ppp) and dist/<profile_name>.streamDeckProfile."""
    profile = build_profile_zip(profile_name, main, pages, id_prefix)

    staging = os.path.join(DIST, "_staging_" + image_dir)
    shutil.rmtree(staging, ignore_errors=True)
    shutil.copytree(pkg_src, staging)
    images.write_annunciators(os.path.join(staging, "Images", image_dir))
    os.makedirs(os.path.join(staging, "Profiles"), exist_ok=True)
    with open(os.path.join(staging, "Profiles", f"{profile_name}.streamDeckProfile"), "wb") as f:
        f.write(profile)

    out = os.path.join(DIST, package_name)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(staging):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, staging).replace(os.sep, "/"))
    shutil.copy(os.path.join(staging, "Profiles", f"{profile_name}.streamDeckProfile"),
                os.path.join(DIST, f"{profile_name}.streamDeckProfile"))
    shutil.rmtree(staging)

    total = sum(len(p.actions) for p in pages)
    print(f"{len(pages)} pages, {total} keys -> {out}")
