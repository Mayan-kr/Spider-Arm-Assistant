# 🕷️ Spider-Arm v2.5 — Agent Capabilities Reference

> **Complete reference for all 18 tools the agent can execute.**
> Includes command examples, parameter details, and security threat levels.

---

## 🔐 Threat Level Legend

| Badge | Level | Meaning |
|---|---|---|
| 🟢 **SAFE** | No risk | Read-only or fully reversible. Executes immediately. |
| 🟡 **LOW** | Minor risk | Changes state but easily undone. Executes immediately. |
| 🟠 **MEDIUM** | Moderate risk | Can disrupt workflow or lose context. Requires care. |
| 🔴 **HIGH** | High risk | Can cause **data loss** or **system disruption**. Requires your explicit phone approval before executing. |

---

## 📋 Tool Index

| # | Tool | Category | Threat Level | Needs Approval? |
|---|---|---|---|---|
| 1 | `screenshot` | Capture | 🟢 SAFE | ❌ |
| 2 | `launch_app` | Control | 🟢 SAFE | ❌ |
| 3 | `get_system_info` | Monitoring | 🟢 SAFE | ❌ |
| 4 | `get_battery` | Monitoring | 🟢 SAFE | ❌ |
| 5 | `control_media` | Media | 🟢 SAFE | ❌ |
| 6 | `type_text` | Input | 🟡 LOW | ❌ |
| 7 | `press_key` | Input | 🟡 LOW | ❌ |
| 8 | `submit_text` | Input | 🟡 LOW | ❌ |
| 9 | `open_url` | Browser | 🟡 LOW | ❌ |
| 10 | `set_volume` | System | 🟡 LOW | ❌ |
| 11 | `lock_screen` | Security | 🟡 LOW | ❌ |
| 12 | `hotkey` (safe combos) | Input | 🟡 LOW | ❌ |
| 13 | `hotkey` (destructive combos) | Input | 🟠 MEDIUM | ✅ **Yes** |
| 14 | `sleep_pc` | Power | 🟠 MEDIUM | ✅ **Yes** |
| 15 | `create_folder` | File System | 🟠 MEDIUM | ✅ **Yes** |
| 16 | `create_file` | File System | 🔴 HIGH | ✅ **Yes** |
| 17 | `terminate_process` | Process | 🔴 HIGH | ✅ **Yes** |
| 18 | `delete_file` | File System | 🔴 HIGH | ✅ **Yes** |

---

## 🔍 Detailed Tool Descriptions

---

### 1. `screenshot()`
**Category:** Capture | **Threat:** 🟢 SAFE

Captures the entire primary display and saves it as a PNG file inside the `outputs/` folder.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters needed |

**Example commands:**
- *"Take a screenshot"*
- *"Capture the screen"*
- *"Show me what's on my PC right now"*

**Output:** `outputs/screenshot.png`

**Use cases:**
- Checking what's currently on your PC screen from your phone
- Documenting the screen state remotely
- Debugging what a running application is showing

**Threat notes:** Completely read-only. Does not modify any files or system state. The output PNG is simply overwritten each call.

---

### 2. `launch_app(name)`
**Category:** Control | **Threat:** 🟢 SAFE

Opens any installed application, shortcut, or web app on the PC. Searches Desktop, Start Menu, and Brave App shortcuts before falling back to system commands.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | App name or alias (e.g. `"spotify"`, `"calculator"`, `"browser"`) |

**Built-in aliases:**
| You say | Opens |
|---|---|
| `browser` | Brave Browser |
| `calculator` / `calc` | Windows Calculator |
| `terminal` | Windows Terminal |
| `editor` | Notepad |
| `settings` | Windows Settings |
| `task manager` | Task Manager |

**Example commands:**
- *"Open Spotify"*
- *"Launch the calculator"*
- *"Open the browser"*
- *"Start Notepad"*

**Threat notes:** Launches apps with your user permissions. Cannot open apps that require elevation (admin). Does not modify files.

---

### 3. `get_system_info(metric)`
**Category:** Monitoring | **Threat:** 🟢 SAFE

Fetches real-time hardware and performance statistics from the PC.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `metric` | string | ✅ | One of: `"cpu"`, `"mem"`, `"disk"`, `"temp"`, `"all"` |

