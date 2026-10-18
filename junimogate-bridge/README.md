# SMAPI Aurora × JunimoGate — source integration

## Status

**Source integration validated. This is not an Android release.**

Aurora is adopting the open-source JunimoGate architecture for a real on-device
SMAPI runtime. The new bridge is an **application/UI overlay**, not an APK
rebadging trick. The exact JunimoGate upstream commit is:

`029eafed917ae853d6c0a59330ee273524168296`

The bridge clone, transformation, and Android XML consistency checks execute
in [Aurora JunimoGate bridge validation](../.github/workflows/junimogate-bridge.yml).
No commercial game files are included or distributed.

### Verified CI gates

- [Pinned source overlay and XML integration PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39176471760) — validates original JunimoGate commit, Aurora resource links, app identity, Russian selector, and that game/runtime/license files stay untouched.
- [Platform-neutral JunimoGate host suites PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39176757497) — separately compiles and executes the public-dependency Core, Extraction, Rewriter and Mods tests after applying the Aurora overlay.
- **Not tested:** Android assembly compilation, game execution, physical-device SMAPI and mod loading.

## What the first integration implements

- Keeps JunimoGate's existing `JunimoGate.GameHost`, GameHostBridge,
  extraction, rewriter, SMAPI fork, mod groups, saves, and logging code unchanged.
- Gives the derived APK its own `com.marocto.smapi.aurora.jg` application ID
  (the upstream CLR/Java class namespaces remain unchanged for compatibility).
- Applies Aurora's midnight-violet/mint Material3 resource palette in both
  light and night resource qualifiers.
- Replaces the home backdrop, brand visual and adaptive app icon with
  original vector resources.
- Adds the Aurora banner to the home dashboard and changes the app's visible name.
- Adds Russian translations for launch status, navigation, game-preparation
  diagnostics and some mod-management surfaces.
- Wires Russian into the explicit Android language selector (English and Chinese remain).
- Points in-app release links and update checks to Aurora releases, not JunimoGate.
- Preserves JunimoGate licensing and creator attribution explicitly.

This is still an incremental localization; untranslated settings and mod text
fall back to English. It is not yet a pixel-perfect transplant of every v0.6
Preview interaction.

## Reproduce the source overlay

```bash
git clone https://github.com/marocto1/SMAPI-Aurora.git
cd SMAPI-Aurora
git clone https://github.com/leontismaro/JunimoGate.git .aurora-build/JunimoGate
git -C .aurora-build/JunimoGate checkout 029eafed917ae853d6c0a59330ee273524168296
python3 -m unittest discover -s junimogate-bridge/tests -v
python3 junimogate-bridge/apply_aurora.py .aurora-build/JunimoGate --check
python3 junimogate-bridge/apply_aurora.py .aurora-build/JunimoGate --apply
```

The application overlay refuses to patch a source tree at another commit or
with local modifications. It modifies only `src/JunimoGate.App/`. Upstream
game execution checks and signing identity policies are **not** bypassed.

## Binary and Android test blockers

JunimoGate's original source build also requires legally extracted **mobile**
game compilation references, as documented in
[the upstream build guide](https://github.com/leontismaro/JunimoGate/blob/main/docs/build-environment.md).
These are compile-time inputs, not a license to embed paid game data into the APK.
The existing public desktop reference assemblies are missing Android-specific
Stardew Valley types and cannot substitute for the mobile references.

In addition, a full build needs the pinned Android toolchain, SMAPI submodule,
MonoGame source/bindings, patched Harmony/MonoMod runtime, and signing.
Only after it builds should an Android ARM64 device test cover initial extraction,
SMAPI game startup, mods, saves, and error recovery.

**No full Aurora-with-SMAPI APK has been produced or device-tested.**
The separate [v0.6.1 Preview](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.6.1-preview)
remains an installable native companion, but launches the ordinary game without SMAPI.

JunimoGate currently validates installed-game package and signer identities.
Therefore, a third-party APK is not guaranteed to pass compatibility checks.
Do not imply arbitrary repackaged APKs are supported or bypass signature enforcement.

## Licensing

JunimoGate source is GPL-3.0-only plus its **specific** MonoGame linking
exception. Its SMAPI fork is LGPL-3.0-only, while additional dependencies have
independent licenses. Aurora does not delete or replace license files or
copyright notices, and any distributable APK must include the corresponding
source, license notices, exact upstream commit, and relevant LGPL provisions.

See [JunimoGate source](https://github.com/leontismaro/JunimoGate),
[upstream license exception](https://github.com/leontismaro/JunimoGate/blob/main/LICENSE-EXCEPTION),
and [upstream open-source release requirements](https://github.com/leontismaro/JunimoGate/blob/main/docs/open-source-release.md).

The new overlay script and original Aurora UI resources are distributed
under the SMAPI Aurora repository's GPL-3.0 license.
