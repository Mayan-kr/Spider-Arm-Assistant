# 🕷️ Spider-Arm v2.5: Technical Features & Working

Spider-Arm is a professional, cloud-linked agentic AI assistant designed to give you total control over your PC from any Android device. This document details the underlying architecture, intelligence layers, and the specialized toolset that powers the experience.

---

## 🕸️ System Flow: The Architecture Pipeline
User writes command -> Firebase Firestore -> Python Bridge -> Qwen 2.5 Brain -> Tools -> PC.

---

## 📚 Library Ecosystem: The Engine Room

Spider-Arm relies on a curated stack of Python libraries to achieve high-performance local AI and system control:

| Library | Role | Why we use it |
| :--- | :--- | :--- |
| **Unsloth** | **AI Acceleration** | Provides 2x faster 4-bit LoRA fine-tuning and inference for Qwen models on consumer GPUs. |
| **Firebase Admin** | **Cloud Sync** | Handles the persistent snapshot connection between the phone and PC. |
| **PyAutoGUI** | **System Interaction**| Orchestrates real-time typing, screenshot capture, and media key simulation. |
| **PyGetWindow** | **Focus Management** | Ensures media commands actually reach the target app (e.g., Spotify) by bringing it to focus. |
| **GPUtil / WMI** | **Hardware Pulse** | Directly interfaces with NVIDIA drivers and Windows thermal zones for heat monitoring. |
| **Psutil** | **Process Control** | Monitors CPU/RAM load and executes the 'Force Close' logic for apps. |

---

## 🏗️ How it Works: The Agentic Loop
The system operates as a **Real-Time Synchronized Loop** across three primary layers:

1.  **Control Layer (Mobile Dashboard)**:
    - User authenticates via **Google One-Tap Sign-In**.
    - User sends a natural language command (e.g., *"Resume my Spotify music"*).
    - The dashboard writes this command to a **Firebase Firestore** collection with a `pending` status.

2.  **Sync Layer (The Cloud Bridge)**:
    - The local PC runs `backend/firebase_bridge.py`, which maintains an active **Snapshot Listener** on the cloud.
    - As soon as a command is detected, the bridge pulls it, and marks it as `processing`.

3.  **Intelligence Layer (Qwen 2.5 + Tools)**:
    - The command is fed into the **Fine-Tuned Qwen 2.5 1.5B** model (running locally on your NVIDIA GPU via Unsloth).
    - The model "thinks" (Chain of Thought) and generates a structured **JSON Tool Call**.
    - The bridge executes the corresponding Python function in `controller/tools.py`.
    - The result is sent back to the cloud, appearing on your phone instantly.

---

## 🧠 Intelligence & Reliability

### 1. Fine-Tuned Brain (LoRA)
Spider-Arm uses a **4-bit Quantized LoRA** of Qwen 2.5 1.5B Instruct. It has been specifically trained on thousands of "PC Control" scenarios to understand the nuance of system commands versus general chat.

### 2. Smart JSON Repair Layer
To combat the "jittery" output potential of smaller AI models (1.5B parameters), we implemented a **Robust Parser** in `inference.py`. If the model makes a syntax mistake (like forgetting a quote or a key), the bridge automatically "repairs" the JSON string before it crashes.

### 3. Search-First App Launcher
Unlike simple launchers, Spider-Arm's `launch_app` tool:
- Resolves **Aliases** (e.g., "browser" -> "Brave").
- Scans **Brave/Chrome Web App Shortcuts** first (to support sites like YouTube/Spotify installed as apps).
- Defaults to system binaries only if no shortcut is found.

---

## 🛡️ Security Architecture: The Private Fort

Spider-Arm is built with a **Zero-Trust** philosophy:
-   **Google Authentication**: Only authorized Google accounts can even view the dashboard.
-   **Identity Lockdown**: Firestore Security Rules ensure that only your specific email has "Write" permissions. Anyone else with the link is blocked by the cloud itself.
-   **Approval Loop**: Destructive actions (like `delete_file`) use the `@requires_confirmation` decorator. The AI cannot actually delete anything until you click "Approve" on your phone.
-   **Spider-Pulse (Heartbeat)**: The system sends a heartbeat every 30 seconds. Your phone reflects this live status, so you know exactly when your "Private Fort" is active.

---

## 🛠️ Engineering Challenges & Solutions

During the development of Spider-Arm, we encountered several platform-specific hurdles. Below is the log of how we solved them:

### 1. The "Jittery" Model (JSON Syntax Errors)
- **Problem**: Lower-parameter models (1.5B) occasionally produce minor syntax typos in their JSON output (missing quotes or keys), which originally crashed the parser.
- **Solution**: Implemented a **Smart JSON Repair** layer. We use regex to "auto-correct" missing parameter keys and balance braces before passing the string to the JSON loader.

### 2. Windows File Locking (`os error 1224`)
- **Problem**: During training, Windows would lock model files, preventing the AI from saving intermediate checkpoints.
- **Solution**: Updated `train.py` to use `save_strategy="no"`. This keeps the entire training process in VRAM and only saves the final high-quality LoRA adapter.

### 3. Media Focus Deadlocks
- **Problem**: Media commands (like Skip/Pause) would fail if the music player was minimized or not the "active" window.
- **Solution**: Integrated **Focus-Aware Controls**. The tool now uses fuzzy search to find the player's window title, restores it from the taskbar, and activates it before "pressing" the media keys.

### 4. Public URL Security
- **Problem**: Anyone with the `web.app` link could theoretically control the user's PC.
- **Solution**: Architecture-level security. We added **Google One-Tap Auth** and restrictive **Firestore Rules** that block any write requests unless the user's verified Gmail matches the project owner's identity.

---

## 🔧 Core Tool Reference

| Tool | Purpose | Internal Working |
| :--- | :--- | :--- |
| `get_system_info` | **Hardware Pulse** | Uses `psutil` & `GPUtil` to read CPU load, RAM, and NVIDIA GPU temperature. |
| `control_media` | **Universal Media** | Uses `pygetwindow` to find your player (Spotify/Chrome), brings it to focus, and simulates media keys. |
| `screenshot` | **Remote View** | Captures the primary display and saves it to the `outputs/` folder for review. |
| `launch_app` | **App Control** | Priority-based search across Start Menu, Shortcuts, and ENV paths. |
| `type_text` | **Remote Input** | Simulates human-like keyboard typing at a steady interval. |
| `terminate_process`| **App Killer** | Scans active processes and force-closes matching windows. |

---

## 🧙‍♂️ Zero-Touch Setup (v3.0 Logic)
To make deployment seamless, the `setup_wizard.py` automates:
1.  **Cloud Architecting**: Uses Firebase CLI to auto-create projects and register apps.
2.  **Unified Vault**: Harvests all API keys and admin secrets into a single `credentials.json`.
3.  **Auto-Rules**: Pushes the specialized `firestore.rules` to the cloud instantly.
4.  **Brain Activation**: Automatically runs the `train.py` script to bake the local AI model.

---
*Spider-Arm v2.5 - Built for Performance, Security, and Style.*
