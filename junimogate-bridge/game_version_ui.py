"""Aurora Android source-only Stardew Valley version/install chooser.

This module patches the pinned JunimoGate Android *source*. It does not alter
the v0.7.0 prebuilt SMAPI QA APK's executable code and cannot be applied to
a binary without a full .NET Android GameHost rebuild.
"""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

APP = Path("src/JunimoGate.App")
EN = {
    "aurora_game_versions": "Stardew Valley versions",
    "aurora_version_store": "Get / update from Google Play",
    "aurora_version_choose_apk": "Choose an APK on this phone",
    "aurora_version_compat": "Game version compatibility",
    "aurora_version_dialog_about": "Google Play installs the version available for your device; this launcher cannot select older paid releases. A user-supplied APK can be handed to Android's system installer, with your confirmation. Split APK packages need their complete split set. SMAPI support must be checked separately.",
    "aurora_version_install_question": "Hand this file to Android's system app installer? The APK is not provided or modified by SMAPI Aurora. Verify the source and back up saves before changing versions. This will not guarantee SMAPI support.",
    "aurora_version_install_action": "Open system installer",
    "aurora_version_install_permission": "To install an APK from this launcher, Android must allow SMAPI Aurora to request app installs. Grant permission in system settings, then select your APK again.",
    "aurora_version_open_settings": "Open settings",
    "aurora_version_install_unavailable": "Android cannot open an installer for this file. Check that it is a standalone APK, not an APK split bundle.",
    "aurora_version_source_warning": "A modified, unsigned or differently signed APK may be rejected by the SMAPI GameHost. Aurora does not bypass game signature checks.",
    "aurora_version_store_unavailable": "The official app store cannot be opened on this device.",
}
RU = {
    "aurora_game_versions": "Версии Stardew Valley",
    "aurora_version_store": "Скачать или обновить через Google Play",
    "aurora_version_choose_apk": "Выбрать APK на телефоне",
    "aurora_version_compat": "Совместимость с SMAPI",
    "aurora_version_dialog_about": "Google Play устанавливает доступную для твоего устройства версию игры; выбрать через него старый платный релиз по номеру нельзя. Свой APK можно передать стандартному установщику Android с подтверждением. Для разделённых APK нужен полный комплект. Совместимость со SMAPI проверяется отдельно.",
    "aurora_version_install_question": "Передать выбранный APK системному установщику Android? Aurora не предоставляет и не изменяет этот файл. Проверь его источник и сделай резервную копию сохранений перед сменой версии. Установка не гарантирует работу SMAPI.",
    "aurora_version_install_action": "Открыть установщик Android",
    "aurora_version_install_permission": "Для установки APK из Aurora необходимо разрешение Android на установку из этого источника. Разреши его в настройках системы и снова выбери APK.",
    "aurora_version_open_settings": "Открыть настройки",
    "aurora_version_install_unavailable": "Android не смог открыть установщик. Убедись, что это одиночный APK, а не набор split APK.",
    "aurora_version_source_warning": "Модифицированные APK или APK с неизвестной подписью могут быть отклонены SMAPI GameHost. Aurora не обходит проверку подписи игры.",
}
ACTIVITY_SRC = """
    // Version selection never silently installs software or downloads paid game APKs.
    private const int AuroraGameApkRequestCode = 4902;
    private void OnAuroraGameVersionsClicked(object? sender, EventArgs args)
    {
        var dialog = new Google.Android.Material.Dialog.MaterialAlertDialogBuilder(RequireContext());
        dialog.SetTitle(Resource.String.aurora_game_versions);
        dialog.SetItems(new[]
        {
            GetString(Resource.String.aurora_version_store),
            GetString(Resource.String.aurora_version_choose_apk),
            GetString(Resource.String.aurora_version_compat),
        }, (_, selected) =>
        {
            switch (selected.Which)
            {
                case 0:
                    OpenAuroraOfficialGameStore();
                    break;
                case 1:
                    ChooseAuroraGameApk();
                    break;
                case 2:
                    new Google.Android.Material.Dialog.MaterialAlertDialogBuilder(RequireContext())
                        .SetTitle(Resource.String.aurora_version_compat)
                        .SetMessage(Resource.String.aurora_version_dialog_about)
                        .SetPositiveButton(global::Android.Resource.String.Ok, (_, _) => { })
                        .Show();
                    break;
            }
        });
        dialog.SetNegativeButton(global::Android.Resource.String.Cancel, (_, _) => { });
        dialog.Show();
    }

    private void OpenAuroraOfficialGameStore()
    {
        try
        {
            StartActivity(new Android.Content.Intent(
                Android.Content.Intent.ActionView,
                Android.Net.Uri.Parse("market://details?id=com.chucklefish.stardewvalley")));
        }
        catch (Android.Content.ActivityNotFoundException)
        {
            try
            {
                StartActivity(new Android.Content.Intent(
                    Android.Content.Intent.ActionView,
                    Android.Net.Uri.Parse("https://play.google.com/store/apps/details?id=com.chucklefish.stardewvalley")));
            }
            catch (Android.Content.ActivityNotFoundException)
            {
                Android.Widget.Toast.MakeText(
                    RequireContext(), Resource.String.aurora_version_store_unavailable,
                    Android.Widget.ToastLength.Long)?.Show();
            }
        }
    }

    private void ChooseAuroraGameApk()
    {
        var intent = new Android.Content.Intent(Android.Content.Intent.ActionOpenDocument);
        intent.AddCategory(Android.Content.Intent.CategoryOpenable);
        // Some file providers report a .apk file as application/octet-stream.
        intent.SetType("*/*");
        try
        {
#pragma warning disable CS0618
            StartActivityForResult(intent, AuroraGameApkRequestCode);
#pragma warning restore CS0618
        }
        catch (Android.Content.ActivityNotFoundException)
        {
            Android.Widget.Toast.MakeText(
                RequireContext(), Resource.String.aurora_version_install_unavailable,
                Android.Widget.ToastLength.Long)?.Show();
        }
    }

#pragma warning disable CS0672
    public override void OnActivityResult(
        int requestCode, int resultCode, Android.Content.Intent? data)
    {
#pragma warning disable CS0618
        base.OnActivityResult(requestCode, resultCode, data);
#pragma warning restore CS0618
        if (requestCode != AuroraGameApkRequestCode ||
            resultCode != (int)Android.App.Result.Ok || data?.Data is not { } uri ||
            !IsAdded)
            return;

        var dialog = new Google.Android.Material.Dialog.MaterialAlertDialogBuilder(RequireContext());
        dialog.SetTitle(Resource.String.aurora_version_install_action);
        dialog.SetMessage(Resource.String.aurora_version_install_question);
        dialog.SetNegativeButton(global::Android.Resource.String.Cancel, (_, _) => { });
        dialog.SetPositiveButton(Resource.String.aurora_version_install_action,
            (_, _) => OpenAuroraSystemInstaller(uri));
        dialog.Show();
    }
#pragma warning restore CS0672

    private void OpenAuroraSystemInstaller(Android.Net.Uri uri)
    {
        var context = RequireContext();
        if (OperatingSystem.IsAndroidVersionAtLeast(26) &&
            context.PackageManager?.CanRequestPackageInstalls() == false)
        {
            var dialog = new Google.Android.Material.Dialog.MaterialAlertDialogBuilder(context);
            dialog.SetTitle(Resource.String.aurora_version_open_settings);
            dialog.SetMessage(Resource.String.aurora_version_install_permission);
            dialog.SetNegativeButton(global::Android.Resource.String.Cancel, (_, _) => { });
            dialog.SetPositiveButton(Resource.String.aurora_version_open_settings, (_, _) =>
            {
                var settings = new Android.Content.Intent(
                    Android.Provider.Settings.ActionManageUnknownAppSources,
                    Android.Net.Uri.Parse("package:" + context.PackageName));
                try { StartActivity(settings); }
                catch (Android.Content.ActivityNotFoundException) { }
            });
            dialog.Show();
            return;
        }

        var install = new Android.Content.Intent(Android.Content.Intent.ActionView);
        install.SetDataAndType(uri, "application/vnd.android.package-archive");
        install.AddFlags(Android.Content.ActivityFlags.GrantReadUriPermission);
        try { StartActivity(install); }
        catch (Android.Content.ActivityNotFoundException)
        {
            Android.Widget.Toast.MakeText(
                context, Resource.String.aurora_version_install_unavailable,
                Android.Widget.ToastLength.Long)?.Show();
        }
        catch (Java.Lang.SecurityException)
        {
            Android.Widget.Toast.MakeText(
                context, Resource.String.aurora_version_install_permission,
                Android.Widget.ToastLength.Long)?.Show();
        }
    }
"""


