#!/usr/bin/env python3
"""Apply the Aurora Android UI overlay to a pinned JunimoGate source checkout.

This program intentionally does NOT modify the proprietary-game extraction,
signature checks, runtime/SMAPI host, or any project license/attribution.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

UPSTREAM = "https://github.com/leontismaro/JunimoGate"
UPSTREAM_SHA = "029eafed917ae853d6c0a59330ee273524168296"
APP = Path("src/JunimoGate.App")
PACKAGE = "com.marocto.smapi.aurora.jg"
VERSION = "0.7.0-bridge"

# Android Material3 semantic colors; preserve the resource IDs used by upstream.
PALETTE = {
    "junimo_home_background_scrim": "#DB0B0D19",
    "junimo_home_compact_glass_surface": "#DF22263D",
    "junimo_home_glass_surface": "#EC1A1D31",
    "junimo_navigation_glass_surface": "#F01A1D2E",
    "junimo_launcher_background": "#0B0D19",
    "junimo_primary": "#AD99FF",
    "junimo_on_primary": "#141028",
    "junimo_primary_container": "#38315F",
    "junimo_on_primary_container": "#E9E2FF",
    "junimo_secondary": "#8BEFC6",
    "junimo_on_secondary": "#11291E",
    "junimo_secondary_container": "#1D443E",
    "junimo_on_secondary_container": "#CEFFEB",
    "junimo_tertiary": "#A6B8FF",
    "junimo_on_tertiary": "#1A2252",
    "junimo_tertiary_container": "#323D70",
    "junimo_on_tertiary_container": "#E0E8FF",
    "junimo_surface": "#0B0D19",
    "junimo_surface_dim": "#0B0D19",
    "junimo_surface_bright": "#353B57",
    "junimo_surface_container_lowest": "#080A14",
    "junimo_surface_container_low": "#141727",
    "junimo_surface_container": "#1A1D2E",
    "junimo_surface_container_high": "#252A41",
    "junimo_surface_container_highest": "#30364F",
    "junimo_on_surface": "#F4F6FF",
    "junimo_on_surface_variant": "#A5ACC5",
    "junimo_outline": "#737B9B",
    "junimo_outline_variant": "#414963",
    "junimo_error": "#FFB4AB",
    "junimo_on_error": "#690005",
    "junimo_error_container": "#93000A",
    "junimo_on_error_container": "#FFDAD6",
    "junimo_warning": "#FFC989",
    "junimo_warning_container": "#674520",
    "junimo_on_warning_container": "#FFF0D4",
    "junimo_wood": "#575078",
    "junimo_wood_dark": "#15102D",
    "junimo_wood_light": "#DCD5FF",
    "junimo_hero_rail": "#5D52A2",
    "junimo_hero_border": "#A796FF",
    "junimo_hero_inner_border": "#342C6C",
    "junimo_hero_gradient_start": "#3C3580",
    "junimo_hero_gradient_end": "#1A3658",
    "junimo_hero_surface_start": "#323361",
    "junimo_hero_surface_end": "#1B294A",
    "junimo_hero_surface_stroke": "#736FC1",
    "junimo_hero_icon_surface": "#242544",
    "junimo_hero_title": "#F4F2FF",
    "junimo_hero_body": "#C9C9E7",
    "junimo_hero_track": "#6F8BEFC6",
    "junimo_leaf_dark": "#48508A",
    "junimo_leaf_primary": "#AD99FF",
    "junimo_leaf_light": "#D4C9FF",
    "junimo_leaf_muted": "#9292CD",
}
BRAND_STRINGS = {
    "app_name": "SMAPI Aurora",
    "nav_home": "Home",
    "nav_mods": "Mods",
    "nav_logs": "Logs",
    "nav_settings": "Settings",
    "about_summary": "SMAPI Aurora: an Android game and mod launcher built on the open-source JunimoGate runtime.",
    "about_author_value": "Aurora UI by Marocto · runtime based on JunimoGate by leontismaro",
    "about_up_to_date": "This SMAPI Aurora build is up to date with the latest stable release.",
    "about_no_stable_release": "No stable SMAPI Aurora release has been published yet.",
    "open_source_notice_title": "SMAPI Aurora is free and open source",
    "open_source_notice_message": "Aurora is a GPLv3 adaptation of JunimoGate. The original authors and licenses are credited in About and the included source.",
    "environment_app_version_value": "SMAPI Aurora %1$s",
    "environment_smapi_value": "Version %1$s\\nBundled in SMAPI Aurora; originally maintained by the JunimoGate contributors.",
}
RU_STRINGS = {
    "app_name": "SMAPI Aurora",
    "nav_home": "Главная",
    "nav_mods": "Моды",
    "nav_logs": "Журнал",
    "nav_settings": "Настройки",
    "drawer_open": "Открыть навигацию",
    "drawer_close": "Закрыть навигацию",
    "game_title": "Stardew Valley",
    "launch_game": "Запустить игру",
    "prepare_and_launch": "Подготовить и запустить",
    "retry_and_launch": "Повторить запуск",
    "launching_game": "Подготовка…",
    "launcher_checking_game": "Проверка установленной игры…",
    "launcher_checking_workspace": "Проверка игровой среды…",
    "launcher_needs_preparation": "Перед первым запуском нужно подготовить игровые файлы.",
    "launcher_recovery_available": "Предыдущий запуск завершился ошибкой. Нажми, чтобы попробовать восстановление.",
    "launcher_preparing_game": "Подготовка игровых файлов…",
    "launcher_prepared_game_changed": "Игровые файлы изменились. Повторная проверка…",
    "launcher_game_updated": "Обнаружено обновление Stardew Valley. Проверка совместимости…",
    "launcher_recovering": "Восстановление игровой среды…",
    "launcher_game_not_installed": "Stardew Valley не установлена для текущего пользователя Android.",
    "launcher_unsupported": "Эта установка Stardew Valley пока не поддерживается.\\n\\nКод: %1$s",
    "launcher_failed": "Не удалось запустить Stardew Valley.\\n\\nКод: %1$s",
    "launcher_ready": "Версия %1$s · Готово",
    "launcher_mod_configuration_invalid": "Невозможно запустить выбранную группу модов. Восстанови отсутствующие моды или отключи их.",
    "launcher_launching": "Запуск игры…",
    "home_summary": "Обзор",
    "home_play_time_label": "Время игры",
    "home_enabled_mods_label": "Активных модов",
    "home_last_save_label": "Последнее сохранение",
    "home_open_saves": "Сохранения и копии",
    "last_save_empty": "Нет сохранений",
    "mods_title": "Моды",
    "mods_tab_library": "Библиотека",
    "mods_tab_groups": "Группы",
    "mods_manage_groups": "Управление группами",
    "mods_default_group": "По умолчанию",
    "mods_no_mods_group": "Без модов",
    "about_title": "О программе",
    "about_summary": "SMAPI Aurora: моды и Stardew Valley на Android. Основа загрузчика — открытый проект JunimoGate.",
    "about_author_value": "Aurora — адаптация Marocto; ядро JunimoGate — leontismaro",
    "language_setting": "Язык",
    "language_system": "Как в системе",
    "language_simplified_chinese": "Китайский (упрощённый)",
    "language_english": "Английский",
    "language_russian": "Русский",
    "settings_section_general": "Основные",
    "settings_section_mods": "Моды",
    "about_check_update": "Проверить обновления",
    "about_repository": "GitHub",
    "about_notices": "Лицензии",
    "about_up_to_date": "Установлена последняя стабильная версия Aurora.",
    "about_no_stable_release": "Стабильного выпуска Aurora пока нет.",
    "open_source_notice_title": "SMAPI Aurora — бесплатное ПО с открытым кодом",
    "open_source_notice_message": "Aurora основана на JunimoGate (GPLv3). Оригинальные авторы указаны в разделе «О программе» и исходном коде.",
    "open_source_notice_official_release": "Страница релизов",
    "open_source_notice_acknowledge": "Понятно",
    "environment_app_version_value": "SMAPI Aurora %1$s",
    "environment_smapi_value": "Версия %1$s\\nSMAPI поставляется с Aurora; исходная интеграция создана JunimoGate.",
    "aurora_home_caption": "✦  AURORA  /  ANDROID",
}
A = '{http://schemas.android.com/apk/res/android}'
MARK = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#AD99FF"
        android:pathData="M54,10 L64,43 L98,54 L64,65 L54,98 L44,65 L10,54 L44,43 Z" />
    <path android:fillColor="#8BEFC6"
        android:pathData="M54,35 L59,49 L73,54 L59,59 L54,73 L49,59 L35,54 L49,49 Z" />
</vector>
"""
BACKDROP = """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient android:type="linear" android:angle="135"
        android:startColor="#30285C" android:centerColor="#15192F"
        android:endColor="#0B0D19" />
</shape>
"""
LAUNCHER = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/aurora_launcher_bg"/>
    <foreground android:drawable="@drawable/aurora_mark"/>
