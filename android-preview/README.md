# SMAPI Aurora Preview — installable Android APK

A native Android companion **preview**, built from our own source in this repository. It deliberately does **not** claim to inject SMAPI into Stardew Valley or bypass ownership protections. The full patched SMAPI launcher still needs private compilation references.

Features available in the preview: dark animated native UI, installed Android game chooser (including sideloaded apps visible to Android), read-only base/split APK structure/version diagnostics, launch the selected installed game **without SMAPI**, Android Storage Access Framework mod-workspace selection and mod manifest browsing.

See `../BUILD_STATUS.md` for full SMAPI build requirements. The preview has a different Android package ID so it will not overwrite the original loader.

Run **Build Aurora Android preview APK** under GitHub Actions to retrieve the debug APK artifact. Do not interpret this companion preview as the final SMAPI runtime.
