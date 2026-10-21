"""Aurora Network 2.0 Windows diagnostics; existing external VPN only."""
from __future__ import annotations

import ipaddress
import json
import shutil
import subprocess
from typing import Any


def tailscale_state(*, which=shutil.which, runner=subprocess.run) -> dict[str, Any]:
    executable=which("tailscale")
    if not executable:
        return {"installed": False, "running": False,
                "message": "CLI Tailscale не найдена. Это не проверка всех VPN."}
    kwargs={"capture_output":True,"text":True,"timeout":4,"check":False}
    if hasattr(subprocess,"CREATE_NO_WINDOW"):
        kwargs["creationflags"]=subprocess.CREATE_NO_WINDOW
    try:
        result=runner([executable,"status","--json"],**kwargs)
        if result.returncode!=0:
            return {"installed":True,"running":False,
                    "message":"CLI есть, но Tailscale не сообщает активную сеть."}
        if len(result.stdout)>2*1024*1024:
            raise ValueError("Oversized CLI response")
        status=json.loads(result.stdout)
        if not isinstance(status,dict):
            raise ValueError("Unexpected CLI JSON")
        state=str(status.get("BackendState","Unknown"))
        self_node=status.get("Self")
        node=self_node if isinstance(self_node,dict) else {}
        candidates=node.get("TailscaleIPs",[])
        ips=[]
        if isinstance(candidates,list):
            for candidate in candidates[:8]:
                try:
                    ipv4=ipaddress.ip_address(candidate)
                    if ipv4.version==4 and ipv4 in ipaddress.ip_network("100.64.0.0/10") and str(ipv4)!="100.100.100.100":
                        ips.append(str(ipv4))
                except ValueError:
                    continue
        return {"installed":True,"running":state=="Running","state":state,
                "ipv4":ips,
                "message":"Статус клиента VPN, НЕ проверка доступности игры UDP 24642."}
    except (OSError, subprocess.TimeoutExpired, ValueError, json.JSONDecodeError):
        return {"installed":True,"running":False,
                "message":"Tailscale CLI недоступна или вернула некорректный ответ."}
