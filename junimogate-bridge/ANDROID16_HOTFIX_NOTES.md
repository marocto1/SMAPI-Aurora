# SMAPI Aurora v0.8.1 — Android 16 split APK preparation hotfix (QA)

**Experimental ARM64 APK. Compiled, APK-signed and byte-audited, but NOT yet tested on the affected Android 16 handset.**

## What was diagnosed

In the user-supplied Android 16 launcher log, SMAPI failed before inspecting any game APK payload:

```text
JunimoGate.DeepPrepare: System.InvalidOperationException:
Split APK names and source paths are not aligned.
  at AndroidPackageInstallationSnapshotProvider.ReadSources(...)
sourceStatus=not-run appliedStatus=not-run
```

The original code paired `PackageInfo.SplitNames` with `ApplicationInfo.SplitSourceDirs`. Android's API documentation says `SplitSourceDirs` is indexed in the same order as **`ApplicationInfo.SplitNames`**. In some installations `PackageInfo.SplitNames` may be null or incomplete.

## Fix

- Rebuilt `JunimoGate.Android.dll` from the [original pinned JunimoGate source](https://github.com/leontismaro/JunimoGate/commit/029eafed917ae853d6c0a59330ee273524168296) with a **single source change** in `AndroidPackageInstallationSnapshotProvider.ReadSources`.
- The code now uses `ApplicationInfo.SplitNames` with `ApplicationInfo.SplitSourceDirs` first, falling back to `PackageInfo.SplitNames` only if lengths match; never guesses split APK identities.
- When metadata still differs, the error now includes safe numeric array counts rather than private source paths.
- Repackaged the revised .NET Android assembly into its `lib_JunimoGate.Android.dll.so` ARM64 payload wrapper.
- **No other executable, managed, native, game-host, SMAPI, launcher, or resource file was modified** relative to the v0.8.0 QA APK; the CI test enforces exactly-one-file change.
- Android installer and game-signature verification remain unchanged. This does not bypass the original JunimoGate game compatibility rules.

## Build evidence

- [Successful release-config Android C# build + APK QA run](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39190650579).
- 0 C# build warnings/errors.
- ARM64 native managed DLL wrapper revalidated and APK re-signed.
- Existing full SMAPI and GameHost runtime retained.
- APK SHA-256: `a6b36d352efca3fc2f72a5a7bff150624d180c691c01cf52318ef438fbb29dd5`.
- Complete source patch: [android-split-source-fix.patch](https://github.com/marocto1/SMAPI-Aurora/blob/main/junimogate-bridge/android-split-source-fix.patch).
- [Reproducible Android APK QA build workflow](https://github.com/marocto1/SMAPI-Aurora/blob/main/.github/workflows/aurora-android16-split-fix.yml).

## On-phone verification still required

Open v0.8.1 on the phone, tap **Запустить SMAPI Aurora** and inspect current Launcher logs. Success for this fix means that the earlier `Split APK names and source paths are not aligned` exception has disappeared and APK preparation proceeds. Further compatibility failures may still occur.

**BACK UP YOUR DATA BEFORE ANY INSTALL/UNINSTALL:** this experimental build has a different disposable QA signing certificate from v0.8.0 and prior JunimoGate/Aurora APKs, while retaining Android app ID `org.junimogate.app`. Android may reject installing over the earlier app; uninstalling it can delete private app settings/mods/logs. Don't uninstall without exporting or backing up data first. No commercial game code/paid APKs are distributed.
