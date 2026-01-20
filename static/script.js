// ===== GLOBAL STATE =====
let whitelist = ['github.com', 'stackoverflow. com', 'docs.python. org'];
let timerInterval = null;
let timeRemaining = 25 * 60; // 25 minutes in seconds
let isTimerRunning = false;
let sessionStartTime = null;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    loadBlocklist(); // Load custom blocklist on startup
    setInterval(checkStatus, 5000); // Check status every 5 seconds
    updateTimerDisplay();
});

// ===== STATUS CHECK =====
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        updateStatusBadge(status);
        updateStats(status);
        
        if (! status.is_admin) {
            showAdminWarning(status. platform);
        }
        
        if (status.is_blocking) {
            document.getElementById('blockBtn').style.display = 'none';
            document.getElementById('unblockBtn').style.display = 'block';
        } else {
            document.getElementById('blockBtn').style.display = 'block';
            document.getElementById('unblockBtn').style.display = 'none';
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

function updateStatusBadge(status) {
    const badge = document.getElementById('statusBadge');
    const dot = badge.querySelector('.status-dot');
    const text = badge.querySelector('.status-text');
    
    if (status.is_blocking) {
        dot.style.background = '#ef4444'; // Red
        text.textContent = 'Focus Mode Active';
    } else if (! status.is_admin) {
        dot.style.background = '#f59e0b'; // Orange
        text.textContent = 'Admin Required';
    } else {
        dot.style.background = '#10b981'; // Green
        text.textContent = 'Ready';
    }
}

function updateStats(status) {
    const sessionTime = Math.floor(status.session_duration / 60);
    document.getElementById('sessionTime').textContent = `${sessionTime}m`;
    document.getElementById('blockedCount').textContent = status.distractions_blocked;
}

function showAdminWarning(platform) {
    const warning = document.getElementById('adminWarning');
    const instructions = document.getElementById('adminInstructions');
    
    warning.style.display = 'flex';
    
    if (platform === 'Windows') {
        instructions.innerHTML = `
            <strong>Windows:</strong> Close this browser, right-click Command Prompt, 
            select "Run as administrator", then run: <code>python app.py</code>
        `;
    } else {
        instructions.innerHTML = `
            <strong>${platform}:</strong> Run the app with sudo:  
            <code>sudo python3 app.py</code>
        `;
    }
}

// ===== TIMER FUNCTIONS =====
function toggleTimer() {
    if (isTimerRunning) {
        pauseTimer();
    } else {
        startTimer();
    }
}

function startTimer() {
    isTimerRunning = true;
    sessionStartTime = Date.now();
    
    const btn = document.getElementById('startBtn');
    btn.innerHTML = '<span class="btn-icon">⏸</span>Pause';
    btn.classList.remove('btn-primary');
    btn.classList.add('btn-secondary');
    
    timerInterval = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        
        if (timeRemaining <= 0) {
            timerComplete();
        }
    }, 1000);
}

function pauseTimer() {
    isTimerRunning = false;
    clearInterval(timerInterval);
    
    const btn = document.getElementById('startBtn');
    btn.innerHTML = '<span class="btn-icon">▶</span>Resume';
    btn.classList.add('btn-primary');
    btn.classList.remove('btn-secondary');
}

function resetTimer() {
    isTimerRunning = false;
    clearInterval(timerInterval);
    timeRemaining = 25 * 60;
    updateTimerDisplay();
    
    const btn = document.getElementById('startBtn');
    btn.innerHTML = '<span class="btn-icon">▶</span>Start Session';
    btn.classList.add('btn-primary');
    btn.classList.remove('btn-secondary');
}

function setTimer(minutes) {
    if (isTimerRunning) {
        pauseTimer();
    }
    
    timeRemaining = minutes * 60;
    updateTimerDisplay();
    
    // Update active preset button
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    document.getElementById('timerDisplay').textContent = display;
    
    // Change color based on time remaining
    const timerDisplay = document.getElementById('timerDisplay');
    if (timeRemaining < 60) {
        timerDisplay. style.color = '#ef4444'; // Red
    } else if (timeRemaining < 300) {
        timerDisplay. style.color = '#f59e0b'; // Orange
    } else {
        timerDisplay. style.color = '#6366f1'; // Primary
    }
}

function timerComplete() {
    isTimerRunning = false;
    clearInterval(timerInterval);
    
    showToast('🎉 Focus session complete!  Great job!', 'success');
    
    // Play notification sound
    playNotificationSound();
    
    // Reset button
    const btn = document.getElementById('startBtn');
    btn.innerHTML = '<span class="btn-icon">▶</span>Start Session';
    btn.classList.add('btn-primary');
    btn.classList.remove('btn-secondary');
    
    // Update streak
    const streakEl = document.getElementById('streakCount');
    streakEl.textContent = parseInt(streakEl.textContent) + 1;
}