**Available metrics:**
| metric | Returns |
|---|---|
| `cpu` | CPU usage percentage |
| `mem` | RAM usage percentage |
| `disk` | Disk usage percentage |
| `temp` | GPU temperature (NVIDIA) + CPU temperature |
| `all` | All of the above |

**Example commands:**
- *"Check CPU usage"*
- *"Is my PC running hot?"*
- *"What's my RAM at?"*
- *"Give me a full system health check"*

**Threat notes:** Completely read-only. Only reads public hardware telemetry, no personal data.

---

### 4. `get_battery()`
**Category:** Monitoring | **Threat:** 🟢 SAFE

Returns the laptop's battery percentage, charging status, and estimated time remaining.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters needed |

**Example commands:**
- *"Check the battery"*
- *"How much battery is left?"*
- *"Is my laptop charging?"*
- *"Battery status"*

**Output example:** `78%, Charging, N/A time remaining`

**Threat notes:** Read-only. Returns `No battery detected` on desktop PCs.

---

### 5. `control_media(action, app_hint)`
**Category:** Media | **Threat:** 🟢 SAFE

Controls music and video playback using system media keys. Works with Spotify, YouTube, Chrome, and any app that responds to media keys.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `action` | string | ✅ | See action table below |
| `app_hint` | string | ❌ | App name to focus before sending key (e.g. `"spotify"`) |

**Available actions:**
| Action | What it does |
|---|---|
| `play_pause` | Toggles play/pause |
| `next` | Skips to next track |
| `previous` | Goes to previous track |
| `volume_up` | Increases volume (5 presses ≈ 10%) |
| `volume_down` | Decreases volume (5 presses ≈ 10%) |
| `mute` | Toggles mute |

**Supported aliases:** `play`, `pause`, `resume`, `skip`, `change`, `change_song`, `back`

**Example commands:**
- *"Play the music"*
- *"Next song"*
- *"Change the song"* / *"Skip this"*
- *"Previous track"*
- *"Volume up"* / *"Volume down"*
- *"Mute everything"*

**Threat notes:** Only sends virtual media keys. Cannot read or modify any files.

---

### 6. `type_text(text)`
**Category:** Input | **Threat:** 🟡 LOW

Simulates keyboard typing in the currently active window, character by character. Does **not** press Enter at the end.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `text` | string | ✅ | The text to type |

**Example commands:**
- *"Type Hello World"*
- *"Type my name is Spider-Arm"*
- *"Write spider in the search box"*

**Threat notes:** Types into whatever window is currently focused. If a wrong window is active (e.g. a terminal or Run dialog), text could be typed there unintentionally. Always ensure the correct window is focused first.

---

### 7. `press_key(key)`
**Category:** Input | **Threat:** 🟡 LOW

Presses a single keyboard key in the active window.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `key` | string | ✅ | Key name: `"enter"`, `"esc"`, `"space"`, `"tab"`, `"backspace"`, `"delete"`, `"f1"`–`"f12"`, arrow keys |

**Example commands:**
- *"Press enter"* / *"Hit enter"*
- *"Press escape"*
- *"Press the space bar"*
- *"Press tab"*

**Threat notes:** Context-dependent. Pressing Enter in a form submits it; pressing Delete removes selected content. The risk depends entirely on what's currently focused.

---

### 8. `submit_text(text)`
**Category:** Input | **Threat:** 🟡 LOW

Combines `type_text` + `press_key(enter)` in a single atomic action. Types the text and immediately submits it (presses Enter). Designed for search boxes, chat inputs, and terminal commands.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `text` | string | ✅ | The text to type and submit |

**Example commands:**
- *"Type turtle and press enter"*
- *"Search for lo-fi music"*
- *"Type spider arm and submit"*

**Threat notes:** Higher than `type_text` alone because it also submits the input. If a terminal is focused, this could execute a shell command. Use `type_text` first and verify focus before submitting.

---

### 9. `open_url(url)`
**Category:** Browser | **Threat:** 🟡 LOW

Opens a URL in the system's default browser. Automatically prepends `https://` if the protocol is missing.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `url` | string | ✅ | URL to open (e.g. `"youtube.com"`, `"https://github.com"`) |

