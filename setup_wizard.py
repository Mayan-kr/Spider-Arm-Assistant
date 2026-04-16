import os
import re
import subprocess
import sys
import json
import random
import string
import webbrowser
import time

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("="*70)
    print("      🕷️  Spider-ARM: Zero-Touch 'Cloud Architect' Wizard v3.0 🕷️")
    print("="*70)
    print("This wizard will automatically build your Firebase Infrastructure.")
    print("Requirement: You must have the Firebase CLI installed.\n")

def get_input(prompt, default=None):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

def run_cmd(cmd, capture_output=True):
    """Runs a shell command and returns the output."""
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, shell=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed: {cmd}")
        print(f"Details: {e.stderr}")
        return None

def run_step(name, func):
    print(f"\n[STEP] {name}...")
    try:
        res = func()
        if res is not False:
            print(f"[SUCCESS] {name} complete.")
            return res
        return False
    except Exception as e:
        print(f"[ERROR] {name} failed: {e}")
        return False

def generate_id(prefix="spider-arm"):
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}-{suffix}"

def setup():
    clear()
    print_banner()

    # --- 1. AUTH CHECK ---
    def check_auth():
        print("Checking Firebase login status...")
        # Try to get projects to see if logged in
        out = run_cmd("firebase projects:list")
        if not out or "Error" in out:
            print("Action Required: Please log in to Firebase in your browser.")
            run_cmd("firebase login", capture_output=False)
        return True

    if not run_step("Firebase Authentication", check_auth): return

    # --- 2. PROJECT PROVISIONING ---
    project_id = generate_id()
    def create_project():
        print(f"Creating project '{project_id}'... this takes ~30 seconds.")
        run_cmd(f"firebase projects:create {project_id} --display-name 'Spider Arm Assistant'", capture_output=False)
        
        # Enable it in the current dir
        run_cmd(f"firebase use {project_id}", capture_output=False)
        return project_id

    if not run_step(f"Provisioning Cloud Project ({project_id})", create_project): return

    # --- 3. FIRESTORE ACTIVATION ---
    def enable_firestore():
        print("Initializing Firestore Database (Region: us-central)...")
        # Note: This might fail if the user already has too many databases, but for a new project it works.
        run_cmd(f"firebase firestore:databases:create (default) --location us-central", capture_output=False)
        return True

    run_step("Activating Firestore Database", enable_firestore)

    # --- 4. APP REGISTRATION ---
    def register_app():
        print("Registering the 'Spider Dashboard' Web App...")
        run_cmd(f"firebase apps:create WEB 'Spider Dashboard'", capture_output=False)
        
        # Fetch the config
        print("Harvesting SDK credentials...")
        config_out = run_cmd("firebase apps:sdkconfig WEB --json")
        if config_out:
            data = json.loads(config_out)
            return data.get("result", {}).get("sdkConfig")
        return None

    web_config = run_step("Registering Web Dashboard", register_app)
    if not web_config: 
        print("[CRITICAL] Could not harvest Web SDK Keys.")
        return

    # --- 5. UNIFIED VAULT INJECTION ---
    def save_vault():
        # First, ensure we have the Dashboard Email for rules
        email = get_input("Your Gmail (for Security Lockdown rules)")
        
        # Save to credentials.json (Root)
        vault = {
            "web_dashboard": web_config,
            "authorized_email": email,
            "service_account": None # Will fill in next step
        }
        
        # Mirror to mobile/firebase-config.js (Safe keys only)
        js_content = "export const firebaseConfig = " + json.dumps(web_config, indent=4) + ";"
        with open("mobile/firebase-config.js", "w") as f:
            f.write(js_content)
        
        return vault

    vault = run_step("Generating Unified Vault & Dashboard Config", save_vault)

    # --- 6. SERVICE ACCOUNT (THE LAST MANUAL BIT) ---
    def fetch_service_account():
        print("\n[ACTION REQUIRED]")
        print("1. Your browser will now open to the Firebase Console.")
        print("2. Click 'Generate New Private Key'.")
        print("3. Copy the ENTIRE content of that JSON file.")
        
        url = f"https://console.firebase.google.com/project/{project_id}/settings/serviceaccounts/adminsdk"
        webbrowser.open(url)
        
        print("\nPaste the JSON content from the downloaded file here:")
        print("(Press Enter on an empty line when finished, or paste it as one line)")
        
        lines = []
        while True:
            line = input()
            if line == "": break
            lines.append(line)
        
        json_str = "".join(lines)
        try:
            sa_data = json.loads(json_str)
            vault["service_account"] = sa_data
            
            # Save the final consolidated vault
            with open("credentials.json", "w") as f:
                json.dump(vault, f, indent=4)
            return True
        except:
            print("[ERROR] Invalid JSON pasted.")
            return False

    if not run_step("Linking Security Systems (Service Account)", fetch_service_account): return

    # --- 7. AUTO-DEPLOY RULES ---
    def deploy_systems():
        print("Deploying Security Rules and Hosting to the Cloud...")
        run_cmd("firebase deploy", capture_output=False)
        return True

    run_step("Deploying to Web", deploy_systems)

    # --- 8. BRAIN ACTIVATION ---
    def train_brain():
        print("Activating AI Brain (Fine-Tuning LoRA)...")
        subprocess.check_call([sys.executable, "train.py"])

    run_step("Awakening the AI Brain", train_brain)

    print("\n" + "="*70)
    print("      🎊  ZERO-TOUCH SETUP COMPLETE! SPIDER-ARM IS LIVE 🎊")
    print("="*70)
    print(f"URL: https://{project_id}.web.app")
    print("\nNext steps:")
    print("1. Open the URL on your phone.")
    print("2. Run 'python -m backend.firebase_bridge' to start the heartbeat.")
    print("\nWelcome to the future of PC Assistant control! 🕸️🤖")

if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n[WIZARD] Setup cancelled.")
    except Exception as e:
        print(f"\n[FATAL] Wizard crashed: {e}")