</adaptive-icon>
"""

def replace_one(s: str, a: str, b: str, location: str) -> str:
    count = s.count(a)
    if count != 1:
        raise ValueError(f"{location}: expected exactly one anchor, got {count}: {a!r}")
    return s.replace(a, b, 1)

def read(root: Path, relative: Path) -> str:
    target = root / relative
    if target.is_symlink() or not target.is_file():
        raise ValueError(f"Source file is missing or is a symlink: {relative}")
    return target.read_text(encoding="utf-8-sig")

def patch_colors(text: str) -> str:
    root = ET.fromstring(text)
    if root.tag != "resources":
        raise ValueError("Unexpected colors.xml root")
    applied = 0
    for e in root.findall("color"):
        name = e.attrib.get("name")
        if name in PALETTE:
            e.text = PALETTE[name]
            applied += 1
    if applied < 35 or root.find("color[@name='junimo_primary']") is None:
        raise ValueError("Upstream palette layout changed")
    if root.find("color[@name='aurora_launcher_bg']") is None:
        ET.SubElement(root, "color", {"name": "aurora_launcher_bg"}).text = "#0B0D19"
    ET.indent(root, space="    ")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"

def patch_strings(text: str, values: dict[str, str], required: bool = True) -> str:
    root = ET.fromstring(text)
    if root.tag != "resources":
        raise ValueError("Unexpected strings.xml root")
    for name, value in values.items():
        e = root.find(f"string[@name='{name}']")
        if e is None:
            if required:
                raise ValueError(f"Missing expected string: {name}")
            e = ET.SubElement(root, "string", {"name": name})
        e.text = value
    ET.indent(root, space="    ")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"

def make_ru_resources(default_english: str) -> str:
    english = ET.fromstring(default_english)
    names = {e.attrib["name"] for e in english.findall("string")}
    missing = set(RU_STRINGS) - names
    if missing:
        raise ValueError("Russian translation keys absent from default strings: " + repr(sorted(missing)))
    root = ET.Element("resources")
    for key, val in RU_STRINGS.items():
        ET.SubElement(root, "string", {"name": key}).text = val
    ET.indent(root, space="    ")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"

def plan(root: Path) -> dict[Path, str]:
    if not (root / "JunimoGate.sln").exists() and not (root / "JunimoGate.Host.slnf").exists():
        raise ValueError("Not a JunimoGate source checkout")
    changes: dict[Path, str] = {}

    project = APP / "JunimoGate.App.csproj"
    s = read(root, project)
    for old, new in [
        ("<ApplicationId>org.junimogate.app</ApplicationId>", f"<ApplicationId>{PACKAGE}</ApplicationId>"),
        ("<ApplicationTitle>JunimoGate</ApplicationTitle>", "<ApplicationTitle>SMAPI Aurora</ApplicationTitle>"),
        ("<ApplicationVersion>11</ApplicationVersion>", "<ApplicationVersion>700</ApplicationVersion>"),
        ("<ApplicationDisplayVersion>0.3.1</ApplicationDisplayVersion>", f"<ApplicationDisplayVersion>{VERSION}</ApplicationDisplayVersion>"),
    ]:
        s = replace_one(s, old, new, str(project))
    changes[project] = s

    manifest = APP / "Properties/AndroidManifest.xml"
    s = read(root, manifest)
    for a, b in [
        ('android:label="JunimoGate"', 'android:label="@string/app_name"'),
        ('android:icon="@mipmap/ic_launcher"', 'android:icon="@mipmap/aurora_ic_launcher"'),
        ('android:roundIcon="@mipmap/ic_launcher_round"', 'android:roundIcon="@mipmap/aurora_ic_launcher"'),
    ]:
        s = replace_one(s, a, b, str(manifest))
    changes[manifest] = s

    for variant in ("values", "values-night"):
        p = APP / f"Resources/{variant}/colors.xml"
        changes[p] = patch_colors(read(root, p))

    default_strings = APP / "Resources/values/strings.xml"
    s = patch_strings(read(root, default_strings), BRAND_STRINGS)
    s = patch_strings(s, {
        "language_russian": "Русский",
        "aurora_home_caption": "✦  AURORA  /  ANDROID",
    }, required=False)
    changes[default_strings] = s
    changes[APP / "Resources/values-ru/strings.xml"] = make_ru_resources(s)

    cn = APP / "Resources/values-zh-rCN/strings.xml"
    s = patch_strings(read(root, cn), {"app_name": "SMAPI Aurora"})
    changes[cn] = s

    p = APP / "Resources/xml/locales_config.xml"
    s = read(root, p)
    s = replace_one(s, '    <locale android:name="zh-CN" />',
                    '    <locale android:name="zh-CN" />\n    <locale android:name="ru" />', str(p))
    changes[p] = s

    p = APP / "SettingsFragment.cs"
    s = read(root, p)
    s = replace_one(s,
        '"en" => Resource.String.language_english,',
        '"en" => Resource.String.language_english,\n            "ru" => Resource.String.language_russian,', str(p))
    s = replace_one(s,
        '2 => LocaleListCompat.ForLanguageTags("en"),',
        '2 => LocaleListCompat.ForLanguageTags("en"),\n            3 => LocaleListCompat.ForLanguageTags("ru"),', str(p))
    s = replace_one(s,
        'GetString(Resource.String.language_english),',
        'GetString(Resource.String.language_english),\n                GetString(Resource.String.language_russian),', str(p))
    changes[p] = s

    p = APP / "Resources/layout/fragment_home.xml"
    s = read(root, p)
    old = '        <com.google.android.material.card.MaterialCardView\n'
    new = """        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginBottom="12dp"
            android:text="@string/aurora_home_caption"
            android:textAppearance="?attr/textAppearanceLabelLarge"
            android:textColor="@color/junimo_primary" />

