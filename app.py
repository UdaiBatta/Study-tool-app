from flask import Flask, render_template, jsonify, request
import os
import platform
import time
from datetime import datetime
import ctypes
import signal
import atexit
import requests
import json

app = Flask(__name__)

# ===== CONFIGURATION =====
# Set your online blocklist URL here (GitHub Gist, Pastebin, or your own API)
ONLINE_BLOCKLIST_URL = os.getenv('BLOCKLIST_URL', '')
# Fallback to local list if online fetch fails
USE_ONLINE_BLOCKLIST = True
CACHE_DURATION = 300  # Cache for 5 minutes
CUSTOM_BLOCKLIST_FILE = "custom_blocklist.json"  # User's custom blocked sites

class StudyFocusManager: 
    """Manages website blocking and study sessions"""
    
    def __init__(self):
        self.platform = platform.system()
        self.hosts_path = self._get_hosts_path()
        self.redirect_ip = "127.0.0.1"
        self.backup_file = "hosts_backup.txt"
        self.is_blocking = False
        self.session_start = None
        self.distractions_blocked = 0
        self.cached_blocklist = None
        self.cache_timestamp = 0
        self.custom_blocklist = self._load_custom_blocklist()
        
    def _get_hosts_path(self):
        """Get hosts file path based on OS"""
        if self.platform == "Windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        else:
            return "/etc/hosts"
    
    def _load_custom_blocklist(self):
        """Load user's custom blocklist from file"""
        try:
            if os.path.exists(CUSTOM_BLOCKLIST_FILE):
                with open(CUSTOM_BLOCKLIST_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('websites', [])
        except Exception as e:
            print(f"⚠️  Could not load custom blocklist: {e}")
        return []
    
    def _save_custom_blocklist(self):
        """Save user's custom blocklist to file"""
        try:
            with open(CUSTOM_BLOCKLIST_FILE, 'w') as f:
                json.dump({'websites': self.custom_blocklist}, f, indent=2)
            return True
        except Exception as e:
            print(f"⚠️  Could not save custom blocklist: {e}")
            return False
    
    def add_to_blocklist(self, website):
        """Add a website to custom blocklist"""
        website = website.strip().lower()
        # Remove protocol and www if present
        website = website.replace('http://', '').replace('https://', '')
        website = website.replace('www.', '')
        # Remove trailing slash
        website = website.rstrip('/')
        
        if website and website not in self.custom_blocklist:
            self.custom_blocklist.append(website)
            # Also add www version
            www_version = f"www.{website}"
            if www_version not in self.custom_blocklist:
                self.custom_blocklist.append(www_version)
            
            self._save_custom_blocklist()
            return True
        return False
    
    def remove_from_blocklist(self, website):
        """Remove a website from custom blocklist"""
        website = website.strip().lower()
        if website in self.custom_blocklist:
            self.custom_blocklist.remove(website)
            self._save_custom_blocklist()
            return True
        return False
    
    def get_custom_blocklist(self):
        """Get user's custom blocklist"""
        return self.custom_blocklist
    
    def _get_default_blocklist(self):
        """Default blocked sites (fallback)"""
        return [
            "www.facebook.com", "facebook.com",
            "www.instagram.com", "instagram.com",
            "www.twitter.com", "twitter.com", "x.com",
            "www.youtube.com", "youtube.com", "m.youtube.com",
            "www.reddit.com", "reddit.com",
            "www.tiktok.com", "tiktok.com",
            "www.netflix.com", "netflix.com",
            "www.twitch.tv", "twitch.tv",
            "discord.com", "www.discord.com",
            "www.snapchat.com", "snapchat.com",
            "www.pinterest.com", "pinterest.com",
            "www.9gag.com", "9gag.com",
            "www.imgur.com", "imgur.com",
            "www.x.com/home"
        ]
    
    def fetch_online_blocklist(self):
        """Fetch blocklist from online source"""
        # Check cache first
        current_time = time.time()
        if (self.cached_blocklist and 
            current_time - self.cache_timestamp < CACHE_DURATION):
            return self.cached_blocklist
        
        if not ONLINE_BLOCKLIST_URL or not USE_ONLINE_BLOCKLIST:
            return self._get_default_blocklist()
        
        try:
            response = requests.get(ONLINE_BLOCKLIST_URL, timeout=5)
            response.raise_for_status()
            
            # Support JSON format: {"websites": ["site1.com", "site2.com"]}
            # Or plain text format (one site per line)
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                data = response.json()
                blocklist = data.get('websites', data.get('sites', []))
            else:
                # Plain text format
                blocklist = [
                    line.strip() 
                    for line in response.text.strip().split('\n') 
                    if line.strip() and not line.startswith('#')
                ]
            
            # Cache the result
            self.cached_blocklist = blocklist
            self.cache_timestamp = current_time
            
            print(f"✅ Fetched {len(blocklist)} sites from online source")
            return blocklist
            
        except Exception as e:
            print(f"⚠️  Failed to fetch online blocklist: {e}")
            print("   Using default blocklist...")
            return self._get_default_blocklist()
    
    def get_combined_blocklist(self):
        """Combine online/default blocklist with user's custom list"""
        # Start with online or default list
        if ONLINE_BLOCKLIST_URL:
            base_list = self.fetch_online_blocklist()
        else:
            base_list = self._get_default_blocklist()
        
        # Combine with custom blocklist (remove duplicates)
        combined = list(set(base_list + self.custom_blocklist))
        return combined
    
    def _check_admin(self):
        """Check if running with admin privileges"""
        try:
            if self.platform == "Windows": 
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else: 
                return os.geteuid() == 0
        except: 
            return False
    
    def block_websites(self, allowed_sites):
        """Block all websites except whitelisted ones"""
        if not self._check_admin():
            return {
                "success": False,
                "error": "Administrator privileges required!"
            }
        
        # Backup hosts file
        try:
            with open(self.hosts_path, 'r') as file:
                original_content = file.read()
            
            with open(self.backup_file, 'w') as backup: 
                backup.write(original_content)
        except Exception as e:
            return {
                "success": False,
                "error": f"Backup failed: {str(e)}"
            }
        
        # Get combined blocklist (online + custom)
        blocked_sites = self.get_combined_blocklist()
        
        # Remove whitelisted sites
        blocked_sites = [site for site in blocked_sites if site not in allowed_sites]
        
        # Write to hosts file
        try:
            with open(self.hosts_path, 'a') as file:
                file.write("\n\n# === STUDY FOCUS MODE - ACTIVE ===\n")
                file.write(f"# Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write("# DO NOT EDIT WHILE FOCUS MODE IS ACTIVE\n")
                if ONLINE_BLOCKLIST_URL:
                    file.write(f"# Blocklist source: {ONLINE_BLOCKLIST_URL}\n")
                file.write("\n")
                
                for site in blocked_sites: 
                    file.write(f"{self.redirect_ip} {site}\n")
            
            self.is_blocking = True
            self.session_start = time.time()
            self.distractions_blocked = len(blocked_sites)
            
            # Flush DNS cache
            self._flush_dns()
            
            return {
                "success": True,
                "blocked_count": len(blocked_sites),
                "source": "online" if ONLINE_BLOCKLIST_URL else "default"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Blocking failed: {str(e)}"
            }
    
    def unblock_websites(self):
        """Restore normal internet access"""
        if not os.path.exists(self.backup_file):
            return {
                "success": False,
                "error": "No backup file found"
            }
        
        try:
            with open(self.backup_file, 'r') as backup:
                original_content = backup.read()
            
            with open(self.hosts_path, 'w') as file:
                file.write(original_content)
            
            # Keep backup for safety - rename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"hosts_backup_{timestamp}.txt"
            os.rename(self.backup_file, backup_name)
            print(f"✅ Backup saved as: {backup_name}")
            
            self.is_blocking = False
            
            # Flush DNS cache
            self._flush_dns()
            
            return {
                "success": True,
                "message": "All websites unblocked"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Unblocking failed: {str(e)}"
            }
    
    def _flush_dns(self):
        """Flush DNS cache to apply changes immediately"""
        try:
            if self.platform == "Windows": 
                os.system("ipconfig /flushdns > nul 2>&1")
            elif self.platform == "Darwin":  # macOS
                os.system("dscacheutil -flushcache > /dev/null 2>&1")
            else:  # Linux
                os.system("sudo systemd-resolve --flush-caches > /dev/null 2>&1")
        except:
            pass
    
    def get_status(self):
        """Get current blocking status"""
        session_duration = 0
        if self.session_start:
            session_duration = int(time.time() - self.session_start)
        
        return {
            "is_blocking": self.is_blocking,
            "is_admin": self._check_admin(),
            "session_duration": session_duration,
            "distractions_blocked": self.distractions_blocked,
            "platform": self.platform
        }

# Initialize manager
focus_manager = StudyFocusManager()

# Cleanup on exit
def cleanup():
    """Restore internet on program exit"""
    if focus_manager.is_blocking:
        print("\n🔄 Cleaning up... Restoring internet access...")
        focus_manager.unblock_websites()
        print("✅ Internet restored!")

# Register cleanup handlers
atexit.register(cleanup)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    cleanup()
    print("\n👋 Study Focus App stopped. Good luck with your studies!")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Routes
@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current status"""
    return jsonify(focus_manager.get_status())

@app.route('/api/start', methods=['POST'])
def start_blocking():
    """Start blocking websites"""
    data = request.json
    allowed_sites = data.get('whitelist', [])
    result = focus_manager.block_websites(allowed_sites)
    return jsonify(result)

@app.route('/api/stop', methods=['POST'])
def stop_blocking():
    """Stop blocking websites"""
    result = focus_manager.unblock_websites()
    return jsonify(result)

@app.route('/api/blocklist', methods=['GET'])
def get_blocklist():
    """Get custom blocklist"""
    return jsonify({
        "success": True,
        "custom_sites": focus_manager.get_custom_blocklist(),
        "default_sites": focus_manager._get_default_blocklist()
    })

@app.route('/api/blocklist/add', methods=['POST'])
def add_to_blocklist():
    """Add website to custom blocklist"""
    data = request.json
    website = data.get('website', '')
    
    if not website:
        return jsonify({"success": False, "error": "Website required"})
    
    success = focus_manager.add_to_blocklist(website)
    if success:
        return jsonify({
            "success": True,
            "message": f"Added {website} to blocklist",
            "blocklist": focus_manager.get_custom_blocklist()
        })
    else:
        return jsonify({
            "success": False,
            "error": "Website already in blocklist or invalid"
        })

@app.route('/api/blocklist/remove', methods=['POST'])
def remove_from_blocklist():
    """Remove website from custom blocklist"""
    data = request.json
    website = data.get('website', '')
    
    if not website:
        return jsonify({"success": False, "error": "Website required"})
    
    success = focus_manager.remove_from_blocklist(website)
    if success:
        return jsonify({
            "success": True,
            "message": f"Removed {website} from blocklist",
            "blocklist": focus_manager.get_custom_blocklist()
        })
    else:
        return jsonify({
            "success": False,
            "error": "Website not found in custom blocklist"
        })

@app.route('/api/blocklist/custom', methods=['GET', 'POST', 'DELETE'])
def manage_custom_blocklist():
    """Manage custom blocklist (add/remove websites)"""
    if request.method == 'GET':
        # Return current custom blocklist
        return jsonify({
            "success": True,
            "websites": focus_manager.get_custom_blocklist()
        })
    
    data = request.json or {}
    website = data.get('website', '').strip()
    
    if request.method == 'POST':
        # Add website to blocklist
        if focus_manager.add_to_blocklist(website):
            return jsonify({
                "success": True,
                "message": f"✅ '{website}' added to blocklist"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid website or already in blocklist"
            })
    
    elif request.method == 'DELETE':
        # Remove website from blocklist
        if focus_manager.remove_from_blocklist(website):
            return jsonify({
                "success": True,
                "message": f"✅ '{website}' removed from blocklist"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Website not found in blocklist"
            })
    
    return jsonify({
        "success": False,
        "error": "Invalid request"
    })

if __name__ == '__main__': 
    print("\n" + "="*60)
    print("🎯 STUDY FOCUS APP")
    print("="*60)
    print("Starting web server...")
    print("Open your browser to: http://localhost:5000")
    print("\n⚠️  Make sure to run as Administrator/sudo!")
    print("⚠️  Press Ctrl+C to stop (internet will auto-restore)")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
