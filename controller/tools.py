import os
import sys
import pyautogui
import psutil
import platform
import subprocess
import glob
import shutil
import time
import ctypes
import webbrowser
from functools import wraps


# Common Windows App Aliases — also used as website shortcuts
APP_ALIASES = {
    "calculator": "calc",
    "calc": "calc",
    "notepad": "notepad",
    "editor": "notepad",
    "chrome": "chrome",
    "browser": "brave",
    "brave": "brave",
    "settings": "ms-settings:",
    "terminal": "wt",
    "command prompt": "cmd",
    "task manager": "taskmgr"
}

# Website shortcuts: bare word -> full URL (used by launch_app URL detection)
SITE_SHORTCUTS = {
    "linkedin": "linkedin.com",
    "youtube": "youtube.com",
    "github": "github.com",
    "google": "google.com",
    "twitter": "twitter.com",
    "x": "x.com",
    "instagram": "instagram.com",
    "reddit": "reddit.com",
    "facebook": "facebook.com",
    "netflix": "netflix.com",
    "gmail": "mail.google.com",
    "whatsapp": "web.whatsapp.com",
}

# Common domain TLDs — if name ends with one, treat as URL
_URL_TLDS = ('.com', '.net', '.org', '.io', '.co', '.to', '.app', '.dev',
             '.ai', '.in', '.uk', '.us', '.tv', '.me', '.gg')

# Optional hardware/window libraries
try:
    import GPUtil
except ImportError:
    GPUtil = None
try:
    import wmi
except ImportError:
    wmi = None
try:
    import pygetwindow as gw
except ImportError:
    gw = None

# State for the confirmation logic
pending_actions = {}

def _get_common_dirs():
    """Returns a list of common user directories for file searching."""
    user_profile = os.environ.get("USERPROFILE", "")
    return [
        os.path.join(user_profile, "Desktop"),
        os.path.join(user_profile, "Documents"),
        os.path.join(user_profile, "Downloads"),
    ]

def requires_confirmation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # We generate a unique ID for this pending action
        action_id = f"act_{len(pending_actions) + 1}"
        entry = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "status": "pending_approval",
            "action_name": func.__name__
        }
        pending_actions[action_id] = entry
        
        # In a real environment with Firebase, we would write this to a 'requests' collection
        # For now, we print it so the bridge/agent knows it needs approval.
        print(f"[SAFETY] Action '{func.__name__}' blocked. Waiting for approval of ID: {action_id}")
        
        return {
            "status": "request_confirmation", 
            "action_id": action_id, 
            "message": f"Security: Approval required for {func.__name__}"
        }
    return wrapper

def screenshot():
    os.makedirs("outputs", exist_ok=True)
    path = "outputs/screenshot.png"
    pyautogui.screenshot(path)
    return {"status": "success", "message": f"Screenshot saved to {path}"}

def launch_app(name):
    try:
        if platform.system() == "Windows":
            name_lower = name.lower().strip()

            # 0. Website shortcut lookup (bare words like 'linkedin', 'youtube')
            if name_lower in SITE_SHORTCUTS:
                url = 'https://' + SITE_SHORTCUTS[name_lower]
                webbrowser.open(url)
                return {"status": "success", "message": f"Opened: {url}"}

            # 1. Domain name detection — anything ending with a known TLD is a URL
            if name_lower.endswith(_URL_TLDS) or name_lower.startswith(('http://', 'https://')):
                url = name if name_lower.startswith(('http://', 'https://')) else 'https://' + name
                webbrowser.open(url)
                return {"status": "success", "message": f"Opened: {url}"}

            # 2. File detection: if name has a known file extension, open it directly
            file_exts = ('.txt', '.pdf', '.docx', '.xlsx', '.pptx', '.csv',
                         '.jpg', '.jpeg', '.png', '.mp4', '.mp3', '.html',
                         '.json', '.py', '.md', '.log')
            if name_lower.endswith(file_exts):
                search_dirs = _get_common_dirs()
                for d in search_dirs:
                    candidate = os.path.join(d, name)
                    if os.path.exists(candidate):
                        os.startfile(candidate)
                        return {"status": "success", "message": f"Opened file: {candidate}"}
                if os.path.exists(name):
                    os.startfile(name)
                    return {"status": "success", "message": f"Opened file: {name}"}
                return {"status": "error", "message": f"File '{name}' not found on Desktop, Documents, or Downloads."}

            # 3. App alias resolution
            target = APP_ALIASES.get(name_lower, name)

            # 4. Search for Shortcuts (.lnk files)
            search_paths = [
                os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Brave Apps"),
                os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Chrome Apps"),
                os.path.join(os.environ["USERPROFILE"], "Desktop"),
                os.path.join(os.environ["USERPROFILE"], "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs")
            ]
            for path in search_paths:
                if os.path.exists(path):
                    pattern = os.path.join(path, f"*{target}*.lnk")
                    matches = glob.glob(pattern)
                    if matches:
                        os.startfile(matches[0])
                        return {"status": "success", "message": f"Launched shortcut: {os.path.basename(matches[0])}"}

            # 5. System commands (calc, notepad, etc.)
            if shutil.which(target) or target.startswith("ms-settings:"):
                subprocess.Popen(["start", target], shell=True)
                return {"status": "success", "message": f"Launched system app: {target}"}

            return {"status": "error", "message": f"Could not find app or shortcut for '{name}'"}

        # Fallback for non-Windows
        subprocess.Popen([name])
        return {"status": "success", "message": f"Launched {name}"}

    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

