import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import configparser
import time
import threading
import os
from datetime import datetime
from playsound import playsound

# Config and log file paths
CONFIG_FILE = "config.ini"
LOG_FILE = f"session_log_{datetime.now().strftime('%Y-%m-%d')}.txt"

def log_session(message):
    """
    Appends a timestamped message to the log file.
    """
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        f.write(f"{timestamp} {message}\n")

class RestReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rest Reminder")
        self.is_paused = False  # Flag for pause/resume
        self.timer_thread = None  # Background thread for countdown
        self.remaining = 0  # Seconds left in current session
        self.current_mode = None  # 'work' or 'rest'

        # Load saved durations and sound path
        self.config = configparser.ConfigParser()
        self.load_settings()

        # Create menu bar with settings option
        menubar = tk.Menu(root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Set Work Duration", command=self.set_work_duration)
        settings_menu.add_command(label="Set Rest Duration", command=self.set_rest_duration)
        settings_menu.add_command(label="Select Sound File", command=self.set_sound_file)
        menubar.add_cascade(label="Menu", menu=settings_menu)
        root.config(menu=menubar)

        # Label for countdown display
        self.label = tk.Label(root, text="Ready", font=("Arial", 24))
        self.label.pack(pady=20)

        # Start button begins the work session
        self.start_button = tk.Button(root, text="Start", command=self.start_work)
        self.start_button.pack(pady=10)

        # Pause button toggles countdown
        self.pause_button = tk.Button(root, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(pady=10)
        self.pause_button.config(state="disabled")  # Hidden until timer starts

    def load_settings(self):
        """
        Loads or creates default config.ini settings.
        """
        if not os.path.exists(CONFIG_FILE):
            self.config['TIMER'] = {
                'work_duration': '25',
                'rest_duration': '5',
                'sound_file': ''
            }
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(CONFIG_FILE)

    def set_work_duration(self):
        """Prompt for work duration and save it."""
        duration = simpledialog.askinteger("Work Duration", "Enter work duration (minutes):", initialvalue=int(self.config['TIMER']['work_duration']))
        if duration:
            self.config['TIMER']['work_duration'] = str(duration)
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)

    def set_rest_duration(self):
        """Prompt for rest duration and save it."""
        duration = simpledialog.askinteger("Rest Duration", "Enter rest duration (minutes):", initialvalue=int(self.config['TIMER']['rest_duration']))
        if duration:
            self.config['TIMER']['rest_duration'] = str(duration)
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)

    def set_sound_file(self):
        """Prompt for sound file and save it."""
        sound_file = filedialog.askopenfilename(title="Select Sound File", filetypes=[("Audio Files", "*.mp3 *.wav")])
        if sound_file:
            self.config['TIMER']['sound_file'] = sound_file
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)

    def start_work(self):
        """
        Initiates work timer based on configured duration.
        """
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.start_timer(int(self.config['TIMER']['work_duration']) * 60, "work")

    def start_rest(self):
        """
        Starts rest countdown timer.
        """
        self.start_timer(int(self.config['TIMER']['rest_duration']) * 60, "rest")

    def start_timer(self, seconds, mode):
        """
        Begins a countdown in the background.
        """
        self.remaining = seconds
        self.current_mode = mode
        self.is_paused = False
        self.update_timer()
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self.run_timer)
            self.timer_thread.start()

    def run_timer(self):
        """
        Threaded function to count down each second.
        """
        while self.remaining > 0:
            if not self.is_paused:
                time.sleep(1)
                self.remaining -= 1
                self.update_timer()
        self.on_timer_end()

    def update_timer(self):
        """
        Updates label with formatted mm:ss time.
        """
        minutes, seconds = divmod(self.remaining, 60)
        self.label.config(text=f"{self.current_mode.capitalize()} Time: {minutes:02d}:{seconds:02d}")

    def toggle_pause(self):
        """
        Pauses or resumes the countdown.
        """
        self.is_paused = not self.is_paused
        self.pause_button.config(text="Resume" if self.is_paused else "Pause")

    def on_timer_end(self):
        """
        Called when countdown ends. Shows popup + sound.
        """
        self.play_sound()
        self.root.after(0, lambda: self.show_popup(
            "Time to rest!" if self.current_mode == "work" else "Back to work!",
            self.start_rest if self.current_mode == "work" else self.start_work
        ))
        log_session(f"Finished {self.current_mode} session.")

    def show_popup(self, message, callback):
        """
        Shows a popup window that stays on top.
        """
        popup = tk.Toplevel(self.root)
        popup.title("Reminder")
        popup.attributes('-topmost', True)
        tk.Label(popup, text=message, font=("Arial", 18)).pack(pady=10)
        tk.Button(popup, text="Acknowledge", command=lambda: [popup.destroy(), callback()]).pack(pady=10)

    def play_sound(self):
        """
        Plays the configured sound file.
        """
        sound_file = self.config['TIMER']['sound_file']
        if sound_file and os.path.exists(sound_file):
            threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()

# Entry point of the app
if __name__ == "__main__":
    root = tk.Tk()
    app = RestReminderApp(root)
    root.mainloop()
