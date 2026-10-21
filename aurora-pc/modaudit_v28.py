"""v2.8 non-destructive local profile comparison and dependency audit."""
from __future__ import annotations
import aurora_core as core
import workshop_v25 as workshop
from pathlib import Path


def compare_profiles(game: Path, first: str, second: str,
                     root: Path | None = None) -> dict[str, object]:
    if first == second:
        raise ValueError("Choose two different profiles")
    # Read manifests only. This is not a runtime/Android DLL compatibility test.
    a = core.get_mods(game, first, root)
    b = core.get_mods(game, second, root)
    def indexed(rows):
        out = {}
        for row in rows:
            key=row["id"].casefold().strip()
            if not key or key in out:
                raise ValueError("Duplicate or missing SMAPI UniqueID in profile")
            out[key]=(row["name"],row["version"])
        return out
    ia, ib = indexed(a), indexed(b)
    only_a = sorted(set(ia)-set(ib))
    only_b = sorted(set(ib)-set(ia))
    different = sorted(x for x in set(ia)&set(ib) if ia[x][1] != ib[x][1])
    return {
        "left":first, "right":second,
        "only_left":only_a, "only_right":only_b,
        "versions":{k:{"left":ia[k][1],"right":ib[k][1]} for k in different},
        "left_dependencies":workshop.check_dependencies(game,first,root),
        "right_dependencies":workshop.check_dependencies(game,second,root),
        "verified_runtime":False,
        "note":"manifest-only; does not execute mods or verify Android compatibility",
    }


def summarize(report: dict[str, object]) -> str:
    lines=[
        f"Профили: {report['left']} ↔ {report['right']}",
        f"Только {report['left']}: {len(report['only_left'])}",
        f"Только {report['right']}: {len(report['only_right'])}",
        f"Разные версии: {len(report['versions'])}",
        f"Проблемы обязательных зависимостей слева: {len(report['left_dependencies'])}",
        f"Проблемы обязательных зависимостей справа: {len(report['right_dependencies'])}"
    ]
    for mod in report["only_left"][:16]:
        lines.append(f"  + {mod} только {report['left']}")
    for mod in report["only_right"][:16]:
        lines.append(f"  + {mod} только {report['right']}")
    for mod, values in list(report["versions"].items())[:20]:
        lines.append(f"  ! {mod}: {values['left']} / {values['right']}")
    lines.append("Только metadata. Не доказывает работу в SMAPI / Android.")
    return "\n".join(lines)