**Example commands:**
- *"Open youtube.com"*
- *"Go to google.com"*
- *"Navigate to reddit.com"*
- *"Open my GitHub"*

**Threat notes:** Low risk — only opens a URL. The risk is that a malicious command could navigate to a phishing or malicious site. Since commands come only from your authenticated phone dashboard, this is not a practical concern.

---

### 10. `set_volume(level)`
**Category:** System | **Threat:** 🟡 LOW

Sets the Windows system master volume to an exact percentage (0–100). Uses the Windows Audio Session API (`pycaw`).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `level` | integer | ✅ | Volume percentage from `0` (silent) to `100` (maximum) |

**Example commands:**
- *"Set volume to 40"*
- *"Volume at 70 percent"*
- *"Max out the volume"*
- *"Lower volume to 20"*
- *"Mute the PC"* → `set_volume(0)`

**Threat notes:** Fully reversible. Only affects system audio output level.

---

### 11. `lock_screen()`
**Category:** Security | **Threat:** 🟡 LOW

Immediately locks the Windows workstation using the Windows API (`LockWorkStation`). Equivalent to pressing `Win + L`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters needed |

**Example commands:**
- *"Lock my PC"*
- *"Lock the screen"*
- *"I'm stepping away, lock the computer"*

**Threat notes:** Fully reversible — just enter your Windows PIN or password to unlock. Does not close apps or lose data. Useful as a quick security action when leaving your desk.

---

### 12 & 13. `hotkey(keys)`
**Category:** Input | **Threat:** 🟡 LOW (safe) / 🟠 MEDIUM (destructive)

Presses a keyboard shortcut (key combination). Safe shortcuts execute instantly; **destructive shortcuts are automatically intercepted** and sent to your phone for approval.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keys` | string | ✅ | `+`-separated key combo (e.g. `"ctrl+c"`, `"alt+tab"`) |

**Safe shortcuts (execute immediately 🟢):**
| Shortcut | Action |
|---|---|
| `ctrl+c` | Copy |
| `ctrl+v` | Paste |
| `ctrl+z` | Undo |
| `ctrl+a` | Select All |
| `ctrl+s` | Save |
| `alt+tab` | Switch Window |
| `win+d` | Show Desktop |

**Destructive shortcuts (require phone approval 🔴):**
| Shortcut | Action | Why blocked |
|---|---|---|
| `alt+f4` | Close active window | Can close apps with unsaved work |
| `ctrl+w` | Close active tab | Can close browser tabs/windows |
| `ctrl+alt+del` | System interrupt | System-level action |
| `ctrl+shift+esc` | Open Task Manager | Can be used to kill processes |
| `win+l` | Lock workstation | Handled by `lock_screen` tool instead |

**Example commands:**
- *"Copy that"* → `ctrl+c`
- *"Paste"* → `ctrl+v`
- *"Undo"* → `ctrl+z`
- *"Switch window"* / *"Alt tab"* → `alt+tab`
- *"Show desktop"* → `win+d`
- *"Close this window"* → `alt+f4` *(approval required)*

---

### 14. `sleep_pc()`
**Category:** Power | **Threat:** 🟠 MEDIUM | **⚠️ Requires Approval**

Puts the Windows PC into sleep/suspend mode using `powrprof.dll`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| — | — | — | No parameters needed |

**Example commands:**
- *"Put the PC to sleep"*
- *"Sleep"*
- *"Suspend the computer"*

**Threat notes:**
> ⚠️ **The Firebase bridge will disconnect when the PC sleeps.** You will need to wake the PC manually and restart the bridge. Requires explicit approval on your phone before executing.

---

### 15. `create_folder(name)`
**Category:** File System | **Threat:** 🟠 MEDIUM | **⚠️ Requires Approval**

Creates a new folder. If a plain name is given (no path), the folder is created on the Desktop.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | Folder name or absolute path |

**Example commands:**
- *"Create a folder called Projects"*
- *"Make a new folder named Work on my Desktop"*

**Threat notes:** Creating a folder is largely harmless, but since it modifies the file system, it is protected by the approval flow. Using an absolute path allows folder creation anywhere on the system.

---

### 16. `create_file(name, content, append)`
**Category:** File System | **Threat:** 🔴 HIGH | **⚠️ Requires Approval**

Creates a new file or overwrites an existing one. If `append=True`, adds content to the end of the file instead of overwriting. Files are saved to the Desktop by default unless an absolute path is given.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | Filename or absolute path (e.g. `"todo.txt"`) |
| `content` | string | ✅ | Text to write into the file |
| `append` | boolean | ✅ | `false` = overwrite, `true` = append to end |

**Example commands:**
- *"Create a note called todo.txt saying Buy milk"*
- *"Add Remember the dentist appointment to notes.txt"*
- *"Write Done for today to work.txt"*

**Threat notes:**
> ⚠️ **Overwrite mode (`append=false`) silently replaces the file's entire contents.** If the file already exists, its previous content is permanently lost. Always confirm before approving this action for existing files.

---

### 17. `terminate_process(name)`
**Category:** Process Management | **Threat:** 🔴 HIGH | **⚠️ Requires Approval**

Force-terminates all running processes whose name contains the given string. Equivalent to "End Task" in Task Manager.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | Process name (e.g. `"chrome"`, `"notepad"`, `"python"`) |

**Example commands:**
- *"Close all Chrome windows"*
- *"Kill Notepad"*
- *"Stop all Python processes"*
- *"Terminate Discord"*

**Threat notes:**
> ⚠️ **Force-killing a process bypasses the app's normal close flow.** Any unsaved work in that application (e.g., open Chrome tabs, unsaved documents, unfinished downloads) will be **permanently lost**. Requires explicit phone approval before executing.

---

### 18. `delete_file(path)`
**Category:** File System | **Threat:** 🔴 HIGH | **⚠️ Requires Approval**

Permanently deletes a file from the file system. The file is **not moved to Recycle Bin** — it is immediately removed.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | string | ✅ | Absolute path to the file to delete |

**Example commands:**
- *"Delete the file test.txt from C:\temp"*
- *"Remove the old log file"*

**Threat notes:**
> ⚠️ **This action is IRREVERSIBLE.** The file is permanently deleted, not moved to the Recycle Bin. There is no undo. Always double-check the path shown in the approval card on your phone before confirming.

---

## 🔒 The Approval Flow (How High-Risk Tools Work)

When you send a command that maps to a 🔴 HIGH or 🟠 MEDIUM tool, here's what happens:

```
1. You send: "Close Chrome"
         │
         ▼
