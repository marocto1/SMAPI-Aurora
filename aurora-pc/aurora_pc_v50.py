"""Aurora SMAPI PC v2.0: invite-only local/VPN rooms, mods and game launch."""
from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog

import aurora_core as core
import coop_v20 as coop
import coop_v27 as udpcoop
import workshop_v25 as workshop
import network_v24 as network
import safety_v22 as safety
import recovery_v26 as recovery
import modaudit_v28 as audit
import readiness_v40 as readiness
import link_v41 as link
import workshop_v43 as transfer
import threading
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
        self.title("Aurora SMAPI PC · v5.0.0-rc.1")
        self.geometry("1100x960")
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
        self.label(header, "AURORA  /  NEXT GENERATION 5.0", size=24, color=ACCENT, bold=True)
        self.label(header,
                   "Stardew Valley · SMAPI · Recovery 2.6 · Coop 2.7 · Mods 2.8",
                   size=11, color=MUTED)
        # RC2: a tall Control Center must be scrollable even on 768p screens.
        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(fill="both", expand=True)
        canvas = tk.Canvas(wrapper, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        outer = tk.Frame(canvas, bg=BG, padx=26)
        window_id = canvas.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>", lambda event: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(
            window_id, width=event.width))
        self._content_canvas = canvas
        # RC2: mouse wheel works while pointer is over the scrollable surface.
        def wheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        canvas.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>",wheel))
        canvas.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))
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
        self.button(row,"Workshop 5.0",self.open_workshop)
        utilities=self.row(modsp)
        self.button(utilities,"Резервная копия профиля",self.export_mod_backup)
        self.button(utilities,"Проверить VPN",self.show_vpn_status)
        recover=self.row(modsp)
        self.button(recover,"Recovery: ZIP → новый профиль",self.restore_isolated_profile)
        self.button(recover,"Сравнить профили",self.compare_profiles)
        exchange=self.row(modsp)
        self.button(exchange,"Экспорт метаданных профиля",self.export_mod_manifest)
        self.button(exchange,"Сравнить с отчётом друга",self.compare_peer_manifest)
        self.mod_summary = tk.StringVar()
        tk.Label(modsp, textvariable=self.mod_summary, bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 10), anchor="w").pack(fill="x", pady=5)

        coop = self.panel(outer)
        self.label(coop, "3. AURORA COOP · ЛОКАЛЬНАЯ СЕТЬ", size=11, bold=True)
        checkrow=self.row(coop)
        self.button(checkrow,"Проверить готовность ПК",self.show_readiness,primary=True)
        self.button(checkrow,"Скопировать отчёт",self.copy_readiness)
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
        self.button(code_row,"QR приглашения",self.show_invite_qr)
        cooprow = self.row(coop)
        self.button(cooprow, "Открыть комнату Aurora", self.start_server, primary=True)
        self.button(cooprow, "Закрыть комнату", self.stop_server)
        self.label(coop,"Дополнительный UDP 24645: диагностический эхо-тест Aurora. "
                   "Не проверяет игровой UDP 24642.",color=MUTED,size=9)
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
        popup.title("Aurora Workshop 4.0 · поиск / категории / зависимости")
        popup.geometry("765x720")
        popup.configure(bg=BG)
        self.label(popup,"AURORA WORKSHOP 4.0",size=18,color=ACCENT,bold=True)
        self.label(popup,
            "Официальные Nexus-страницы. Установка через Import ZIP. "
            "Работа на Android не гарантируется.",size=10,color=MUTED)
        searchrow=tk.Frame(popup,bg=BG,padx=15,pady=10)
        searchrow.pack(fill="x")
        query=tk.StringVar()
        selection=tk.StringVar(value="Все")
        tk.Entry(searchrow,textvariable=query,bg=SURFACE2,fg=WHITE,
                 insertbackground=WHITE).pack(side="left",fill="x",expand=True,ipady=8,padx=(0,8))
        names=["Все"]+sorted({row[1] for row in workshop.OFFICIAL_SOURCES})
        ttk.Combobox(searchrow,textvariable=selection,values=names,
                     state="readonly",width=17).pack(side="right")
        listframe=tk.Frame(popup,bg=BG)
        listframe.pack(fill="x")
        def render_catalog(*_):
            for child in listframe.winfo_children():child.destroy()
            chosen=selection.get()
            find=query.get().strip().lower()
            for name,category,url,modid in workshop.OFFICIAL_SOURCES:
                if chosen!="Все" and category!=chosen:continue
                if find and find not in (name+" "+category).lower():continue
                row=tk.Frame(listframe,bg=SURFACE,padx=10,pady=4)
                row.pack(fill="x",padx=15,pady=3)
                tk.Label(row,text=f"{name} · {category}",fg=WHITE,bg=SURFACE,
                    font=("Segoe UI",10,"bold"),anchor="w").pack(side="left",fill="x",expand=True)
                tk.Button(row,text="Nexus",bg=SURFACE2,fg=WHITE,
                          command=lambda link=url:webbrowser.open(link)).pack(side="right")
        query.trace_add("write",render_catalog)
        selection.trace_add("write",render_catalog)
        render_catalog()
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

    def restore_isolated_profile(self):
        archive=filedialog.askopenfilename(
            title="Выбери проверенный ZIP Aurora PC v2.2",
            filetypes=[("Aurora backup ZIP","*.zip")])
        if not archive:return
        name=simpledialog.askstring("Aurora Recovery 2.6",
            "Имя НОВОГО профиля (никогда не заменяем Default/старые):",parent=self)
        if not name:return
        try:
            # Dry-run validates path layout and manifest. This is a preview only.
            file_count=len(recovery.preview_archive(Path(archive)))
            folder=core.profile_folder(name)
            if folder.parent.exists():
                raise FileExistsError("Такой профиль уже существует. Выбери новое имя.")
        except Exception as error:
            messagebox.showerror("Recovery · Проверка",str(error))
            return
        if not messagebox.askyesno("Aurora Recovery 2.6",
            f"Проверено метаданных: {file_count} файлов. " +
            f"Восстановить в новый профиль «{name}»? " +
            "Каждый байт будет повторно проверен SHA-256 перед записью профиля. " +
            "Игра и Default Mods останутся неизменны."):
            return
        self.status.set("Восстанавливаем отдельный профиль; не закрывай приложение.")
        def task():
            try:
                recovery.restore_new_profile(Path(archive),name)
                ok=True;message="Новый профиль создан и проверен: "+name
            except Exception as error:
                ok=False;message="Recovery отказала: "+str(error)
            def done():
                if ok:
                    self.profile.set(name);self.refresh()
                    messagebox.showinfo("Aurora Recovery",message)
                else:messagebox.showerror("Aurora Recovery",message)
                self.status.set(message)
            self.after(0,done)
        threading.Thread(target=task,daemon=True,
                         name="AuroraVerifiedRecovery").start()

    def compare_profiles(self):
        profiles=core.available_profiles()
        current=self.profile.get()
        others=[x for x in profiles if x!=current]
        if not others:
            messagebox.showinfo("Mod Manager Pro",
                "Создай второй профиль, чтобы сравнить моды. Ничего не будет изменено.")
            return
        second=simpledialog.askstring("Mod Manager Pro",
            "С чем сравнить активный профиль "+current+"?\\n"+
            "Доступно: "+", ".join(others),parent=self)
        if not second:return
        if second not in others:
            messagebox.showerror("Mod Manager Pro","Выбери существующий второй профиль.")
            return
        try:
            report=audit.compare_profiles(self.game_path(),current,second)
            message=audit.summarize(report)
        except Exception as error:
            messagebox.showerror("Mod Manager Pro",str(error));return
        popup=tk.Toplevel(self)
        popup.title("Aurora Mod Manager Pro · сравнение профилей")
        popup.geometry("750x540");popup.configure(bg=BG)
        t=tk.Text(popup,bg=SURFACE,fg=WHITE,wrap="word",
                  font=("Consolas",11))
        t.pack(fill="both",expand=True,padx=16,pady=16)
        t.insert("1.0",message);t.configure(state="disabled")

    def _readiness_text(self):
        game=self.game_path()
        report=readiness.prepare_readiness(
            game,self.profile.get(),declared_game=self.game_version.get().strip(),
            declared_smapi=self.smapi_version.get().strip(),
            room_ip=self.room_address.get().strip(),room_open=self.server is not None)
        return readiness.format_report(report)

    def show_readiness(self):
        try:
            content=self._readiness_text()
        except Exception as error:
            messagebox.showerror("Aurora Unified 4.0",str(error))
            return
        popup=tk.Toplevel(self)
        popup.title("Aurora Unified · Проверка готовности")
        popup.geometry("720x510")
        popup.configure(bg=BG)
        heading=tk.Label(popup,text="AURORA  /  UNIFIED PREFLIGHT",
            bg=BG,fg=ACCENT,font=("Segoe UI",17,"bold"))
        heading.pack(fill="x",padx=17,pady=(18,5))
        txt=tk.Text(popup,bg=SURFACE,fg=WHITE,wrap="word",
                    font=("Consolas",11))
        txt.pack(fill="both",expand=True,padx=18,pady=(0,16))
        txt.insert("1.0",content)
        txt.configure(state="disabled")

    def copy_readiness(self):
        try:
            content=self._readiness_text()
        except Exception as error:
            messagebox.showerror("Aurora Unified",str(error));return
        self.clipboard_clear()
        self.clipboard_append(content)
        self.update()
        self.status.set("Aurora Unified: диагностический отчёт скопирован, без токена комнаты.")

    def export_mod_backup(self):
        try:
            directory=core.mods_directory(self.game_path(),self.profile.get())
        except Exception as error:
            messagebox.showerror("Aurora Safe Backup",str(error))
            return
        file=filedialog.asksaveasfilename(
            title="Сохранить новую ZIP-копию модов вне папки игры",
            defaultextension=".zip",filetypes=[("ZIP archive","*.zip")])
        if not file:return
        if not messagebox.askyesno("Aurora Safe Backup",
            "Создать проверенную копию ТОЛЬКО модов текущего PC-профиля? " +
            "Сохранения Stardew сюда не входят. Закрой игру перед копированием."):
            return
        self.status.set("Создаём и повторно проверяем ZIP. Приложение остаётся доступным.")
        def task():
            try:
                count=safety.backup_profile(directory,Path(file))
                message=f"Готово: {count} файлов модов, SHA-256 проверены. Сохранения не включены."
                error=False
            except Exception as exc:
                message=str(exc);error=True
            def finished():
                self.status.set("Backup: "+message)
                if error: messagebox.showerror("Backup",message)
                else:messagebox.showinfo("Backup",message)
            self.after(0,finished)
        threading.Thread(target=task,daemon=True,name="AuroraVerifiedModBackup").start()

    def show_vpn_status(self):
        self.status.set("Проверяем локальный статус клиента VPN...")
        def worker():
            status=network.tailscale_state()
            def done():
                if status.get("running") and status.get("ipv4"):
                    ip=status["ipv4"][0]
                    self.room_address.set(ip)
                    message="Tailscale активен. Подставлен IPv4 "+ip+" — " + \
                            "подключение к игровой ферме не подтверждено."
                else:
                    message=status.get("message","VPN не обнаружена")
                self.status.set(message)
                messagebox.showinfo("Aurora Network 2.0",message)
            self.after(0,done)
        threading.Thread(target=worker,daemon=True,name="AuroraVPNCheck").start()

    def open_mods(self):
        try:
            directory = core.mods_directory(self.game_path(), self.profile.get())
            directory.mkdir(parents=True, exist_ok=True)
            os.startfile(str(directory))
        except Exception as exc:
            messagebox.showerror("Папка модов", str(exc))

    def show_invite_qr(self):
        if not self.server:
            messagebox.showinfo("Aurora Link 4.1","Сначала открой комнату.")
            return
        try:
            from PIL import ImageTk
            picture=link.generate_qr_image(self.invite.get())
            popup=tk.Toplevel(self)
            popup.title("Aurora Link · QR-код приглашения")
            popup.configure(bg=BG)
            tk.Label(popup,text="Покажи только доверенному другу: QR содержит токен комнаты.",
                     fg=WHITE,bg=BG,font=("Segoe UI",10)).pack(padx=16,pady=10)
            photo=ImageTk.PhotoImage(picture)
            label=tk.Label(popup,image=photo,bg=BG)
            label.image=photo
            label.pack(padx=15,pady=12)
            self.label(popup,"Закрытие и повторное открытие комнаты меняет токен.",
                       size=10,color=MUTED)
        except Exception as error:
            messagebox.showerror("Aurora Link 4.1","Не удалось нарисовать QR: "+str(error))

    def export_mod_manifest(self):
        try:
            data=transfer.profile_report(self.game_path(),self.profile.get())
            target=filedialog.asksaveasfilename(title="Сохранить НОВЫЙ отчёт о модах",
                defaultextension=".json",filetypes=[("Aurora profile JSON","*.json")])
            if not target:return
            transfer.export_report(data,Path(target))
            self.status.set("Готово: экспортированы только ID и версии модов, без DLL/сохранений.")
        except Exception as error:
            messagebox.showerror("Workshop 5.0",str(error))

    def compare_peer_manifest(self):
        try:
            remote=filedialog.askopenfilename(title="Отчёт модов друга",
                filetypes=[("Aurora JSON","*.json")])
            if not remote:return
            peer=transfer.read_report(Path(remote))
            own=transfer.profile_report(self.game_path(),self.profile.get())
            diff=transfer.compare_reports(own,peer)
            message=transfer.format_comparison(diff)
            popup=tk.Toplevel(self)
            popup.title("Workshop 5.0 · Сравнение без изменения модов")
            popup.geometry("710x540");popup.configure(bg=BG)
            txt=tk.Text(popup,bg=SURFACE,fg=WHITE,wrap="word",
                        font=("Consolas",11))
            txt.pack(fill="both",expand=True,padx=16,pady=16)
            txt.insert("1.0",message);txt.configure(state="disabled")
        except Exception as error:
            messagebox.showerror("Workshop 5.0",str(error))

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
            self.server = udpcoop.CoopAdvancedService(
                self.game_path(), self.profile.get(),
                self.game_version.get(), self.smapi_version.get())
            self.server.start()
            self.invite.set(coop.make_invite(ip,self.server.room_token))
            self.status.set(
                "Комната активна: UDP автопоиск 24644 / проба 24645 и защищённый токеном TCP 24643. "
                "По интернету работает ТОЛЬКО при уже подключённой VPN на обоих устройствах. "
                "Не открывай порт в публичный интернет."
            )
        except Exception as exc:
            if self.server is not None:
                try:
                    self.server.stop()
                except Exception:
                    pass
            self.server = None
            self.invite.set("Комната пока не открыта.")
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