// ===== WHITELIST FUNCTIONS =====
function addToWhitelist() {
    const input = document.getElementById('whitelistInput');
    const site = input.value.trim().toLowerCase();
    
    if (!site) {
        showToast('Please enter a website', 'error');
        return;
    }
    
    // Remove protocol and www
    const cleanSite = site.replace(/^(https?:\/\/)?(www\.)?/, '');
    
    if (whitelist.includes(cleanSite)) {
        showToast('Site already in whitelist', 'error');
        return;
    }
    
    whitelist.push(cleanSite);
    renderWhitelist();
    input.value = '';
    showToast(`Added ${cleanSite} to whitelist`, 'success');
}

function removeFromWhitelist(button, site) {
    whitelist = whitelist.filter(s => s !== site);
    button.parentElement.remove();
    showToast(`Removed ${site} from whitelist`, 'success');
}

function renderWhitelist() {
    const container = document.getElementById('whitelistTags');
    container.innerHTML = '';
    
    whitelist.forEach(site => {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            <span>${site}</span>
            <button onclick="removeFromWhitelist(this, '${site}')">×</button>
        `;
        container.appendChild(tag);
    });
}

function handleWhitelistEnter(event) {
    if (event.key === 'Enter') {
        addToWhitelist();
    }
}

// ===== BLOCKLIST FUNCTIONS =====
async function loadBlocklist() {
    try {
        const response = await fetch('/api/blocklist');
        const data = await response.json();
        
        if (data.success) {
            renderBlocklist(data.custom_sites);
        }
    } catch (error) {
        console.error('Failed to load blocklist:', error);
    }
}

async function addToBlocklist() {
    const input = document.getElementById('blocklistInput');
    const site = input.value.trim().toLowerCase();
    
    if (!site) {
        showToast('Please enter a website', 'error');
        return;
    }
    
    // Remove protocol and www
    const cleanSite = site.replace(/^(https?:\/\/)?(www\.)?/, '');
    
    try {
        const response = await fetch('/api/blocklist/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                website: cleanSite
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            renderBlocklist(result.blocklist);
            input.value = '';
            showToast(`🚫 Added ${cleanSite} to blocklist`, 'success');
        } else {
            showToast(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('❌ Failed to add to blocklist', 'error');
    }
}

async function removeFromBlocklist(button, site) {
    try {
        const response = await fetch('/api/blocklist/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                website: site
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            renderBlocklist(result.blocklist);
            showToast(`✅ Removed ${site} from blocklist`, 'success');
        } else {
            showToast(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('❌ Failed to remove from blocklist', 'error');
    }
}

function renderBlocklist(sites) {
    const container = document.getElementById('blocklistTags');
    container.innerHTML = '';
    
    if (sites.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; font-size: 14px;">No custom blocked sites yet. Add some above!</p>';
        return;
    }
    
    sites.forEach(site => {
        const tag = document.createElement('div');
        tag.className = 'tag tag-danger';
        tag.innerHTML = `
            <span>${site}</span>
            <button onclick="removeFromBlocklist(this, '${site}')">×</button>
        `;
        container.appendChild(tag);
    });
}

function handleBlocklistEnter(event) {
    if (event.key === 'Enter') {
        addToBlocklist();
    }
}

// ===== BLOCKING FUNCTIONS =====
async function startBlocking() {
    const btn = document.getElementById('blockBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span>Starting... ';
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                whitelist: whitelist
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`🔒 Focus mode activated!  ${result.blocked_count} sites blocked.`, 'success');
            document.getElementById('blockBtn').style.display = 'none';
            document.getElementById('unblockBtn').style.display = 'block';
            
            // Auto-start timer
            if (! isTimerRunning) {
                startTimer();
            }
        } else {
            showToast(`❌ Error: ${result.error}`, 'error');
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">🔒</span>Start Focus Mode';
        }
    } catch (error) {
        showToast('❌ Failed to start focus mode', 'error');
        btn.disabled = false;
        btn. innerHTML = '<span class="btn-icon">🔒</span>Start Focus Mode';
    }
}

async function stopBlocking() {
    const btn = document.getElementById('unblockBtn');
    btn.disabled = true;
    btn. innerHTML = '<span class="btn-icon">⏳</span>Stopping...';
    
    try {
        const response = await fetch('/api/stop', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('🔓 Focus mode deactivated.  All sites unblocked.', 'success');
            document.getElementById('blockBtn').style.display = 'block';
            document.getElementById('unblockBtn').style.display = 'none';
            
            // Pause timer
            if (isTimerRunning) {
                pauseTimer();
            }
        } else {
            showToast(`❌ Error: ${result. error}`, 'error');
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">🔓</span>Stop Focus Mode';
        }
    } catch (error) {
        showToast('❌ Failed to stop focus mode', 'error');
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">🔓</span>Stop Focus Mode';
    }
}

// ===== UTILITY FUNCTIONS =====
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast. className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function playNotificationSound() {
    // Create a simple beep using Web Audio API
    try {
        const audioContext = new (window.AudioContext || window. webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext. createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator. start(audioContext.currentTime);
        oscillator.stop(audioContext. currentTime + 0.5);
    } catch (e) {
        console.log('Could not play sound');
    }
}
