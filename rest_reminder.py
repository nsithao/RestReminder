import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import threading
import time
import configparser
import os
import platform
from playsound import playsound

CONFIG_FILE = "rest_reminder.ini"

# Default settings
default_settings = {
    'Durations': {
        'work_duration': '50',  # in minutes
        'rest_duration': '10',  # in minutes
    },
    'Sound': {
        'alert_sound': ''  # path to sound file
    }
}

class RestReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rest Reminder")

        self.load_settings()

        self.work_duration = int(self.config['Durations']['work_duration']) * 60
        self.rest_duration = int(self.config['Durations']['rest_duration']) * 60
        self.alert_sound = self.config['Sound']['alert_sound']

        self.timer_running = False
        self.current_mode = None  # 'work' or 'rest'

        self.build_gui()

    def build_gui(self):
        # Menu
        menu_bar = tk.Menu(self.root)
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Set Durations", command=self.set_durations)
        settings_menu.add_command(label="Set Alert Sound", command=self.set_alert_sound)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        self.root.config(menu=menu_bar)

        # Timer Label
        self.timer_label = tk.Label(self.root, text="Ready", font=("Helvetica", 32))
        self.timer_label.pack(pady=30)

        # Start Button
        self.start_button = tk.Button(self.root, text="Start", command=self.start_work)
        self.start_button.pack(pady=10)

    def load_settings(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists(CONFIG_FILE):
            self.config.read_dict(default_settings)
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(CONFIG_FILE)

    def save_settings(self):
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

    def set_durations(self):
        work = simpledialog.askinteger("Work Duration", "Enter work duration (minutes):", initialvalue=int(self.config['Durations']['work_duration']))
        rest = simpledialog.askinteger("Rest Duration", "Enter rest duration (minutes):", initialvalue=int(self.config['Durations']['rest_duration']))
        if work and rest:
            self.config['Durations']['work_duration'] = str(work)
            self.config['Durations']['rest_duration'] = str(rest)
            self.save_settings()
            self.work_duration = work * 60
            self.rest_duration = rest * 60

    def set_alert_sound(self):
        sound_path = filedialog.askopenfilename(title="Choose alert sound", filetypes=[("Audio Files", "*.mp3 *.wav")])
        if sound_path:
            self.config['Sound']['alert_sound'] = sound_path
            self.save_settings()
            self.alert_sound = sound_path

    def start_rest(self):
        self.is_work_time = False
        self.remaining_time = self.rest_duration
        self.update_timer_label()
        self.run_timer()

    def start_work(self):
        if not self.timer_running:
            self.current_mode = 'work'
            self.start_timer(self.work_duration)

    def start_timer(self, duration):
        self.timer_running = True
        threading.Thread(target=self.run_timer, args=(duration,), daemon=True).start()

    def run_timer(self, duration):
        while duration > 0 and self.timer_running:
            mins, secs = divmod(duration, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            self.timer_label.config(text=time_str)
            time.sleep(1)
            duration -= 1

        self.timer_running = False
        if self.current_mode == 'work':
            self.show_popup("Time to rest!", self.start_rest)
        elif self.current_mode == 'rest':
            self.show_popup("Back to work!", self.start_work)

    def show_popup(self, message, callback):
        popup = tk.Toplevel(self.root)
        popup.title("Time out !!!")
        popup.attributes('-topmost', True)
        popup.geometry("300x150")
        label = tk.Label(popup, text=message, font=("Helvetica", 14))
        label.pack(pady=20)
        button = tk.Button(popup, text="Acknowledge" if self.current_mode == 'work' else "Resume to work", command=lambda: self.handle_ack(popup, callback))
        button.pack()

        if self.alert_sound:
            threading.Thread(target=playsound, args=(self.alert_sound,), daemon=True).start()

    def handle_ack(self, popup, callback):
        popup.destroy()
        if self.current_mode == 'work':
            self.current_mode = 'rest'
            self.start_timer(self.rest_duration)
        elif self.current_mode == 'rest':
            self.current_mode = 'work'
            self.start_timer(self.work_duration)

if __name__ == '__main__':
    root = tk.Tk()
    app = RestReminderApp(root)
    root.mainloop()
