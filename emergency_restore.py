"""
 EMERGENCY INTERNET RESTORE SCRIPT
Run this as Administrator if your internet gets stuck blocked!
"""

import os
import platform

def restore_internet():
    """Emergency restore of internet access"""
    system = platform.system()
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if system == "Windows" else "/etc/hosts"
    
    print("\n EMERGENCY INTERNET RESTORE")
    print("=" * 50)
    
    # Method 1: Restore from backup if it exists
    backup_files = [f for f in os.listdir('.') if f.startswith('hosts_backup')]
    
    if backup_files:
        backup_file = backup_files[-1]  # Use the most recent
        print(f"\n Found backup: {backup_file}")
        print(" Restoring from backup...")
        
        try:
            with open(backup_file, 'r') as backup:
                original_content = backup.read()
            
            with open(hosts_path, 'w') as file:
                file.write(original_content)
            
            print(" Hosts file restored from backup!")
        except Exception as e:
            print(f" Error restoring from backup: {e}")
            print("  Trying manual cleanup...")
            clean_hosts_file(hosts_path)
    else:
        print("\n⚠️  No backup found. Cleaning hosts file manually...")
        clean_hosts_file(hosts_path)
    
    # Flush DNS cache
    print("\n🔄 Flushing DNS cache...")
    try:
        if system == "Windows":
            os.system("ipconfig /flushdns")
        elif system == "Darwin":
            os.system("dscacheutil -flushcache")
        else:
            os.system("sudo systemd-resolve --flush-caches")
        print DNS cache flushed!")
    except Exception as e:
        print(f"  DNS flush warning: {e}")
    
    print("\n" + "=" * 50)
    print(" DONE! Your internet should work now.")
    print(" Try opening a website to test.")
    print("=" * 50 + "\n")

def clean_hosts_file(hosts_path):
    """Remove STUDY FOCUS MODE entries from hosts file"""
    try:
        with open(hosts_path, 'r') as file:
            lines = file.readlines()
        
        cleaned_lines = []
        skip_section = False
        
        for line in lines:
            # Start of our blocking section
            if "# === STUDY FOCUS MODE - ACTIVE ===" in line:
                skip_section = True
                continue
            
            # Skip all lines in our section
            if skip_section:
                # Empty line or comment - keep skipping
                if line.strip() == "" or line.startswith("#"):
                    continue
                # Line starting with 127.0.0.1 - this is our blocked site
                elif line.strip().startswith("127.0.0.1"):
                    continue
                # Something else - end of our section
                else:
                    skip_section = False
            
            # Keep lines that aren't in our blocking section
            if not skip_section:
                cleaned_lines.append(line)
        
        # Write cleaned content back
        with open(hosts_path, 'w') as file:
            file.writelines(cleaned_lines)
        
        print(" Hosts file cleaned!")
        
    except Exception as e:
        print(f" Error cleaning hosts file: {e}")
        print("\n MANUAL FIX:")
        print(f"1. Open Notepad as Administrator")
        print(f"2. Open: {hosts_path}")
        print("3. Delete all lines starting with '127.0.0.1' that block websites")
        print("4. Save the file")
        print("5. Run 'ipconfig /flushdns' in Command Prompt")

if __name__ == "__main__":
    try:
        import ctypes
        if platform.system() == "Windows":
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("\n ERROR: This script needs Administrator privileges!")
                print("\n HOW TO FIX:")
                print("1. Right-click on PowerShell or Command Prompt")
                print("2. Select 'Run as Administrator'")
                print("3. Navigate to this folder:")
                print(f"   cd {os.getcwd()}")
                print("4. Run: python emergency_restore.py")
                input("\nPress Enter to exit...")
                exit(1)
        
        restore_internet()
        input("\nPress Enter to exit...")
        
    except KeyboardInterrupt:
        print("\n\n Cancelled by user")
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        input("\nPress Enter to exit...")
