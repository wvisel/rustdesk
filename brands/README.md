# White-label builds (SentinelOps)

This fork builds RustDesk 1.5.0 under an MSP's own name, icon and settings.
Branch `sentinelops/1.5.0` is upstream tag `1.5.0` plus three small changes:

| Change | Where | Effect when no brand is applied |
|---|---|---|
| Embedded brand config, read before (and instead of) `custom.txt` | `src/common.rs` `apply_embedded_brand` | none: `res/brand/brand.json` is `{}` |
| `enforce-e2ee` option: refuse a connection whose peer identity did not verify, instead of offering "continue insecure" | `src/common.rs` `is_insecure_connection_refused`, hook in `src/client/io_loop.rs` | none: the option is unset |
| Brand packs, apply script, Windows workflow | `brands/`, `.github/workflows/sentinelops-branded-windows.yml` | not part of the build |

## Make a brand

1. Copy `brands/sentinelops/` to `brands/<msp-id>/` (letters, digits, `-`, `_`).
2. Edit `brand.json`:
   - `app-name`: 3 to 32 letters/digits, no spaces (`AcmeRemote`). It becomes the
     exe name, the config folder (`%APPDATA%\<app-name>`), the service name and
     the link scheme. Changing it later makes a different product on the PC.
   - `display`: product name, description, company and copyright shown in
     the exe's properties and the installer.
   - `override-settings`: locked settings (same keys as RustDesk's custom
     client). To pin an MSP's own servers add `custom-rendezvous-server`,
     `relay-server` and `key`. Keep `enforce-e2ee: Y`.
   - `default-settings`: initial values the user may change.
3. Replace `icon.ico` (16 to 256 px), `icon.png` (256 px) and optionally
   `logo.png`, `logo_light.png`, `logo_dark.png`.
4. Run **Actions → SentinelOps branded Windows build → Run workflow**, brand
   `<msp-id>`. Output: `<app-name>-1.5.0-x86_64.exe` (portable) and `.msi`,
   with `SHA256SUMS`, attached to a prerelease.

## Code signing

Without signing secrets the build is unsigned (SmartScreen will warn). Add
repository secrets `WINDOWS_SIGN_PFX_BASE64` (base64 of the .pfx) and
`WINDOWS_SIGN_PASSWORD` to sign every exe, dll and installer with the MSP's
certificate.

## Using a branded build in SentinelOps

- Technician app: stamp `engine.OverrideName`, `OverrideSHA256`, `OverrideURL`
  and `OverrideAppName` (= `app-name`) at build time
  (`scripts/build-branded.sh` in the sentinelops-support repo).
- Endpoint agent: install the branded `.msi` instead of upstream's; its config
  folder and service follow `app-name` (spec handed to the agent thread).

## Licence

RustDesk is AGPL-3.0. Anyone you distribute a branded build to (MSPs, their
technicians, their customers' PCs) must be able to get this fork's source at
the commit it was built from; the release notes link it. Keep `LICENCE` and
upstream copyright notices in the source. The SentinelOps Support app and the
endpoint agent run RustDesk as a separate program and are not covered by it.
