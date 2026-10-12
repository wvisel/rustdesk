#!/usr/bin/env python3
"""Apply a brand pack to this source tree before a build.

Usage: python3 brands/apply.py brands/<id> [--github-env FILE]

A brand pack is a folder with:
  brand.json   app-name, display{product, description, company, copyright},
               default-settings{}, override-settings{} (custom.txt keys)
  icon.ico     multi-size Windows icon (16..256)
  icon.png     256x256 PNG
  logo.png     optional, shown on the home page
  logo_light.png / logo_dark.png   optional theme variants

What it changes (all build-time; nothing is committed back):
  res/brand/brand.json           compiled into the binary (src/common.rs)
  res/icon.ico, res/tray-icon.ico, flutter/windows/runner/resources/app_icon.ico
  res/icon.png, flutter/assets/icon.png, flutter/assets/logo*.png
  flutter/windows/runner/Runner.rc version strings
It prints APP_NAME for the workflow (and appends it to --github-env).
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{2,31}$")
SAFE_TEXT_RE = re.compile(r'^[^"\\\r\n]{1,100}$')


def fail(msg):
    print(f"brand: {msg}", file=sys.stderr)
    sys.exit(1)


def rc_value(text, key, value):
    pat = re.compile(r'(VALUE "' + re.escape(key) + r'", )"[^"]*"')
    if not pat.search(text):
        fail(f"Runner.rc has no {key}")
    return pat.sub(lambda m: m.group(1) + '"' + value + '"', text)


def main():
    if len(sys.argv) < 2:
        fail(__doc__)
    pack = Path(sys.argv[1]).resolve()
    github_env = None
    if "--github-env" in sys.argv:
        github_env = sys.argv[sys.argv.index("--github-env") + 1]
    if not (pack / "brand.json").is_file():
        fail(f"{pack} has no brand.json")
    brand = json.loads((pack / "brand.json").read_text(encoding="utf-8"))
    app = brand.get("app-name", "")
    if not APP_NAME_RE.match(app) or app.lower() == "rustdesk":
        fail("app-name must be 3-32 letters/digits, start with a letter, and not be RustDesk")
    display = brand.get("display", {})
    product = display.get("product", app)
    description = display.get("description", product)
    company = display.get("company", product)
    copyright_ = display.get("copyright", f"Copyright (C) {company}. Based on RustDesk (AGPL-3.0).")
    for v in (product, description, company, copyright_):
        if not SAFE_TEXT_RE.match(v):
            fail(f"display text {v!r} is empty, too long, or has quotes/backslashes/newlines")
    for section in ("default-settings", "override-settings"):
        s = brand.get(section, {})
        if not isinstance(s, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in s.items()):
            fail(f"{section} must be an object of string values")

    embedded = {"app-name": app}
    for section in ("default-settings", "override-settings"):
        if brand.get(section):
            embedded[section] = brand[section]
    (ROOT / "res/brand/brand.json").write_text(json.dumps(embedded, indent=2) + "\n", encoding="utf-8")

    icon_ico = pack / "icon.ico"
    icon_png = pack / "icon.png"
    if not icon_ico.is_file() or not icon_png.is_file():
        fail("brand pack needs icon.ico and icon.png")
    tray = pack / "tray-icon.ico"
    for dst in ("res/icon.ico", "flutter/windows/runner/resources/app_icon.ico"):
        shutil.copyfile(icon_ico, ROOT / dst)
    shutil.copyfile(tray if tray.is_file() else icon_ico, ROOT / "res/tray-icon.ico")
    for dst in ("res/icon.png", "flutter/assets/icon.png"):
        shutil.copyfile(icon_png, ROOT / dst)
    for logo in ("logo.png", "logo_light.png", "logo_dark.png"):
        if (pack / logo).is_file():
            shutil.copyfile(pack / logo, ROOT / "flutter/assets" / logo)

    rc_path = ROOT / "flutter/windows/runner/Runner.rc"
    rc = rc_path.read_text(encoding="utf-8")
    rc = rc_value(rc, "CompanyName", company)
    rc = rc_value(rc, "FileDescription", description)
    rc = rc_value(rc, "InternalName", app.lower())
    rc = rc_value(rc, "LegalCopyright", copyright_)
    rc = rc_value(rc, "OriginalFilename", app + ".exe")
    rc = rc_value(rc, "ProductName", product)
    rc_path.write_text(rc, encoding="utf-8")

    print(f"APP_NAME={app}")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as f:
            f.write(f"APP_NAME={app}\nAPP_PRODUCT={product}\nAPP_COMPANY={company}\n")


if __name__ == "__main__":
    main()
