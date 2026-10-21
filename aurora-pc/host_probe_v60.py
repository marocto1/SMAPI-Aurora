"""Aurora 6.0: read-only, LOCAL Windows UDP 24642 listener observation.

Do not confuse a visible local socket with a reachable Android↔PC farm.
The user must start a Stardew Co-op host before this check can find it.
This module never sends game packets, changes firewall rules, or opens ports.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Any


def inspect_local_game_udp(*, platform: str | None = None,
                           which=shutil.which, runner=subprocess.run) -> dict[str, Any]:
    platform = sys.platform if platform is None else platform
    if platform != "win32":
        return {"status":"unsupported","local_udp_listener_checked":False,
                "gameplay_verified":False,"message":"Локальный UDP-тест доступен только в Windows."}
    executable=which("powershell.exe") or which("powershell")
    if not executable:
        return {"status":"unknown","local_udp_listener_checked":False,
                "gameplay_verified":False,"message":"PowerShell недоступен: проверить UDP 24642 нельзя."}
    cmd=[executable,"-NoProfile","-NonInteractive","-Command",
         "(Get-NetUDPEndpoint -LocalPort 24642 -ErrorAction SilentlyContinue | Measure-Object).Count"]
    kwargs={"capture_output":True,"text":True,"timeout":5,"check":False}
    if hasattr(subprocess,"CREATE_NO_WINDOW"):
        kwargs["creationflags"]=subprocess.CREATE_NO_WINDOW
    try:
        result=runner(cmd,**kwargs)
        if result.returncode != 0 or len(result.stdout)>128:
            raise ValueError("Invalid PowerShell result")
        count=int(result.stdout.strip())
        if count<0 or count>100000:
            raise ValueError("Invalid local endpoint count")
    except (ValueError,OSError,subprocess.TimeoutExpired):
        return {"status":"unknown","local_udp_listener_checked":False,
                "gameplay_verified":False,"message":"Не удалось прочитать локальные UDP-сокеты."}
    if count:
        msg="Локальный UDP 24642 прослушивается ("+str(count)+" сокет(ов)). Доступ с Android НЕ подтверждён."
    else:
        msg="Локального слушателя UDP 24642 не обнаружено. Создай ферму Co-op → Host и проверь снова."
    return {"status":"present" if count else "absent",
            "local_udp_listener_checked":True,"gameplay_verified":False,"message":msg}