def add_version_install_ui(root: Path, changes: dict, read, replace_one):
    """Extend pending overlay: main screen action, strings, safe APK handoff."""
    p = APP / "Resources/layout/fragment_home.xml"
    s = changes[p]
    needle = '''        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginTop="24dp"
            android:text="@string/home_summary"'''
    panel = '''        <com.google.android.material.button.MaterialButton
            android:id="@+id/aurora_game_versions"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            android:text="@string/aurora_game_versions"
            app:icon="@drawable/ic_gamepad_24" />

'''
    s = replace_one(s, needle, panel + needle, str(p))
    changes[p] = s

    p = APP / "HomeFragment.cs"
    s = read(root, p)
    s = replace_one(
        s,
        "    private TextView? modCountText;",
        "    private TextView? modCountText;\n    private View? auroraVersionButton;",
        str(p))
    s = replace_one(
        s,
        "        modCountText = view.FindViewById<TextView>(Resource.Id.home_mod_count);",
        """        modCountText = view.FindViewById<TextView>(Resource.Id.home_mod_count);
        auroraVersionButton = view.FindViewById(Resource.Id.aurora_game_versions);
        if (auroraVersionButton is not null)
            auroraVersionButton.Click += OnAuroraGameVersionsClicked;""",
        str(p))
    s = replace_one(
        s,
        "        if (lastSaveCard is not null)\n            lastSaveCard.Click -= OnLastSaveClicked;",
        """        if (lastSaveCard is not null)
            lastSaveCard.Click -= OnLastSaveClicked;
        if (auroraVersionButton is not null)
            auroraVersionButton.Click -= OnAuroraGameVersionsClicked;""",
        str(p))
    s = replace_one(
        s,
        "        modCountText = null;\n        base.OnDestroyView();",
        "        modCountText = null;\n        auroraVersionButton = null;\n        base.OnDestroyView();",
        str(p))
    mark = "    private void TrySetInstalledGameIcon()"
    s = replace_one(s, mark, ACTIVITY_SRC + "\n" + mark, str(p))
    changes[p] = s

    # The build requests installs only with user confirmation through Android.
    p = APP / "Properties/AndroidManifest.xml"
    s = changes[p]
    needle = '  <uses-permission android:name="android.permission.INTERNET" />'
    s = replace_one(s, needle, needle +
                    '\n  <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />',
                    str(p))
    changes[p] = s

    # Add the strings to already-localized resources, preserving all existing IDs.
    for qualifier, translations in (("values", EN), ("values-ru", RU)):
        p = APP / f"Resources/{qualifier}/strings.xml"
        xml = ET.fromstring(changes[p])
        if xml.tag != "resources":
            raise ValueError(f"Unexpected {p}")
        for key, value in translations.items():
            if xml.find(f"string[@name='{key}']") is not None:
                raise ValueError(f"Duplicate resource {key}")
            ET.SubElement(xml, "string", {"name": key}).text = value
        ET.indent(xml, space="    ")
        changes[p] = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(xml, encoding="unicode") + "\n"
