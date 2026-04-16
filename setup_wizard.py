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
    print("      🕷️  Spider-ARM: Hybrid 'Cloud Architect' Wizard v2.5 🕷️")
    print("="*70)
    print("Build or Link your Firebase Infrastructure in minutes.")
    print("Requirement: You must have the Firebase CLI installed.\n")

def get_input(prompt, default=None):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

def run_cmd(cmd, capture_output=True):
    """Runs a shell command and returns the output."""
    try:
        # Specified encoding='utf-8' and errors='ignore' to handle Windows symbol mismatches
        result = subprocess.run(cmd, capture_output=capture_output, text=True, shell=True, check=True, encoding='utf-8', errors='ignore')
        # Check if stdout exists before stripping (handles capture_output=False)
        return result.stdout.strip() if result.stdout else ""
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed: {cmd}")
        if e.stderr:
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
        out = run_cmd("firebase projects:list")
        if not out or "Error" in out:
            print("Action Required: Please log in to Firebase in your browser.")
            run_cmd("firebase login", capture_output=False)
        return True

    if not run_step("Firebase Authentication", check_auth): return

    # --- 2. MODE SELECTION ---
    print("\nHow would you like to set up Spider-Arm?")
    print("[1] Create Fresh Project (Zero-Touch - Recommended)")
    print("[2] Link to Existing Project (Choose from your cloud list)")
    
    choice = get_input("Select mode", "1")
    
    project_id = None
    web_config = None

    if choice == "2":
        # --- LINK EXISTING ---
        def fetch_projects():
            print("Fetching your Firebase projects...")
            out = run_cmd("firebase projects:list --json")
            if not out: return False
            
            data = json.loads(out)
            projects = data.get("result", [])
            
            if not projects:
                print("[ERROR] No Firebase projects found in your account.")
                return False
                
            print("\nYour Projects:")
            for i, p in enumerate(projects):
                print(f"[{i+1}] {p['projectId']} ({p.get('displayName', 'No Title')})")
                
            pick = int(get_input("\nSelect Project Number", "1")) - 1
            selected = projects[pick]['projectId']
            
            # Fetch Web Apps in this project
            print(f"Checking for Web Apps in '{selected}'...")
            apps_out = run_cmd(f"firebase apps:list WEB --project {selected} --json")
            apps_data = json.loads(apps_out) if apps_out else {"result": []}
            apps = apps_data.get("result", [])
            
            app_id = None
            if not apps:
                print("No Web App found in this project. Registering 'Spider Dashboard'...")
                run_cmd(f"firebase apps:create WEB 'Spider Dashboard' --project {selected}", capture_output=False)
                # Re-fetch
                apps_out = run_cmd(f"firebase apps:list WEB --project {selected} --json")
                apps = json.loads(apps_out).get("result", [])
            
            if apps:
                print("\nChoose Web App:")
                for i, a in enumerate(apps):
                    print(f"[{i+1}] {a['displayName']} ({a['appId']})")
                apick = int(get_input("Select App Number", "1")) - 1
                app_id = apps[apick]['appId']
            
            # Harvest Config
            print("Harvesting SDK credentials...")
            config_out = run_cmd(f"firebase apps:sdkconfig WEB {app_id} --project {selected} --json")
            if config_out:
                cfg_data = json.loads(config_out)
                return (selected, cfg_data.get("result", {}).get("sdkConfig"))
            return False

        res = run_step("Linking Existing Project", fetch_projects)
        if not res: return
        project_id, web_config = res
        # Switch CLI to this project
        run_cmd(f"firebase use {project_id}", capture_output=False)

    else:
        # --- CREATE NEW ---
        project_id = generate_id()
        def create_project():
            print(f"Creating project '{project_id}'... this takes ~30 seconds.")
            run_cmd(f"firebase projects:create {project_id} --display-name 'Spider Arm Assistant'", capture_output=False)
            run_cmd(f"firebase use {project_id}", capture_output=False)
            return True

        if not run_step(f"Provisioning Cloud Project ({project_id})", create_project): return

        def enable_firestore():
            print("Initializing Firestore Database (Region: us-central)...")
            run_cmd(f"firebase firestore:databases:create (default) --location us-central", capture_output=False)
            return True
        run_step("Activating Firestore Database", enable_firestore)

        def register_app():
            print("Registering the 'Spider Dashboard' Web App...")
            run_cmd(f"firebase apps:create WEB 'Spider Dashboard'", capture_output=False)
            config_out = run_cmd("firebase apps:sdkconfig WEB --json")
            if config_out:
                data = json.loads(config_out)
                return data.get("result", {}).get("sdkConfig")
            return None

        web_config = run_step("Registering Web Dashboard", register_app)

    if not web_config: 
        print("[CRITICAL] Could not harvest Web SDK Keys.")
        return

    # --- 3. UNIFIED VAULT INJECTION ---
    def save_vault():
        email = get_input("Your Gmail (for Security Lockdown rules)")
        
        vault = {
            "web_dashboard": web_config,
            "authorized_email": email,
            "service_account": None
        }
        
        js_content = "export const firebaseConfig = " + json.dumps(web_config, indent=4) + ";"
        with open("mobile/firebase-config.js", "w") as f:
            f.write(js_content)
        
        return vault

    vault = run_step("Generating Unified Vault & Dashboard Config", save_vault)

    # --- 4. SERVICE ACCOUNT ---
    def fetch_service_account():
        print("\n[SECURITY LINKING]")
        print("1. Your browser will open to the Service Accounts page.")
        print("2. Click 'Generate New Private Key'.")
        print("3. Paste the ENTIRE content of that JSON file here.")
        
        url = f"https://console.firebase.google.com/project/{project_id}/settings/serviceaccounts/adminsdk"
        webbrowser.open(url)
        
        print("\nPaste the JSON content (Press Enter on empty line when finished):")
        lines = []
        while True:
            line = input()
            if line == "": break
            lines.append(line)
        
        try:
            sa_data = json.loads("".join(lines))
            vault["service_account"] = sa_data
            with open("credentials.json", "w") as f:
                json.dump(vault, f, indent=4)
            return True
        except:
            print("[ERROR] Invalid JSON pasted.")
            return False

    if not run_step("Linking Security Systems (Service Account)", fetch_service_account): return

    # --- 5. DEPLOY ---
    def deploy_systems():
        print("Pushing Security Rules and Dashboard to the Cloud...")
        run_cmd("firebase deploy", capture_output=False)
        return True

    run_step("Live Deployment", deploy_systems)

    print("\n" + "="*70)
    print("      🎊  HYBRID SETUP COMPLETE! SPIDER-ARM IS LIVE 🎊")
    print("="*70)
    print(f"Project ID: {project_id}")
    print(f"Dashboard URL: https://{project_id}.web.app")
    print("\nNext steps:")
    print("1. Open the URL on your phone.")
    print("2. Run 'python -m backend.firebase_bridge' to start the bridge.")
    print("\nWelcome back to the loop! 🕸️🤖")

if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n[WIZARD] Setup cancelled.")
    except Exception as e:
        print(f"\n[FATAL] Wizard crashed: {e}")