def get_system_info(metric="all"):
    try:
        info = {}
        if metric in ["cpu", "all"]:
            info["cpu_usage"] = f"{psutil.cpu_percent(interval=0.5)}%"
        if metric in ["mem", "all"]:
            info["memory_usage"] = f"{psutil.virtual_memory().percent}%"
        if metric in ["disk", "all"]:
            info["disk_usage"] = f"{psutil.disk_usage('/').percent}%"

        # Battery (always included in 'all' — shows N/A on desktops)
        if metric in ["battery", "all"]:
            bat = psutil.sensors_battery()
            if bat:
                info["battery"] = f"{bat.percent:.0f}% ({'Charging' if bat.power_plugged else 'Discharging'})"
            else:
                info["battery"] = "N/A (desktop)"

        # Safe Temp/Heat/GPU checks
        if metric in ["temp", "heat", "gpu", "all"]:
            # GPU temperature + usage (NVIDIA via GPUtil)
            if GPUtil:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        info["gpu_temp"] = f"{gpus[0].temperature}°C"
                        info["gpu_usage"] = f"{gpus[0].load * 100:.1f}%"
                except: pass
            # CPU temperature via WMI
            if wmi:
                try:
                    w = wmi.WMI(namespace="root\\wmi")
                    temps = w.MSAcpi_ThermalZoneTemperature()
                    if temps:
                        celsius = (temps[0].CurrentTemperature / 10.0) - 273.15
                        info["cpu_temp"] = f"{round(celsius, 1)}°C"
                except: pass

        return {"status": "success", "data": info}
    except Exception as e:
        return {"status": "error", "message": f"Telemetry failed: {str(e)}"}

def control_media(action, app_hint=None):
    try:
        # 1. Provide Focus (Crucial for suspended/minimized apps)
        focus_msg = ""
        if gw and app_hint:
            try:
                # Fuzzy search across all windows
                target_win = None
                all_wins = gw.getAllWindows()
                for w in all_wins:
                    if app_hint.lower() in w.title.lower():
                        target_win = w
                        break
                
                if target_win:
                    if target_win.isMinimized:
                        target_win.restore()
                        time.sleep(0.5) # Wait for "Repaint/Wake up"
                    
                    target_win.activate()
                    time.sleep(0.2)
                    focus_msg = f"Resurrected '{target_win.title}'. "
            except Exception as fe:
                focus_msg = f"(Wake-up failed: {str(fe)}) "

        # 2. Key Mapping (Standardize Resume to PlayPause)
        mapping = {
            "play": "playpause",
            "play_song": "playpause",
            "play_music": "playpause",
            "pause": "playpause",
            "resume": "playpause",
            "play_pause": "playpause",
            "next": "nexttrack",
            "next_song": "nexttrack",
            "change": "nexttrack",
            "change_song": "nexttrack",
            "skip": "nexttrack",
            "skip_song": "nexttrack",
            "previous": "prevtrack",
            "back": "prevtrack",
            "volume_up": "volumeup",
            "volume_down": "volumedown",
            "mute": "volumemute"
        }
        
        key = mapping.get(action.lower())
        if key:
            if "volume" in key:
                # Boost volume steps: 5 presses = ~10% change for snappier control
                for _ in range(5):
                    pyautogui.press(key)
            else:
                pyautogui.press(key)
            return {"status": "success", "message": f"{focus_msg}Media action: {action}"}
        else:
            return {"status": "error", "message": f"Unknown media action: {action}"}
    except Exception as e:
        return {"status": "error", "message": f"Media control failed: {str(e)}"}

