"""Aurora SMAPI PC v2.0: invite-only local/VPN rooms, mods and game launch."""
from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import aurora_core as core
import coop_v20 as coop
import workshop_v21 as workshop
import webbrowser

BG = "#121626"
SURFACE = "#202941"
SURFACE2 = "#2b3555"
WHITE = "#f1f2ff"
MUTED = "#b8c5e1"
TEAL = "#70d4dd"
ACCENT = "#a0b4ff"


class AuroraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aurora SMAPI PC · v2.1.0-preview.1")
        self.geometry("1020x860")
        self.minsize(780, 680)
        self.configure(bg=BG)
        self.settings = core.load_settings()
        if not self.settings["game_directory"]:
            detected = core.detect_game()
            if detected:
                self.settings["game_directory"] = str(detected)
        self.game = tk.StringVar(value=self.settings["game_directory"])
        self.profile = tk.StringVar(value=self.settings["profile"])
        self.game_version = tk.StringVar(value=self.settings.get("game_version",""))
        self.smapi_version = tk.StringVar(value=self.settings.get("smapi_version",""))
        self.server = None
        self.room_address = tk.StringVar(value="")
        self.invite = tk.StringVar(value="Комната пока не открыта.")
        self.status = tk.StringVar(value="Выбери папку Stardew Valley для запуска.")
        self._layout()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def label(self, parent, text, *, size=11, color=WHITE, bold=False):
        result = tk.Label(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"),
                          fg=color, bg=parent.cget("bg"), anchor="w")
        result.pack(fill="x", pady=(3, 4))
        return result

    def button(self, parent, name, handler, *, primary=False):
        b = tk.Button(parent, text=name, command=handler, bg=TEAL if primary else SURFACE2,
                      fg="#0b2630" if primary else WHITE, activebackground=ACCENT,
                      activeforeground=BG, relief="flat", bd=0, padx=14, pady=10,
                      font=("Segoe UI", 10, "bold"), cursor="hand2")
        b.pack(side="left", padx=(0, 8), pady=4)
        return b

    def panel(self, parent):
        p = tk.Frame(parent, bg=SURFACE, padx=15, pady=13)
        p.pack(fill="x", pady=9)
        return p

    def row(self, parent):
        p = tk.Frame(parent, bg=parent.cget("bg"))
        p.pack(fill="x", pady=5)
        return p

    def _layout(self):
        header = tk.Frame(self, bg=BG, padx=28, pady=22)
        header.pack(fill="x")
        self.label(header, "AURORA  /  SMAPI PC", size=24, color=ACCENT, bold=True)
        self.label(header,
                   "Твоя Stardew Valley на Windows · Моды · Профили · Aurora Coop (LAN)",
                   size=11, color=MUTED)
        outer = tk.Frame(self, bg=BG, padx=26)
        outer.pack(fill="both", expand=True)
        game = self.panel(outer)
        self.label(game, "1. ПАПКА ИГРЫ", size=11, bold=True)
        entryrow = self.row(game)
        entry = tk.Entry(entryrow, textvariable=self.game, bg=SURFACE2, fg=WHITE,
                         insertbackground=WHITE, relief="flat", font=("Segoe UI", 11))
        entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 12))
        self.button(entryrow, "Выбрать…", self.pick_game)
        actions = self.row(game)
        self.button(actions, "Играть с модами / SMAPI", lambda: self.launch(True), primary=True)
        self.button(actions, "Обычная Stardew Valley", lambda: self.launch(False))

        modsp = self.panel(outer)
        self.label(modsp, "2. МОДЫ И ПРОФИЛИ", size=11, bold=True)
        row = self.row(modsp)
        self.label(row, "Активный профиль", color=MUTED)
        self.profile_select = ttk.Combobox(row, textvariable=self.profile,
                                            state="readonly", width=28)
        self.profile_select.pack(side="left", padx=8)
        self.profile_select.bind("<<ComboboxSelected>>", lambda event: self.change_profile())
        self.button(row, "Новый профиль", self.create_profile)
        self.button(row, "Импорт ZIP", self.import_mod)
        self.button(row, "Открыть папку", self.open_mods)
        self.button(row,"Workshop 3.0",self.open_workshop)
        self.mod_summary = tk.StringVar()
        tk.Label(modsp, textvariable=self.mod_summary, bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 10), anchor="w").pack(fill="x", pady=5)

        coop = self.panel(outer)
        self.label(coop, "3. AURORA COOP · ЛОКАЛЬНАЯ СЕТЬ", size=11, bold=True)
        self.label(coop,
                   "PC создаёт ферму в Stardew; Android подключается к IP внутри игры.",
                   color=MUTED, size=10)
        self.ipline = tk.StringVar()
        self.label(coop, "IP ПК: определяем…", size=15, color=TEAL, bold=True)
        self.ip_label = coop.winfo_children()[-1]
        self.label(coop, "Версии укажи вручную (это заявления пользователя, не обнаружение игры):",
                   color=MUTED, size=10)
        metadata = self.row(coop)
        self.label(metadata, "Игра", color=MUTED, size=10)
        tk.Entry(metadata, textvariable=self.game_version, width=15, bg=SURFACE2,
                 fg=WHITE, insertbackground=WHITE).pack(side="left", padx=6, ipady=7)
        self.label(metadata, "SMAPI", color=MUTED, size=10)
        tk.Entry(metadata, textvariable=self.smapi_version, width=15, bg=SURFACE2,
                 fg=WHITE, insertbackground=WHITE).pack(side="left", padx=6, ipady=7)
        self.label(coop, "IP для приглашения: Wi-Fi или адрес существующей VPN (100.64–127.x.x).",
                   color=MUTED, size=10)
        iprow=self.row(coop)
        tk.Entry(iprow, textvariable=self.room_address, width=28, bg=SURFACE2,
                 fg=WHITE, insertbackground=WHITE).pack(side="left", padx=(0, 9), ipady=7)
        self.button(iprow,"Подставить локальный IP",self.choose_lan_ip)
        self.label(coop,"Приглашение доступно только после открытия комнаты.",
                   color=MUTED,size=9)
        code_row=self.row(coop)
        tk.Entry(code_row,textvariable=self.invite,bg=SURFACE2,fg=ACCENT,
                 readonlybackground=SURFACE2, state="readonly",
                 font=("Consolas",10)).pack(side="left",fill="x",expand=True,ipady=8)
        self.button(code_row,"Копировать",self.copy_invite)
        cooprow = self.row(coop)
        self.button(cooprow, "Открыть комнату Aurora", self.start_server, primary=True)
        self.button(cooprow, "Закрыть комнату", self.stop_server)
        self.label(coop,
                   "Автопоиск: UDP 24644; статус и сравнение модов: TCP 24643. " 
                   "Игра: UDP 24642. Нет VPN и автовхода. Открывай только в частной сети.",
                   color=MUTED, size=9)
        tk.Label(self, textvariable=self.status, bg=BG, fg=ACCENT,
                 anchor="w", font=("Segoe UI", 10), padx=27, pady=11).pack(fill="x")

    def _save(self):
        core.save_settings({"game_directory": self.game.get(),
                            "profile": self.profile.get(),
                            "game_version": self.game_version.get(),
                            "smapi_version": self.smapi_version.get()})

    def game_path(self):
        path = Path(self.game.get().strip())
        if not path.is_dir():
            raise ValueError("Укажи существующую папку установленной Stardew Valley.")
        return path

    def pick_game(self):
        initial = self.game.get() if Path(self.game.get()).is_dir() else None
        folder = filedialog.askdirectory(title="Выбери папку Stardew Valley", initialdir=initial)
        if folder:
            self.game.set(folder)
            self._save()
            self.refresh()

    def refresh(self):
        profiles = core.available_profiles()
        self.profile_select["values"] = profiles
        if self.profile.get() not in profiles:
            self.profile.set("Default")
        try:
            path = self.game_path()
            mods = core.get_mods(path, self.profile.get())
            present = (path / "StardewModdingAPI.exe").is_file()
            self.mod_summary.set(
                f"Установлено модов в профиле: {len(mods)} · SMAPI: {'найден' if present else 'не установлен'}"
            )
        except ValueError:
            self.mod_summary.set("Папка игры пока не выбрана.")
        ip=core.network_ipv4()
        self.ip_label.config(text=f"IP ПК: {ip}")
        if not self.room_address.get() and coop.local_address(ip):
            self.room_address.set(ip)

    def launch(self, smapi):
        try:
            game = self.game_path()
            process = core.launch_game(game, smapi, self.profile.get())
            self._save()
            self.status.set(
                f"{'SMAPI' if smapi else 'Stardew Valley'} запущена (PID {process.pid}). "
                "Для хоста используй внутриигровое меню Co-op."
            )
        except Exception as exc:
            messagebox.showerror("Запуск Aurora", str(exc))

    def change_profile(self):
        try:
            self._save()
            self.refresh()
        except Exception as e:
            messagebox.showerror("Aurora", str(e))

    def create_profile(self):
        popup = tk.Toplevel(self)
        popup.title("Новый профиль Aurora")
        popup.geometry("400x140")
        popup.configure(bg=BG)
        self.label(popup, "Имя профиля (латиница, цифры, пробел, _ или -)", color=MUTED)
        field = tk.Entry(popup, bg=SURFACE2, fg=WHITE, insertbackground=WHITE)
        field.pack(fill="x", padx=12, pady=8)
        def create():
            name = field.get().strip()
            try:
                if name == "Default":
                    raise ValueError("Профиль Default использует игровую папку Mods.")
                directory = core.profile_folder(name)
                if directory.exists():
                    raise FileExistsError("Такой профиль уже существует.")
                directory.mkdir(parents=True)
                self.profile.set(name)
                self._save()
                self.refresh()
                popup.destroy()
            except Exception as exc:
                messagebox.showerror("Профиль", str(exc), parent=popup)
        b = tk.Button(popup, text="Создать", command=create,
                      bg=TEAL, fg=BG, relief="flat")
        b.pack(pady=4)

    def import_mod(self):
        try:
            game = self.game_path()
        except ValueError as exc:
            messagebox.showwarning("Aurora", str(exc))
            return
        picked = filedialog.askopenfilename(title="Выбери архив SMAPI-мода",
                         filetypes=[("Мод ZIP", "*.zip")])
        if not picked:
            return
        if not messagebox.askyesno("Импорт", "Установить ZIP в профиль «" +
                                   self.profile.get() + "»? Существующие моды не будут заменены."):
            return
        try:
            result = core.import_zip(Path(picked), game, self.profile.get())
            self.refresh()
            self.status.set(f"Установлен мод: {result.name}. Совместимость проверь в логе SMAPI.")
        except Exception as exc:
            messagebox.showerror("Не удалось импортировать мод", str(exc))

    def open_workshop(self):
        popup=tk.Toplevel(self)
        popup.title("Aurora Workshop 3.0 · каталоги / зависимости")
        popup.geometry("745x615")
        popup.configure(bg=BG)
        self.label(popup,"AURORA WORKSHOP 3.0",size=18,color=ACCENT,bold=True)
        self.label(popup,
            "Официальные Nexus-страницы. Установка через Import ZIP. "
            "Работа на Android не гарантируется.",size=10,color=MUTED)
        for name,category,url,modid in workshop.OFFICIAL_SOURCES:
            row=tk.Frame(popup,bg=SURFACE,padx=12,pady=6)
            row.pack(fill="x",padx=16,pady=6)
            tk.Label(row,text=f"{name} · {category}",fg=WHITE,bg=SURFACE,
                font=("Segoe UI",11,"bold"),anchor="w").pack(side="left",fill="x",expand=True)
            b=tk.Button(row,text="Открыть Nexus",bg=SURFACE2,fg=WHITE,
                command=lambda link=url:webbrowser.open(link))
            b.pack(side="right")
        dep=tk.Frame(popup,bg=SURFACE,padx=12,pady=8)
        dep.pack(fill="both",expand=True,padx=16,pady=6)
        self.label(dep,"Проверка обязательных зависимостей (по manifest.json)",bold=True)
        report=tk.Text(dep,height=10,bg=SURFACE2,fg=WHITE,insertbackground=WHITE,
                       wrap="word",font=("Consolas",10))
        report.pack(fill="both",expand=True)
        try:
            issues=workshop.check_dependencies(self.game_path(),self.profile.get())
            if not issues:
                result="Не найдено отсутствующих/устаревших обязательных зависимостей " + \
                    "по метаданным. Время выполнения и Android-совместимость не проверены."
            else:
                result="\\n".join(
                    f"{x['mod']}: {x['requires']} {x['minimum']} => {x['reason']}"
                    for x in issues
                )
            report.insert("1.0",result)
        except Exception as exc:
            report.insert("1.0",f"Не удалось прочитать профиль: {exc}")
        report.configure(state="disabled")

    def open_mods(self):
        try:
            directory = core.mods_directory(self.game_path(), self.profile.get())
            directory.mkdir(parents=True, exist_ok=True)
            os.startfile(str(directory))
        except Exception as exc:
            messagebox.showerror("Папка модов", str(exc))

    def choose_lan_ip(self):
        candidate=core.network_ipv4()
        if coop.local_address(candidate):
            self.room_address.set(candidate)
        else:
            messagebox.showerror("Aurora Coop","Нет доступного локального IPv4; проверь сеть.")

    def copy_invite(self):
        if not self.server:
            messagebox.showinfo("Aurora Coop","Сначала открой комнату.")
            return
        self.clipboard_clear()
        self.clipboard_append(self.invite.get())
        self.update()
        self.status.set("Приглашение скопировано. Отправь его только доверенному другу.")

    def start_server(self):
        if self.server:
            self.status.set("Обнаружение Aurora уже включено.")
            return
        try:
            ip=self.room_address.get().strip()
            # Must already be reachable over LAN or a separately connected VPN.
            if not coop.local_address(ip) or ip in ("0.0.0.0","100.100.100.100"):
                raise ValueError("Нужен локальный IPv4 ПК или действующий VPN IPv4.")
            self._save()
            self.server = coop.CoopLANService(
                self.game_path(), self.profile.get(),
                self.game_version.get(), self.smapi_version.get())
            self.server.start()
            self.invite.set(coop.make_invite(ip,self.server.room_token))
            self.status.set(
                "Комната активна: обнаружение UDP 24644 и доступ по токену TCP 24643. "
                "По интернету работает ТОЛЬКО при уже подключённой VPN на обоих устройствах. "
                "Не открывай порт в публичный интернет."
            )
        except Exception as exc:
            self.server = None
            messagebox.showerror("Aurora Coop", "Не удалось включить сервис: " + str(exc))

    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
        self.invite.set("Комната пока не открыта.")
        self.status.set("Комната Aurora закрыта; прежнее приглашение недействительно.")

    def close(self):
        self.stop_server()
        try:
            self._save()
        finally:
            self.destroy()


def main():
    AuroraApp().mainloop()


if __name__ == "__main__":
    main()