2. Agent identifies: terminate_process("chrome")
         │
         ▼
3. Bridge sends approval request to your phone dashboard
   Showing: "⚠️ Approval required for terminate_process"
   With action ID (e.g. act_3)
         │
         ├── You TAP APPROVE on your phone
         │        │
         │        ▼
         │   Agent calls confirm_action("act_3")
         │   → Process is terminated ✅
         │
         └── You TAP DENY / ignore
                  │
                  ▼
             Action is cancelled ❌
             No changes made
```

The `confirm_action(action_id)` tool is the internal mechanism that executes the held action after you approve it on the dashboard.

---

## 📊 Risk Summary by Category

```
MONITORING (Read-only)    screenshot, get_system_info, get_battery
  Risk: 🟢 None — no system state is changed

MEDIA & AUDIO             control_media, set_volume
  Risk: 🟢–🟡 Fully reversible

INPUT SIMULATION          type_text, submit_text, press_key, hotkey(safe)
  Risk: 🟡 Context-dependent — depends on active window

BROWSER & APPS            open_url, launch_app
  Risk: 🟡 Low — opens things, doesn't modify anything

WINDOW MANAGEMENT         lock_screen, hotkey(destructive)
  Risk: 🟡–🟠 Reversible but disruptive

POWER                     sleep_pc
  Risk: 🟠 Medium — disconnects bridge, requires manual wake

FILE SYSTEM               create_file, create_folder, delete_file
  Risk: 🔴 High — modifies or permanently removes files

PROCESS CONTROL           terminate_process
  Risk: 🔴 High — can cause unsaved data loss
```

---

*Spider-Arm v2.5 — Local AI · Private by Design · Approval-gated for safety*
