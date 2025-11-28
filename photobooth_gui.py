#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import subprocess
import threading
import time
import stat
import pygame
from datetime import datetime
from pathlib import Path
from tkinter import Tk, Label, StringVar
from PIL import Image, ImageTk, ImageOps, ImageColor, Image
from AppKit import NSApp
from tkinter import ttk, messagebox
from typing import List
import platform
# --- Added: optional PowerMate launcher (minimal) ---
def launch_powermate():
    try:
        if platform.system() != "Darwin":
            return
        app_path = "/Applications/PowerMate.app"
        if os.path.exists(app_path):
            subprocess.Popen(["open", "-a", "PowerMate"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Fail silently to avoid altering behavior
        pass



# === Configurable Constants ===
CROP_WIDTH = 2580
CROP_HEIGHT = 2955
GAP_BETWEEN = 180
BORDER_SIDE = 0
BORDER_TOP_BOTTOM = 180
WINDOW_WIDTH_SCALE = 0.5
WINDOW_HEIGHT_SCALE = 0.90
WINDOW_X_POSITION = 160
PREVIEW_SCALE = 0.2
STRIP_PREVIEW_SCALE = 0.05
FONT_STYLE = ("Helvetica", 30)

# === Crop Offsets ===
CROP_VERTICAL_OFFSET = -350    # Negative = shift up
CROP_HORIZONTAL_OFFSET = 25    # Negative = shift left

# === Theme Colors ===
BG_COLOR = "#303030"  # Dark grey
FG_COLOR = "white"    # Text color

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent
ORIGINALS_DIR = BASE_DIR / "Originals"
CROPPED_DIR = Path.home() / "Dropbox" / "FotoPile" / "Cropped"
STRIPS_DIR = Path.home() / "Desktop" / "Strips"
AUDIO_DIR = BASE_DIR / "Audio"
WAKE_DIR = AUDIO_DIR / "Wake"
PROCESS_DIR = AUDIO_DIR / "Process"
DONE_DIR = None  # can be None; we guard for it
PHOTO1_DIR = AUDIO_DIR / "Photo1"
PHOTO2_DIR = AUDIO_DIR / "Photo2"
PHOTO3_DIR = AUDIO_DIR / "Photo3"
PHOTO4_DIR = AUDIO_DIR / "Photo4"
LOG_DIR = BASE_DIR / "Logs"
LOG_FILE = LOG_DIR / "log.txt"
DUMMY_IMAGE_PATH = BASE_DIR / "placeholder.jpg"

for folder in [ORIGINALS_DIR, CROPPED_DIR, STRIPS_DIR, LOG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ---------- Logging ----------
def log_event(message: str):
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

# ---------- Printing ----------
def print_strip_direct(strip_path: Path):
    log_event("🖨️ Sending strip to printer...")
    try:
        subprocess.run(["chmod", "a+r", str(strip_path)], check=False)
        subprocess.run([
            "lp", "-d", "EPSON_PM_400_Series",
            "-o", "PageSize=Custom.150x612",
            "-o", "Resolution=1440x1440dpi",
            "-o", "ColorModel=RGB",
            "-o", "MediaType=GlossyPhoto",
            "-o", "StpQuality=Photo",
            "-o", "OutputOrder=Reverse",
            "-o", "StpColorPrecision=Best",
            "-o", "page-top=0",
            "-o", "page-left=12",
            "-o", "position=top",
            "-o", "StpiShrinkOutput=Crop",
            str(strip_path)
        ], check=True)
        log_event(f"🖨️ Print command sent for: {strip_path.name}")
    except Exception as e:
        log_event(f"❌ Printing failed: {e}")

# ---------- Off-center crop helpers (top-level) ----------
def _clamp(val, lo, hi):
    return max(lo, min(hi, val))

def crop_off_center(img: Image.Image) -> Image.Image:
    """
    Crop using CROP_WIDTH/HEIGHT, offset from center by:
      +CROP_HORIZONTAL_OFFSET => shift right;  - => left
      +CROP_VERTICAL_OFFSET   => shift down;   - => up
    Offsets are applied AFTER rotation.
    """
    w, h = img.size
    cx, cy = w // 2, h // 2
    left = cx - (CROP_WIDTH // 2) + CROP_HORIZONTAL_OFFSET
    top  = cy - (CROP_HEIGHT // 2) + CROP_VERTICAL_OFFSET
    left = _clamp(left, 0, max(0, w - CROP_WIDTH))
    top  = _clamp(top,  0, max(0, h - CROP_HEIGHT))
    return img.crop((left, top, left + CROP_WIDTH, top + CROP_HEIGHT))

# ---------- GUI ----------
def launch_gui():
    root = Tk()
    root.configure(bg=BG_COLOR)
    root.title("Foto Booth")

    root.lift()
    root.attributes("-topmost", True)
    root.after(0, root.focus_force)
    root.after(1000, lambda: root.attributes("-topmost", False))

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * WINDOW_WIDTH_SCALE)
    window_height = int(screen_height * WINDOW_HEIGHT_SCALE)
    root.geometry(f"{window_width}x{window_height}+{WINDOW_X_POSITION}+30")

    Label(root, text="\n", bg=BG_COLOR, fg=FG_COLOR).pack()

    status = StringVar()
    status.set("Press any key to begin...")
    status_label = Label(root, textvariable=status, font=FONT_STYLE, bg=BG_COLOR, fg=FG_COLOR)
    status_label.pack()
    Label(root, text="\n", bg=BG_COLOR).pack()
    preview_label = Label(root, bg=BG_COLOR, fg=FG_COLOR, bd=0, relief="flat")
    preview_label.pack()

    session_state = {'active': False, 'completed': False}

    style = ttk.Style()
    try:
        style.theme_use("alt")
    except Exception:
        pass

    style.configure(
        "Custom.TButton",
        foreground=FG_COLOR,
        background=BG_COLOR,
        font=FONT_STYLE,
        relief="flat",
        borderwidth=0,
        padding=10
    )
    style.map("Custom.TButton", background=[("active", BG_COLOR)])

    # Bring window to front on macOS
    root.after(200, lambda: (
        NSApp.activateIgnoringOtherApps_(True),
        [w.makeKeyAndOrderFront_(None) for w in NSApp.windows()]
    ))

    def play_random_audio(folder: Path, label="", blocking=True):
        if folder is None:
            return
        try:
            options = []
            for ext in ('*.mp3', '*.wav', '*.aif', '*.aiff'):
                options.extend(folder.glob(ext))
            if not options:
                log_event(f"No audio in {folder}")
                return
            selected = random.choice(options)
            log_event(f"Playing audio: {selected.name} for {label}")

            if not pygame.mixer.get_init():
                pygame.mixer.pre_init()
                pygame.mixer.init()
            pygame.mixer.music.load(str(selected))
            pygame.mixer.music.play()

            if blocking:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
        except Exception as e:
            log_event(f"Audio error: {e}")

    def capture_photo(filename: Path):
        try:
            subprocess.run(
                ["/usr/local/bin/gphoto2", "--capture-image-and-download", "--filename", str(filename)],
                check=True
            )
            log_event(f"Captured photo: {filename.name}")
        except subprocess.CalledProcessError as e:
            log_event(f"ERROR: Could not capture photo. {e}")
            status.set("Capture failed")

    def ensure_readable(path: Path):
        try:
            os.chmod(path, 0o644)  # rw-r--r--
        except Exception as e:
            log_event(f"⚠️ Failed to set permissions for {path}: {e}")

    def assemble_strip(images: List[Path], output_path: Path):
        strip_width = CROP_WIDTH + 2 * BORDER_SIDE
        strip_height = (CROP_HEIGHT * len(images)) + GAP_BETWEEN * (len(images) - 1) + BORDER_TOP_BOTTOM
        strip = Image.new("RGB", (strip_width, strip_height), "white")
        y = BORDER_TOP_BOTTOM
        for idx, img_path in enumerate(images):
            img = Image.open(img_path)
            strip.paste(img, (BORDER_SIDE, y))
            y += CROP_HEIGHT + (GAP_BETWEEN if idx < len(images) - 1 else 0)
        strip.save(output_path, dpi=(72, 72))
        subprocess.run(["xattr", "-d", "com.apple.quarantine", str(output_path)], check=False)
        os.chmod(output_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        log_event(f"Assembled strip: {output_path.name}")

    def show_preview(image_path: Path, is_strip=False):
        img = Image.open(image_path)
        scale = STRIP_PREVIEW_SCALE if is_strip else PREVIEW_SCALE
        img = img.resize((int(img.width * scale), int(img.height * scale)))
        img = ImageOps.expand(img, border=6, fill=ImageColor.getrgb("white"))
        preview_img = ImageTk.PhotoImage(img)
        preview_label.config(image=preview_img)
        preview_label.image = preview_img

    def session_logic():
        try:
            session_state['active'] = True
            session_state['completed'] = False
            log_event("-" * 60)
            log_event("Session started")

            play_random_audio(WAKE_DIR, label="wake", blocking=True)

            now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            originals = []
            cropped = []

            for i in range(4):
                status.set(f"Capturing photo {i+1}/4")
                audio_folder = AUDIO_DIR / f"Photo{i+1}"
                play_random_audio(audio_folder, label=f"photo {i+1}", blocking=True)

                fname = ORIGINALS_DIR / f"{now}_{i+1}.jpg"
                capture_photo(fname)
                if not fname.exists():
                    log_event("ERROR: File not created, skipping photo")
                    continue

                originals.append(fname)

                img = Image.open(fname).rotate(-90, expand=True)
                cropped_img = crop_off_center(img)  # ← off-center crop
                cropped_path = CROPPED_DIR / f"Crop_of_{fname.name}"
                cropped_img.save(cropped_path, dpi=(72, 72))
                ensure_readable(cropped_path)
                cropped.append(cropped_path)
                log_event(f"Cropped image saved: {cropped_path.name}")

                show_preview(cropped_path)

            if not cropped:
                status.set("No photos captured")
                log_event("No photos captured. Skipping strip assembly.")
                return

            STRIPS_DIR.mkdir(parents=True, exist_ok=True)
            strip_path = STRIPS_DIR / f"{now}_strip.png"
            assemble_strip(cropped, strip_path)
            show_preview(strip_path, is_strip=True)
            print_strip_direct(strip_path)

            # Non-blocking process/done sounds (if present)
            threading.Thread(target=play_random_audio, args=(PROCESS_DIR,), kwargs={'label': 'process', 'blocking': False}, daemon=True).start()
            threading.Thread(target=play_random_audio, args=(DONE_DIR,),    kwargs={'label': 'done',    'blocking': False}, daemon=True).start()

            log_event("Session complete")
            session_state['completed'] = True
            status.set("Ready. Press any key to begin.")
        except Exception as e:
            log_event(f"Error: {e}")
            status.set("Error during session")
        finally:
            session_state['active'] = False

    def check_dslr_camera_available():
        try:
            result = subprocess.run(
                ["/usr/local/bin/gphoto2", "--auto-detect"],
                capture_output=True, text=True
            )
            if "Canon" not in result.stdout:
                log_event("❌ No Canon camera detected via gphoto2.")
                messagebox.showerror("Camera Error", "No Canon DSLR detected. Please connect the camera.")
                return False
            return True
        except Exception as e:
            log_event(f"❌ Camera check failed: {e}")
            messagebox.showerror("Camera Error", "Unable to check camera. Make sure gphoto2 is installed.")
            return False

    def start_session(event=None):
        if session_state['active']:
            log_event("Start ignored: session already running.")
            return
        if not check_dslr_camera_available():
            return
        if session_state['completed']:
            log_event("Restarting new session after previous complete.")
            session_state['completed'] = False
        threading.Thread(target=session_logic, daemon=True).start()

    root.bind("<Key>", start_session)

    if not DUMMY_IMAGE_PATH.exists():
        dummy = Image.new("RGB", (CROP_WIDTH, CROP_HEIGHT), ImageColor.getrgb(BG_COLOR))
        dummy = ImageOps.expand(dummy, border=6, fill=ImageColor.getrgb("white"))
        dummy.save(DUMMY_IMAGE_PATH)

    show_preview(DUMMY_IMAGE_PATH)

    print("GUI launched. Running mainloop...")
    log_event("App launched")
    root.mainloop()

if __name__ == "__main__":
    launch_powermate()  # added
    try:
        launch_gui()
    except Exception as e:
        log_event(f"Launch error: {e}")
        print(f"Launch error: {e}")