""" + old
    s = replace_one(s, old, new, str(p))
    changes[p] = s

    p = APP / "Resources/layout/fragment_main_shell.xml"
    s = read(root, p)
    s = replace_one(s, '@drawable/junimogate_home_background', '@drawable/aurora_backdrop', str(p))
    changes[p] = s

    p = APP / "Resources/layout/fragment_about.xml"
    s = read(root, p)
    s = replace_one(s, '@drawable/junimogate_brand_logo', '@drawable/aurora_mark', str(p))
    s = replace_one(s, 'android:text="JunimoGate"', 'android:text="@string/app_name"', str(p))
    changes[p] = s

    p = APP / "MainActivity.cs"
    s = read(root, p)
    s = replace_one(s,
        'private const string OfficialReleasesUrl = "https://github.com/leontismaro/JunimoGate/releases";',
        'private const string OfficialReleasesUrl = "https://github.com/marocto1/SMAPI-Aurora/releases";', str(p))
    changes[p] = s

    p = APP / "GitHubUpdateService.cs"
    s = read(root, p)
    s = replace_one(s,
        'private const string LatestReleaseApi = "https://api.github.com/repos/leontismaro/JunimoGate/releases/latest";',
        'private const string LatestReleaseApi = "https://api.github.com/repos/marocto1/SMAPI-Aurora/releases/latest";', str(p))
    s = replace_one(s,
        'new ProductInfoHeaderValue("JunimoGate", currentVersion.Replace(\'+\', \'-\'))',
        'new ProductInfoHeaderValue("SMAPI-Aurora", currentVersion.Replace(\'+\', \'-\'))', str(p))
    changes[p] = s

    changes[APP / "Resources/drawable/aurora_mark.xml"] = MARK
    changes[APP / "Resources/drawable/aurora_backdrop.xml"] = BACKDROP
    changes[APP / "Resources/mipmap-anydpi-v26/aurora_ic_launcher.xml"] = LAUNCHER

    # No changes to game binaries, app signing policy or isolated GameHost process.
    for path in changes:
        if not str(path).startswith(str(APP) + "/") or path.suffix not in (".cs", ".xml", ".csproj"):
            raise ValueError("Overlay attempted to modify a forbidden path: " + str(path))
    return changes

def check_commit(root: Path) -> None:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True)
    if result.stdout.strip() != UPSTREAM_SHA:
        raise ValueError("Expected pinned JunimoGate commit " + UPSTREAM_SHA +
                         ", got " + result.stdout.strip())

def execute(root: Path, apply: bool) -> None:
    check_commit(root)
    edits = plan(root)
    if not apply:
        print(f"PASS: Aurora bridge overlay validated against {UPSTREAM_SHA[:12]}; {len(edits)} files")
        return
    # Fail closed on a dirty upstream tree. This prevents clobbering user edits.
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                           check=True, capture_output=True, text=True).stdout
    if dirty.strip():
        raise ValueError("JunimoGate checkout has local changes; refusing to overwrite them")
    for relative, value in edits.items():
        target = root / relative
        if target.is_symlink():
            raise ValueError("Refusing to overwrite symlink: " + str(relative))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")
    print(f"PATCHED: {len(edits)} source files. SMAPI/runtime logic and licenses remain upstream.")

def main() -> None:
    ap = argparse.ArgumentParser(description="Apply SMAPI Aurora theme to pinned JunimoGate.")
    ap.add_argument("checkout", type=Path, help="JunimoGate source root, not the Aurora repository")
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="Validate anchors, do not write")
    modes.add_argument("--apply", action="store_true", help="Apply UI overlay to clean checkout")
    options = ap.parse_args()
    execute(options.checkout.expanduser().resolve(), options.apply)

if __name__ == "__main__":
    main()
