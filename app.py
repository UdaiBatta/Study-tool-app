from flask import Flask, render_template, jsonify, request
import os
import platform
import time
from datetime import datetime
import ctypes
import signal
import atexit

app = Flask(__name__)

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
        
    def _get_hosts_path(self):
        """Get hosts file path based on OS"""
        if self.platform == "Windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        else:
            return "/etc/hosts"
    
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
        
        # Define blocked sites (uncomment to activate)
        blocked_sites = [
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
        ]
        
        # Remove whitelisted sites
        blocked_sites = [site for site in blocked_sites if site not in allowed_sites]
        
        # Write to hosts file
        try:
            with open(self.hosts_path, 'a') as file:
                file.write("\n\n# === STUDY FOCUS MODE - ACTIVE ===\n")
                file.write(f"# Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write("# DO NOT EDIT WHILE FOCUS MODE IS ACTIVE\n\n")
                
                for site in blocked_sites: 
                    file.write(f"{self.redirect_ip} {site}\n")
            
            self.is_blocking = True
            self.session_start = time.time()
            self.distractions_blocked = len(blocked_sites)
            
            # Flush DNS cache
            self._flush_dns()
            
            return {
                "success": True,
                "blocked_count": len(blocked_sites)
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