def type_text(text):
    pyautogui.write(text, interval=0.1)
    return {"status": "success", "message": f"Typed: {text}"}

def press_key(key):
    pyautogui.press(key)
    return {"status": "success", "message": f"Pressed key: {key}"}

def submit_text(text):
    """Types text and immediately presses Enter — for search boxes, chat inputs, etc."""
    pyautogui.write(text, interval=0.1)
    time.sleep(0.1)  # Brief pause so the keystroke registers before Enter
    pyautogui.press("enter")
    return {"status": "success", "message": f"Typed and submitted: {text}"}

# Hotkey combos that are destructive and require explicit approval before executing
_DESTRUCTIVE_HOTKEYS = {
    frozenset(["alt", "f4"]),           # Close active window
    frozenset(["ctrl", "w"]),            # Close active tab/window
    frozenset(["ctrl", "alt", "del"]),   # System interrupt
    frozenset(["ctrl", "shift", "esc"]), # Task Manager (can kill processes)
    frozenset(["win", "l"]),             # Lock screen (handled by lock_screen tool, avoid double-trigger)
    frozenset(["alt", "f4"]),            # Close window
    frozenset(["ctrl", "alt", "delete"]),
}

def hotkey(keys):
    """Press a keyboard shortcut. keys: '+'-separated, e.g. 'ctrl+c', 'alt+tab', 'win+d'.
    Destructive combos (alt+f4, ctrl+w, ctrl+alt+del, win+l) require phone approval first.
    """
    try:
        normalized = keys.lower().strip().replace(' ', '+')
        key_list = [k.strip() for k in normalized.split('+') if k.strip()]
        # Common word aliases to pyautogui key names
        key_map = {
            'control': 'ctrl',
            'windows': 'win',
            'escape': 'esc',
            'delete': 'del',
            'return': 'enter',
        }
        key_list = [key_map.get(k, k) for k in key_list]

        # Block destructive hotkey combos — route through approval flow
        key_set = frozenset(key_list)
        if key_set in _DESTRUCTIVE_HOTKEYS:
            return _hotkey_confirmed(keys, key_list)

        pyautogui.hotkey(*key_list)
        return {"status": "success", "message": f"Hotkey: {'+'.join(key_list)}"}
    except Exception as e:
        return {"status": "error", "message": f"Hotkey failed: {str(e)}"}

@requires_confirmation
def _hotkey_confirmed(original_keys, key_list):
    """Executes a destructive hotkey after explicit user approval."""
    pyautogui.hotkey(*key_list)
    return {"status": "success", "message": f"Destructive hotkey executed: {original_keys}"}

def open_url(url):
    """Open a URL in the default browser. Adds https:// automatically if missing."""
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    webbrowser.open(url)
    return {"status": "success", "message": f"Opened: {url}"}

def set_volume(level):
    """Set system master volume to an exact percentage (0-100).
    Runs pycaw in a subprocess so a COM crash cannot kill the bridge.
    """
    try:
        level = max(0, min(100, int(level)))
        # Run the COM call in a child process — COM access violations are C-level
        # crashes that bypass Python's try/except and would kill the bridge otherwise.
        script = (
            "from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume;"
            "from ctypes import cast, POINTER;"
            "from comtypes import CLSCTX_ALL;"
            f"s=AudioUtilities.GetSpeakers();"
            f"d=getattr(s,'_dev',s);"
            f"i=d.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None);"
            f"v=cast(i,POINTER(IAudioEndpointVolume));"
            f"v.SetMasterVolumeLevelScalar({level/100.0:.4f},None)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, timeout=6
        )
        if result.returncode == 0:
            return {"status": "success", "message": f"Volume set to {level}%"}
        err = result.stderr.decode("utf-8", errors="ignore").strip()
        return {"status": "error", "message": f"Volume control failed: {err[:200]}"}
    except BaseException as e:
        return {"status": "error", "message": f"Volume control failed: {str(e)}"}

