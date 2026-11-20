import os, json, csv, time
from datetime import datetime, date
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserIconView
from kivy.graphics import Color, RoundedRectangle

try:
    from plyer import notification, vibrator
except Exception:
    notification = vibrator = None

APP_DIR = Path.home() / ".pro_pomodoro"
APP_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = APP_DIR / "data.json"
CSV_FILE = APP_DIR / "focus_history.csv"

DEFAULTS = {
    "focus_minutes": 25, "short_break_minutes": 5, "long_break_minutes": 15,
    "long_break_after": 4, "theme": "dark", "wallpaper": "",
    "sound": "Chime", "volume": 0.8, "tasks": [], "sessions": [],
    "completed_today": 0, "last_day": str(date.today()), "streak": 0,
}

def load_data():
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        merged = DEFAULTS.copy()
        merged.update(data)
        return merged
    except Exception:
        return DEFAULTS.copy()

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

class PomodoroApp(App):
    remaining = NumericProperty(25 * 60)
    progress = NumericProperty(0)
    mode = StringProperty("Ready to focus")
    running = BooleanProperty(False)
    selected_task = StringProperty("No task selected")
    time_text = StringProperty("25:00")

    def build(self):
        self.data = load_data()
        self._event = None
        self._last_tick = None
        self._sound_obj = None
        self._session_start = None
        self._focus_count = 0
        self._refresh_day()
        self._set_theme()
        self.remaining = self.data["focus_minutes"] * 60
        self.total = self.remaining
        self._refresh_time()

        self.root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(10))
        self.root.bind(size=self._draw_background, pos=self._draw_background)
        with self.root.canvas.before:
            self.bg_color = Color(*self.palette["bg"])
            self.bg_rect = RoundedRectangle(pos=self.root.pos, size=self.root.size, radius=[dp(20)])
        self._draw_background()

        header = BoxLayout(size_hint_y=None, height=dp(42))
        header.add_widget(self._label("PRO · POMODORO", 18, True, "muted"))
        header.add_widget(self._button("⚙ Settings", self.open_settings, width=dp(112)))
        self.root.add_widget(header)

        self.state_label = self._label(self.mode, 15, False, "muted")
        self.root.add_widget(self.state_label)
        self.clock_label = self._label(self.time_text, 62, True, "text")
        self.root.add_widget(self.clock_label)
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))
        self.root.add_widget(self.progress_bar)

        self.counter_label = self._label("", 14, False, "muted")
        self.root.add_widget(self.counter_label)
        self.task_label = self._label(self.selected_task, 18, True, "text")
        self.root.add_widget(self.task_label)

        controls = GridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(52))
        controls.add_widget(self._button("Start", self.start_timer))
        controls.add_widget(self._button("Pause", self.pause_timer))
        controls.add_widget(self._button("Reset", self.reset_timer))
        self.root.add_widget(controls)

        task_header = BoxLayout(size_hint_y=None, height=dp(38))
        task_header.add_widget(self._label("YOUR TASKS", 14, True, "muted"))
        task_header.add_widget(self._button("+ Add task", self.add_task, width=dp(112)))
        self.root.add_widget(task_header)

        self.task_list = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.task_list.bind(minimum_height=self.task_list.setter("height"))
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView()
        scroll.add_widget(self.task_list)
        self.root.add_widget(scroll)

        footer = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(44))
        footer.add_widget(self._button("Analytics", self.show_analytics))
        footer.add_widget(self._button("Export CSV", self.export_csv))
        self.root.add_widget(footer)
        self.refresh_tasks()
        self.refresh_counters()
        Window.bind(on_keyboard=self._on_keyboard)
        return self.root

    def _set_theme(self):
        self.dark = self.data.get("theme", "dark") == "dark"
        self.palette = {
            "bg": (0.055, 0.07, 0.11, 1) if self.dark else (0.94, 0.96, 0.99, 1),
            "panel": (0.10, 0.13, 0.19, 1) if self.dark else (1, 1, 1, 1),
            "text": (0.94, 0.96, 1, 1) if self.dark else (0.08, 0.11, 0.17, 1),
            "muted": (0.62, 0.68, 0.78, 1) if self.dark else (0.35, 0.40, 0.48, 1),
            "accent": (0.30, 0.62, 0.98, 1),
        }

    def _draw_background(self, *_):
        if hasattr(self, "bg_rect"):
            self.bg_color.rgba = self.palette["bg"]
            self.bg_rect.pos = self.root.pos
            self.bg_rect.size = self.root.size

    def _label(self, text, size=16, bold=False, color="text"):
        lbl = Label(text=text, font_size=dp(size), bold=bold, color=self.palette[color],
                    halign="center", valign="middle", size_hint_y=None, height=dp(max(28, size*1.65)))
        lbl.bind(size=lambda obj, val: setattr(obj, "text_size", val))
        return lbl

    def _button(self, text, callback, width=None):
        btn = Button(text=text, size_hint_x=None if width else 1, width=width or 0,
                     background_normal="", background_down="",
                     background_color=self.palette["accent"], color=(1,1,1,1),
                     font_size=dp(14), bold=True)
        btn.bind(on_release=lambda *_: callback())
        return btn

    def _refresh_day(self):
        today = str(date.today())
        if self.data.get("last_day") != today:
            yesterday = str(date.fromordinal(date.today().toordinal()-1))
            if self.data.get("last_day") == yesterday and self.data.get("completed_today", 0):
                self.data["streak"] = int(self.data.get("streak", 0)) + 1
            elif self.data.get("last_day") != today:
                self.data["streak"] = 0
            self.data["completed_today"] = 0
            self.data["last_day"] = today
            save_data(self.data)

    def _refresh_time(self):
        mins, secs = divmod(max(0, int(self.remaining)), 60)
        self.time_text = f"{mins:02d}:{secs:02d}"
        if hasattr(self, "clock_label"):
            self.clock_label.text = self.time_text
            self.state_label.text = self.mode
            self.progress_bar.value = self.progress
            self.task_label.text = self.selected_task

    def refresh_counters(self):
        if hasattr(self, "counter_label"):
            self.counter_label.text = f"Pomodoros today: {self.data.get('completed_today', 0)}  ·  Streak: {self.data.get('streak', 0)} days"

    def refresh_tasks(self):
        if not hasattr(self, "task_list"): return
        self.task_list.clear_widgets()
        for i, task in enumerate(self.data["tasks"]):
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            label = Button(text=("● " if task.get("active") else "○ ") + task["title"] +
                           f"   ·   {task.get('done',0)}/{task.get('target',1)}",
                           halign="left", background_normal="", background_color=self.palette["panel"],
                           color=self.palette["text"])
            label.bind(on_release=lambda _, idx=i: self.select_task(idx))
            delete = Button(text="×", size_hint_x=None, width=dp(42), background_normal="",
                            background_color=(0.65,0.22,0.25,1))
            delete.bind(on_release=lambda _, idx=i: self.delete_task(idx))
            row.add_widget(label); row.add_widget(delete)
            self.task_list.add_widget(row)
        active = next((t for t in self.data["tasks"] if t.get("active")), None)
        self.selected_task = active["title"] if active else "No task selected"
        if hasattr(self, "task_label"): self.task_label.text = self.selected_task

    def add_task(self):
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        title = TextInput(hint_text="Task title", multiline=False, size_hint_y=None, height=dp(44))
        due = TextInput(hint_text="Due date (optional, YYYY-MM-DD)", multiline=False, size_hint_y=None, height=dp(44))
        target = TextInput(text="4", hint_text="Pomodoros planned", input_filter="int", multiline=False, size_hint_y=None, height=dp(44))
        box.add_widget(title); box.add_widget(due); box.add_widget(target)
        pop = Popup(title="Add a task", content=box, size_hint=(.9, None), height=dp(260))
        save = self._button("Save task", lambda: self._save_task(title.text, due.text, target.text, pop))
        box.add_widget(save); pop.open()

    def _save_task(self, title, due, target, popup):
        if title.strip():
            self.data["tasks"].append({"title": title.strip(), "due": due.strip(),
                "target": max(1, int(target or 1)), "done": 0, "active": not self.data["tasks"]})
            save_data(self.data); self.refresh_tasks()
        popup.dismiss()

    def select_task(self, index):
        for i, task in enumerate(self.data["tasks"]): task["active"] = i == index
        save_data(self.data); self.refresh_tasks()

    def delete_task(self, index):
        self.data["tasks"].pop(index)
        if self.data["tasks"] and not any(t.get("active") for t in self.data["tasks"]):
            self.data["tasks"][0]["active"] = True
        save_data(self.data); self.refresh_tasks()

    def start_timer(self):
        if self.running: return
        if self.total <= 0: self._prepare_focus()
        self.running = True
        self._last_tick = time.monotonic()
        self.mode = "Focus" if self.mode in ("Ready to focus", "Focus", "Paused") else self.mode
        self._play_sound("Focus start")
        self._event = Clock.schedule_interval(self._tick, .2)
        self._refresh_time()

    def pause_timer(self):
        if not self.running: return
        self.running = False
        if self._event: self._event.cancel(); self._event = None
        self.mode = "Paused"
        self._refresh_time()

    def reset_timer(self):
        self.pause_timer()
        self.mode = "Ready to focus"
        self.remaining = self.data["focus_minutes"] * 60
        self.total = self.remaining
        self.progress = 0
        self._refresh_time()

    def _prepare_focus(self):
        self.mode = "Focus"
        self.remaining = self.data["focus_minutes"] * 60
        self.total = self.remaining
        self.progress = 0

    def _tick(self, _dt):
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._last_tick = now
        self.remaining -= elapsed
        self.progress = min(100, 100 * (1 - self.remaining / max(1, self.total)))
        self._refresh_time()
        if self.remaining <= 0:
            self._event.cancel(); self._event = None; self.running = False
            self._segment_complete()
        return True

    def _segment_complete(self):
        if self.mode == "Focus":
            self._focus_count += 1
            self.data["completed_today"] = int(self.data.get("completed_today", 0)) + 1
            active = next((t for t in self.data["tasks"] if t.get("active")), None)
            if active:
                active["done"] = active.get("done", 0) + 1
            record = {"date": datetime.now().isoformat(timespec="seconds"), "type":"focus",
                      "minutes": self.data["focus_minutes"], "task": active["title"] if active else ""}
            self.data["sessions"].append(record)
            self._append_csv(record)
            long_after = max(1, int(self.data.get("long_break_after", 4)))
            is_long = self._focus_count % long_after == 0
            self.mode = "Long break" if is_long else "Short break"
            mins = self.data["long_break_minutes"] if is_long else self.data["short_break_minutes"]
            self.remaining = mins * 60; self.total = self.remaining; self.progress = 0
            self._play_sound("Long break" if is_long else "Pomodoro end")
            self._notify("Focus session complete", "Time for a " + self.mode.lower() + ".")
            save_data(self.data); self.refresh_tasks(); self.refresh_counters()
            self._popup_message("Great work!", f"Focus session complete. Time for a {self.mode.lower()}.")
        else:
            self.mode = "Ready to focus"
            self.remaining = self.data["focus_minutes"] * 60
            self.total = self.remaining; self.progress = 0
            self._play_sound("Break end")
            self._notify("Break complete", "Ready for the next Pomodoro?")
            self._popup_message("Break complete", "Ready for the next Pomodoro?")
        self._refresh_time()

    def _append_csv(self, record):
        new = not CSV_FILE.exists()
        with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date","type","minutes","task"])
            if new: writer.writeheader()
            writer.writerow(record)

    def _play_sound(self, event):
        sound_name = self.data.get("sound", "Chime")
        if sound_name == "None": return
        # Built-in synthesized fallback; custom WAV/MP3 can be selected in settings.
        path = self.data.get("custom_sound", "")
        if path and os.path.isfile(path):
            snd = SoundLoader.load(path)
            if snd:
                snd.volume = float(self.data.get("volume", .8)); snd.play(); return
        try:
            from kivy.core.audio import SoundLoader
            # Use a short system notification where available; UI remains functional without assets.
            if notification: notification.notify(title="Pro-Pomodoro", message=event)
        except Exception: pass
        if vibrator:
            try: vibrator.vibrate(time=.15)
            except Exception: pass

    def _notify(self, title, message):
        if notification:
            try: notification.notify(title=title, message=message, timeout=5)
            except Exception: pass

    def _popup_message(self, title, message):
        Popup(title=title, content=Label(text=message), size_hint=(.82,.32)).open()

    def open_settings(self):
        box = BoxLayout(orientation="vertical", spacing=dp(7), padding=dp(10))
        fields = {}
        for key, label in [("focus_minutes","Focus minutes"),("short_break_minutes","Short break minutes"),
                           ("long_break_minutes","Long break minutes"),("long_break_after","Long break after focus sessions")]:
            row = BoxLayout(size_hint_y=None, height=dp(40))
            row.add_widget(Label(text=label, color=self.palette["text"]))
            inp = TextInput(text=str(self.data[key]), input_filter="int", multiline=False, size_hint_x=.35)
            fields[key] = inp; row.add_widget(inp); box.add_widget(row)
        theme_btn = self._button("Toggle dark / light", self.toggle_theme)
        box.add_widget(theme_btn)
        sound_row = BoxLayout(size_hint_y=None, height=dp(42))
        sound_row.add_widget(Label(text="Alarm sound", color=self.palette["text"]))
        from kivy.uix.spinner import Spinner
        spinner = Spinner(text=self.data.get("sound","Chime"), values=("Chime","Beep","Digital","Alarm","None"))
        sound_row.add_widget(spinner); box.add_widget(sound_row)
        vol = TextInput(text=str(self.data.get("volume",.8)), hint_text="Volume 0–1", multiline=False, size_hint_y=None, height=dp(40))
        box.add_widget(vol)
        pop = Popup(title="Settings", content=box, size_hint=(.92,.85))
        def save_settings():
            for k, inp in fields.items():
                self.data[k] = max(1, int(inp.text or DEFAULTS[k]))
            self.data["sound"] = spinner.text
            try: self.data["volume"] = min(1, max(0, float(vol.text)))
            except: self.data["volume"] = .8
            save_data(self.data); pop.dismiss()
            if not self.running and self.mode in ("Ready to focus", "Paused"): self.reset_timer()
        box.add_widget(self._button("Choose wallpaper", lambda: self.choose_wallpaper()))
        box.add_widget(self._button("Choose custom alarm audio", lambda: self.choose_audio()))
        box.add_widget(self._button("Save settings", save_settings))
        pop.open()

    def toggle_theme(self):
        self.data["theme"] = "light" if self.dark else "dark"
        save_data(self.data)
        self._popup_message("Theme updated", "Reopen settings to see the selected theme.")

    def choose_wallpaper(self):
        chooser = FileChooserIconView(filters=["*.png","*.jpg","*.jpeg","*.webp"])
        pop = Popup(title="Choose wallpaper image", content=chooser, size_hint=(.95,.9))
        def choose(*_):
            if chooser.selection:
                self.data["wallpaper"] = chooser.selection[0]
                save_data(self.data); pop.dismiss()
                self._popup_message("Wallpaper saved", "Wallpaper preference saved. A themed background is used in this build.")
        chooser.bind(on_submit=choose)
        pop.open()

    def choose_audio(self):
        chooser = FileChooserIconView(filters=["*.wav","*.mp3","*.ogg"])
        pop = Popup(title="Choose alarm audio", content=chooser, size_hint=(.95,.9))
        def choose(*_):
            if chooser.selection:
                self.data["custom_sound"] = chooser.selection[0]
                save_data(self.data); pop.dismiss()
        chooser.bind(on_submit=choose)
        pop.open()

    def show_analytics(self):
        sessions = self.data.get("sessions", [])
        total = sum(int(s.get("minutes",0)) for s in sessions if s.get("type") == "focus")
        today = [s for s in sessions if s.get("date","")[:10] == str(date.today())]
        msg = (f"Focus time: {total // 60}h {total % 60}m\n"
               f"Sessions logged: {len(sessions)}\n"
               f"Today: {len(today)} completed focus sessions\n"
               f"Current streak: {self.data.get('streak',0)} days")
        self._popup_message("Your progress", msg)

    def export_csv(self):
        if not CSV_FILE.exists():
            self._popup_message("Nothing to export", "Complete a focus session first.")
            return
        self._popup_message("CSV exported", f"Your history is saved at:\n{CSV_FILE}")

    def _on_keyboard(self, window, key, *_):
        if key == 32:
            self.pause_timer() if self.running else self.start_timer()
            return True
        return False

    def on_stop(self):
        self.pause_timer()
        save_data(self.data)

if __name__ == "__main__":
    PomodoroApp().run()
