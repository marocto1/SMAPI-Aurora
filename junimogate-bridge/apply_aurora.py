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
    "home_game_icon_description": "Значок установленной Stardew Valley",
    "mods_library_description": "Импортированные моды хранятся в общей библиотеке. Их можно добавлять в активную группу.",
    "mods_group_unavailable": "Текущая группа модов недоступна.",
    "mods_group_summary": "%1$s · включено %2$d · отсутствует %3$d",
    "mods_empty": "В библиотеке пока нет модов.",
    "mods_batch": "Массовые действия",
    "mods_select_all": "Выбрать видимые",
    "mods_clear_visible_selection": "Снять выделение",
    "mods_selected_count": "Выбрано: %1$d",
    "mods_delete_selected": "Удалить выбранные",
    "mods_delete_selected_title": "Удалить выбранные моды?",
    "mods_delete_selected_message": "Удалить %1$d модов из библиотеки? В группах останутся записи об отсутствующих модах.",
    "mods_delete_selected_completed": "Удалено модов: %1$d",
    "mods_add_to_group": "Добавить в группу",
    "mods_group_action_short": "Группа",
    "mods_choose_group": "Выбери группу модов",
    "mods_no_editable_groups": "Сначала создай группу модов.",
    "mods_replace_versions_title": "Заменить версии в этой группе?",
    "mods_replace_versions_message": "У %1$d выбранных модов уже есть другие версии в группе %2$s. Заменить их?",
    "mods_replace_versions_action": "Заменить",
    "mods_added_to_group": "Добавлено %1$d · заменено %2$d · изменено %3$d",
    "mod_picker_title": "Добавить моды в эту группу",
    "mod_picker_empty": "Поиск не нашёл установленных модов.",
    "mod_picker_add": "Добавить выбранные моды",
    "mod_picker_add_count": "Добавить выбранные (%1$d)",
    "mod_picker_already_added": "уже добавлен",
    "mods_import_action": "Импорт ZIP-мода",
    "mods_import_button": "Импорт",
    "mods_search_hint": "Поиск по имени, автору, ID или версии",
    "mods_search_empty": "Нет модов, подходящих под запрос.",
    "mods_inventory_count": "Элементов: %1$d · модов: %2$d",
    "mods_inventory_filtered_count": "Показано %1$d / %2$d · модов: %3$d",
    "mods_import_confirm_title": "Импортировать эти моды?",
    "mods_import_progress": "Обработка %1$d / %2$d: %3$s",
    "mods_import_skip": "Пропустить",
    "mods_import_more": "…и ещё %1$d",
    "mods_import_has_warnings": "В архиве есть предупреждения о совместимости. Импорт всё ещё возможен.",
    "mods_archive_rejected": "Не удалось импортировать архив",
    "mods_archive_rejected_description": "ZIP не прошёл проверку безопасности. Моды не установлены.",
    "mods_import_failed": "Импорт ZIP не удался. Подробности смотри в журнале.",
    "mods_library_read_failed": "Не удалось прочитать библиотеку модов.",
    "mods_no_description": "Описание отсутствует.",
    "mods_details_action": "Подробнее",
    "mods_more_actions": "Дополнительные действия",
    "mods_more_actions_short": "Ещё",
    "mod_files_action": "Файлы",
    "mod_files_title": "Файлы мода",
    "mod_files_choose_mod": "Выбери мод",
    "mod_files_folder": "Папка",
    "mod_files_empty": "Папка пуста.",
    "mod_files_read_failed": "Не удалось прочитать файлы мода.",
    "mods_type_code": "кодовый мод",
    "mods_type_content": "контент-пак",
    "mods_type_mixed": "код и контент",
    "mods_delete_title": "Удалить установленный мод?",
    "mods_delete_message": "Удалить %1$s %2$s из библиотеки? Игровые папки не изменятся.",
    "mods_delete_action": "Удалить",
    "mods_delete_completed": "Мод удалён из библиотеки.",
    "mods_delete_in_use": "Нельзя удалять моды во время запуска игры или игровой сессии.",
    "mods_delete_failed": "Не удалось удалить мод.",
    "logs_title": "Журнал",
    "logs_empty": "Здесь появятся записи текущего и предыдущего запуска.",
    "logs_source": "Источник",
    "logs_generation": "Сессия",
    "logs_source_launcher": "Лаунчер",
    "logs_source_game": "Игровое ядро",
    "logs_source_smapi": "SMAPI и моды",
    "logs_crash": "Сбой",
    "logs_current": "Текущая",
    "logs_previous": "Предыдущая",
    "logs_copy": "Копировать",
    "logs_copy_full": "Копировать журнал целиком",
    "logs_copied": "Журнал скопирован.",
    "logs_copy_failed": "Не удалось скопировать журнал.",
    "logs_share": "Поделиться",
    "logs_share_full": "Поделиться полным журналом",
    "logs_share_current": "Поделиться текущим",
    "logs_share_failed": "Не удалось поделиться файлом журнала.",
    "logs_refresh": "Обновить",
    "logs_filter_important": "Важное",
    "logs_filter_all": "Все",
    "logs_filter_errors": "Ошибки",
    "logs_filter_warnings": "Предупреждения",
    "logs_search_hint": "Поиск источника или сообщения",
    "logs_search_close": "Закрыть поиск",
    "logs_more_actions": "Другие действия с журналом",
    "logs_mode_structured": "По категориям",
    "logs_mode_raw": "Исходный текст",
    "logs_no_matches": "Записей по текущему фильтру нет.",
    "logs_upload": "Загрузить на smapi.io",
    "logs_upload_confirm_title": "Загрузить полный журнал SMAPI?",
    "logs_upload_confirm": "Полный файл %1$s (%2$s) будет отправлен стороннему сервису smapi.io. Журнал может содержать имена модов, сведения об устройстве и пути файлов.",
    "logs_upload_action": "Загрузить",
    "logs_uploading_title": "Загрузка журнала SMAPI",
    "logs_uploading": "Отправка полного журнала на smapi.io…",
    "logs_upload_too_large": "Журнал слишком большой для загрузки. Можно поделиться файлом целиком.",
    "logs_upload_failed": "Сервис smapi.io не принял журнал. Можно поделиться исходным файлом.",
    "logs_upload_success_title": "Журнал SMAPI загружен",
    "logs_open_link": "Открыть",
    "logs_copy_link": "Копировать ссылку",
    "logs_share_link": "Поделиться ссылкой",
    "logs_link_copied": "Ссылка на журнал скопирована.",
    "logs_export": "Экспорт",
    "logs_export_diagnostics": "Экспортировать всё",
    "logs_file_unavailable": "Для выбранного источника и сессии журнал отсутствует.",
    "logs_summary": "Показано %1$s · ошибок %2$d · предупреждений %3$d",
    "logs_summary_truncated": "Показаны последние %1$s · ошибок %2$d · предупреждений %3$d",
    "logs_read_failed": "Не удалось прочитать журнал.",
    "save_backups_title": "Сохранения и копии",
    "save_backups_settings_summary": "Управление сохранениями, импорт архивов и восстановление резервных копий.",
    "save_backups_loading": "Чтение сохранений…",
    "save_backups_export": "Экспорт",
    "save_backups_export_complete": "Резервная копия экспортирована.",
    "save_backups_export_failed": "Не удалось экспортировать сохранение.",
    "save_backups_read_failed": "Не удалось прочитать сведения о сохранениях и копиях.",
    "saves_tab_live": "Сохранения",
    "saves_tab_backups": "Автокопии",
    "saves_loading": "Загрузка…",
    "saves_live_count": "Сохранений: %1$d",
    "saves_backup_count": "Автокопий: %1$d",
    "saves_live_empty": "Сохранения не найдены.",
    "saves_backup_empty": "Резервные копии отсутствуют.",
    "saves_import": "Импорт",
    "saves_restore": "Восстановить",
    "saves_close_game_first": "Закрой игру перед импортом или восстановлением сохранений.",
    "saves_unnamed": "Безымянное сохранение",
    "saves_unknown_farmer": "Неизвестный фермер",
    "saves_incomplete": "Сохранение неполное.",
    "saves_metadata_unreadable": "Некоторые сведения о сохранении не удалось прочитать.",
    "saves_export_complete": "Сохранение экспортировано.",
    "saves_restore_failed": "Не удалось подготовить резервную копию.",
    "saves_import_title": "Импорт сохранений",
    "saves_import_summary": "Найдено %1$d · уже существует %2$d",
    "saves_import_empty": "В ZIP не найдено подходящих сохранений.",
    "saves_import_safety_note": "Существующие сохранения пропускаются по умолчанию. Перед заменой создаётся резервная копия.",
    "saves_import_new": "Новое сохранение",
    "saves_import_conflict": "Уже существует · пропускается",
    "saves_import_add": "Добавить",
    "saves_import_replace": "Заменить",
    "saves_import_action": "Импортировать",
    "saves_import_selected": "Импортировать: %1$d",
    "saves_import_invalid": "В ZIP нет подходящего архива сохранений.",
    "saves_import_failed": "Не удалось импортировать выбранные сохранения.",
    "saves_import_complete": "Импортировано сохранений: %1$d",
    "saves_import_complete_with_backup": "Импортировано %1$d сохранений. Перед заменой созданы резервные копии.",
    "settings_section_maintenance": "Обслуживание",
    "binding_policy": "Конфликты зависимостей",
    "binding_policy_summary": "Как выбирать версии одной зависимости при загрузке модов.",
    "binding_highest_compatible": "Выбирать самую новую совместимую версию",
    "binding_strict": "Строгая проверка",
    "binding_first_loaded": "Использовать первую загруженную версию",
    "settings_add_imported_mods": "Добавлять импорт в активную группу",
    "settings_confirm_mod_deletion": "Подтверждать удаление модов",
    "settings_repair_action": "Восстановить игровую среду",
    "settings_repair_summary": "Используй после обновления игры или при проблемах с запуском.",
    "settings_repair_confirm_title": "Восстановить игровую среду?",
    "settings_repair_confirm_message": "Проверка игры может занять время. Моды, сохранения, резервные копии и журналы не изменятся.",
    "mod_groups_title": "Группы модов",
    "mod_groups_description": "Выбирай группу перед запуском. Она ссылается на нужные версии модов без повторного копирования.",
    "mod_groups_create_action": "Создать группу",
    "mod_groups_import_action": "Импортировать группу",
    "mod_groups_create_title": "Создать группу модов",
    "mod_groups_name_hint": "Название группы",
    "mod_groups_empty": "Группы модов отсутствуют.",
    "mod_groups_active": "текущая",
    "mod_groups_inactive": "не выбрана",
    "mod_groups_item_summary": "Включено %1$d · отключено %2$d · отсутствует %3$d",
    "mod_groups_open": "Изменить",
    "mod_groups_select": "Выбрать",
    "mod_groups_selected": "Выбрана",
    "mod_groups_make_active": "Использовать эту группу",
    "mod_groups_share": "Поделиться",
    "mod_groups_share_title": "Поделиться группой «%1$s»",
    "mod_groups_export_manifest": "Только манифест",
    "mod_groups_export_package": "Полный архив",
    "mod_groups_include_config": "Включить настройки модов",
    "mod_groups_include_config_summary": "Только при экспорте полного архива.",
    "mod_groups_exporting_manifest": "Экспорт манифеста группы…",
    "mod_groups_exporting_package": "Упаковка файлов модов…",
    "mod_groups_package_confirm_title": "Импортировать группу модов?",
    "mod_groups_package_confirm_message": "%1$s\\n\\nУчастников %2$d · модов в архиве %3$d",
    "mod_groups_import_result": "Импортирована группа «%1$s»: новых %2$d, повторно использовано %3$d, отсутствует %4$d, другие варианты %5$d.",
    "mod_groups_export_result": "Экспортировано модов: %1$d; исключено настроек: %2$d; отсутствовало: %3$d.",
    "mod_groups_export_result_with_config": "Экспортировано модов: %1$d; файлов настроек: %2$d; отсутствовало: %3$d.",
    "mod_groups_import_failed": "Не удалось импортировать группу модов.",
    "mod_groups_export_failed": "Не удалось экспортировать группу модов.",
    "mod_groups_delete_title": "Удалить группу модов?",
    "mod_groups_delete_message": "Удалить группу «%1$s»? Файлы установленных модов останутся.",
    "mod_groups_create_failed": "Не удалось создать группу. Укажи корректное название.",
    "mod_groups_select_failed": "Не удалось сменить текущую группу модов.",
    "mod_groups_delete_failed": "Не удалось удалить группу модов.",
    "mod_groups_read_failed": "Не удалось прочитать список групп модов.",
    "mod_group_editor_title": "Редактирование группы модов",
    "mod_group_info": "Настройки группы",
    "mod_group_description_hint": "Описание (необязательно)",
    "mod_group_policy_global": "Общая политика зависимостей",
    "mod_group_member_search_hint": "Поиск модов в группе",
    "mod_group_add_from_library": "Добавить из библиотеки",
    "mod_group_batch": "Массовые действия",
    "mod_group_select_all": "Выбрать видимые",
    "mod_group_clear_visible_selection": "Снять выделение",
    "mod_group_selected_count": "Выбрано: %1$d",
    "mod_group_enable_selected": "Включить",
    "mod_group_disable_selected": "Отключить",
    "mod_group_remove_selected": "Убрать",
    "mod_group_remove_member": "Убрать из группы",
    "mod_group_remove_title": "Убрать моды из группы?",
    "mod_group_remove_message": "Убрать %1$d модов из этой группы? Установленные файлы останутся.",
    "mod_group_members_empty": "В этой группе нет модов.",
    "mod_group_members_search_empty": "Поиск не нашёл модов в группе.",
    "mod_group_member_missing": "отсутствует в библиотеке",
    "mod_group_enabled": "Включён",
    "mod_group_bundle_summary": "Модов: %1$d · %2$s",
    "mod_group_state_enabled": "все включены",
    "mod_group_state_disabled": "все отключены",
    "mod_group_state_partial": "включены частично",
    "mod_group_components": "Содержит: %1$s",
    "mod_group_dependencies": "Зависимости",
    "mod_group_dependency_required": "обязательная",
    "mod_group_dependency_optional": "необязательная",
    "mod_group_dependency_not_installed": "не установлена",
    "mod_group_dependency_available": "доступна в библиотеке",
    "mod_group_dependency_disabled": "отключена в группе",
    "mod_group_dependency_satisfied": "выполнена",
    "mod_group_dependency_version_mismatch": "выбранная версия ниже %1$s",
    "mod_group_dependency_add": "Добавить в эту группу",
    "mod_group_dependency_enable": "Включить в этой группе",
    "mod_group_dependency_choose_version": "Выбрать установленную версию",
    "mod_group_dependency_updated": "Зависимость обновлена.",
    "mod_group_dependency_update_failed": "Не удалось обновить зависимость.",
    "mod_group_update_failed": "Не удалось сохранить изменения группы.",
    "mod_group_read_failed": "Не удалось прочитать группу модов.",
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
    # Android String.format is sensitive to placeholder indexes and argument types.
    # Reject translations that could crash the game/launcher with missing format args.
    placeholder = re.compile(r"(?<!%)%(?:[1-9][0-9]*\$)?[sdf]")
    root = ET.Element("resources")
    for key, val in RU_STRINGS.items():
        source = english.find(f"string[@name='{key}']")
        if source is None:
            raise ValueError("Translation source vanished: " + key)
        expected = sorted(placeholder.findall(source.text or ""))
        received = sorted(placeholder.findall(val))
        if expected != received:
            raise ValueError(f"Russian string {key} changes Android format args: {expected!r} -> {received!r}")
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

    # Aurora uses a dark UI even when Android is in light mode; system bar
    # glyphs must remain light for contrast against the dark status/nav bars.
    style = APP / "Resources/values/styles.xml"
    s = read(root, style)
    s = replace_one(s,
        '<item name="android:windowLightStatusBar">true</item>',
        '<item name="android:windowLightStatusBar">false</item>', str(style))
    s = replace_one(s,
        '<item name="android:windowLightNavigationBar">true</item>',
        '<item name="android:windowLightNavigationBar">false</item>', str(style))
    changes[style] = s

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
    old = '        <com.google.android.material.card.MaterialCardView\n            android:layout_width="match_parent"\n            android:layout_height="wrap_content"\n            app:cardBackgroundColor="@android:color/transparent"'
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

    # Interactive version catalog, store route and user-supplied APK handoff.
    # The prebuilt upstream binary cannot receive these C# changes; it requires
    # a full GameHost source build before this UI can ship.
    from game_version_ui import add_version_install_ui
    add_version_install_ui(root, changes, read, replace_one)

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