def lock_screen():
    """Locks the Windows workstation immediately."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return {"status": "success", "message": "Screen locked"}
    except Exception as e:
        return {"status": "error", "message": f"Lock failed: {str(e)}"}

@requires_confirmation
def sleep_pc():
    """Puts the PC to sleep. WARNING: This will terminate the bridge connection."""
    subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
    return {"status": "success", "message": "PC going to sleep"}

def get_battery():
    """Returns battery percentage and charging status."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return {"status": "error", "message": "No battery detected (desktop PC)"}
        status = "Charging" if battery.power_plugged else "Discharging"
        secs = battery.secsleft
        if secs in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN) or secs < 0:
            time_left = "N/A"
        else:
            time_left = f"{secs // 3600}h {(secs % 3600) // 60}m"
        return {"status": "success", "data": {
            "percent": f"{battery.percent:.0f}%",
            "status": status,
            "time_left": time_left
        }}
    except Exception as e:
        return {"status": "error", "message": f"Battery check failed: {str(e)}"}

@requires_confirmation
def terminate_process(name):
    """Force-closes all processes matching name. Requires approval since unsaved work may be lost."""
    count = 0
    errors = 0
    for proc in psutil.process_iter(['name']):
        try:
            if name.lower() in proc.info['name'].lower():
                proc.terminate()
                count += 1
        except (psutil.AccessDenied, Exception):
            errors += 1
    
    msg = f"Terminated {count} process(es) matching {name}"
    if errors > 0:
        msg += f" ({errors} access denied)"
    return {"status": "success", "message": msg}


@requires_confirmation
def delete_file(path):
    """Delete a file or folder. Searches Desktop/Documents/Downloads if only filename given."""
    # If it's already a valid absolute path, delete directly
    if os.path.isfile(path):
        os.remove(path)
        return {"status": "success", "message": f"Deleted file: {path}"}
    if os.path.isdir(path):
        shutil.rmtree(path)
        return {"status": "success", "message": f"Deleted folder: {path}"}

    # Search common locations by filename/foldername (exact, then fuzzy prefix)
    search_dirs = _get_common_dirs()
    name = os.path.basename(path)

    # Pass 1: exact name match
    for d in search_dirs:
        candidate = os.path.join(d, name)
        if os.path.isfile(candidate):
            os.remove(candidate)
            return {"status": "success", "message": f"Deleted file: {candidate}"}
        if os.path.isdir(candidate):
            shutil.rmtree(candidate)
            return {"status": "success", "message": f"Deleted folder: {candidate}"}

    # Pass 2: fuzzy prefix glob — handles model truncating long filenames
    # e.g. model outputs "cat_dog_gif" but actual file is "cat_dog_giraffe.txt"
    stem = os.path.splitext(name)[0]  # strip extension if present
    for d in search_dirs:
        # Try both the full name and the stem (without extension) as prefix
        for pattern_base in (name, stem):
            if not pattern_base:
                continue
            matches = glob.glob(os.path.join(d, f"{pattern_base}*"))
            if matches:
                match = matches[0]
                if os.path.isfile(match):
                    os.remove(match)
                    return {"status": "success", "message": f"Deleted file: {match}"}
                if os.path.isdir(match):
                    shutil.rmtree(match)
                    return {"status": "success", "message": f"Deleted folder: {match}"}

    return {"status": "error", "message": f"Not found: '{path}' (checked Desktop, Documents, Downloads)"}

@requires_confirmation
def create_file(name, content="", append=False):
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    # If name is just a filename, put it on desktop. Otherwise treat as path.
    path = name if os.path.isabs(name) else os.path.join(desktop, name)
    
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        # If appending, add a newline first
        if append and os.path.exists(path):
            f.write("\n")
        f.write(content)
    return {"status": "success", "message": f"File {'appended' if append else 'created'} at {path}"}

@requires_confirmation
def create_folder(name):
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    path = name if os.path.isabs(name) else os.path.join(desktop, name)
    
    os.makedirs(path, exist_ok=True)
    return {"status": "success", "message": f"Folder created at {path}"}

# Helper to execute a pending action after approval
def confirm_action(action_id):
    if action_id in pending_actions:
        action = pending_actions.pop(action_id)
        return action["func"](*action["args"], **action["kwargs"])
    return {"status": "error", "message": "Invalid action ID"}
