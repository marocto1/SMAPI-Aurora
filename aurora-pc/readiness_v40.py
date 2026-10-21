"""Aurora Unified v4.0 — read-only startup/readiness report for a *real* host.

No probes against Stardew UDP 24642 and no VPN auto-configuration.
All values are derived locally; user-declared versions are clearly labelled.
"""
from __future__ import annotations
from pathlib import Path
import json
import ipaddress

import aurora_core as core
import coop_v20 as room
import workshop_v25 as workshop


def prepare_readiness(game: Path, profile: str, *, declared_game: str = "",
                      declared_smapi: str = "", room_ip: str = "",
                      room_open: bool = False) -> dict:
    directory = game.expanduser().resolve()
    game_present = (directory / "Stardew Valley.exe").is_file()
    smapi_present = (directory / "StardewModdingAPI.exe").is_file()
    mods = core.get_mods(directory,profile)
    missing = workshop.check_dependencies(directory,profile)
    usable_room_ip = bool(room_ip and room.local_address(room_ip) and
                          room_ip != "100.100.100.100")
    checks = [
        {"key":"game", "status":"ok" if game_present else "missing",
         "message":"Игровой EXE найден" if game_present else "Не найден Stardew Valley.exe"},
        {"key":"smapi", "status":"ok" if smapi_present else "missing",
         "message":"SMAPI EXE найден" if smapi_present else "Не найден StardewModdingAPI.exe"},
        {"key":"profile", "status":"ok",
         "message":f"Профиль {profile}: модов по manifest.json — {len(mods)}"},
        {"key":"dependencies","status":"warning" if missing else "ok",
         "message":f"Возможных проблем обязательных зависимостей: {len(missing)}"},
        {"key":"versions","status":"unverified",
         "message":f"Игра {declared_game or 'не указана'}; SMAPI {declared_smapi or 'не указана'} (заявлено пользователем)"},
        {"key":"room","status":"ok" if room_open and usable_room_ip else "not-tested",
         "message":"Комната Aurora открыта" if room_open and usable_room_ip else "Комната Aurora не открыта/адрес не подтверждён"}
    ]
    return {
        "schema":"aurora-unified-readiness/v1",
        "launcher":"Aurora SMAPI PC",
        "platform":"windows",
        "checks":checks,
        "active_profile":profile,
        "mods_by_manifest":len(mods),
        "issues_by_manifest":len(missing),
        "versions_user_declared":True,
        "aurora_network_preflight_only":True,
        "game_udp_24642_checked":False,
        "android_crossplay_checked":False,
        "save_restore_checked":False,
    }


def format_report(result: dict) -> str:
    if result.get("schema") != "aurora-unified-readiness/v1":
        raise ValueError("Unsupported Aurora readiness report")
    icons={"ok":"✓","warning":"!","missing":"×","unverified":"?","not-tested":"–"}
    lines=["AURORA 4.0 · ГОТОВНОСТЬ ПК", "Результат: диагностика лаунчера, не игровой сессии", ""]
    for check in result["checks"]:
        lines.append(f"{icons.get(check['status'],'?')} {check['message']}")
    lines += [
        "",
        "Игровой UDP 24642: НЕ проверялся",
        "Android ↔ PC Stardew Co-op: НЕ проверялся",
        "Резервное восстановление Android: НЕ проверялось",
        "Для интернета обе стороны должны быть в уже подключённой VPN.",
        "Для входа в ферму запускай Co-op внутри Stardew Valley."
    ]
    return "\n".join(lines)
