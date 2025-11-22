// web/script.js

// =========================================
// DOM REFERENCES
// =========================================

// Config Inputs
const apiKeyInput = document.getElementById('api-key');
const modelNameInput = document.getElementById('model-name');
const rateLimitInput = document.getElementById('rate-limit');
const stealthToggle = document.getElementById('stealth-toggle');
const boosterToggle = document.getElementById('booster-toggle');
const stealthOptionsDiv = document.getElementById('stealth-options');
const minDelayInput = document.getElementById('min-delay');
const maxDelayInput = document.getElementById('max-delay');

// Buttons
const btnSave = document.getElementById('btn-save-config');
const btnChrome = document.getElementById('btn-chrome');
const btnSolve = document.getElementById('btn-solve');
const btnClearLog = document.getElementById('btn-clear-log');
const btnCopyLog = document.getElementById('btn-copy-log');
const btnTheme = document.getElementById('theme-toggle');

// Outputs
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const logContainer = document.getElementById('session-log');

// Local State
let isBrowserRunning = false;

// =========================================
// UI LOGIC (Theme, Animations)
// =========================================

// Theme Toggle
btnTheme.addEventListener('click', () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
});

// Stealth Toggle Animation
stealthToggle.addEventListener('change', () => {
    if (stealthToggle.checked) {
        stealthOptionsDiv.classList.add('active');
    } else {
        stealthOptionsDiv.classList.remove('active');
    }
});

// Clear Log
btnClearLog.addEventListener('click', () => {
    logContainer.innerHTML = '';
    append_log('Log cleared by user.', 'system');
});

// Copy Log
if (btnCopyLog) {
    btnCopyLog.addEventListener('click', () => {
        if (!logContainer) return;
        const text = logContainer.innerText;

        // QtWebEngine has a bug with navigator.clipboard permissions,
        // so we use the fallback 'execCommand' method directly.
        useFallback();

        function showCopied() {
            const originalText = btnCopyLog.textContent;
            btnCopyLog.textContent = 'COPIED';
            setTimeout(() => {
                btnCopyLog.textContent = originalText;
            }, 1500);
        }

        function useFallback() {
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed'; // Avoid scrolling to bottom
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showCopied();
            } catch (err) {
                console.error('Failed to copy log via fallback:', err);
                append_log('[ERROR] Failed to copy log to clipboard.');
            }
        }
    });
}


// =========================================
// BACKEND -> FRONTEND BRIDGE
// =========================================

// Called by Python to set text status
function updateStatusLabel(running) {
    if (running) {
        statusText.textContent = 'SOLVING';
        statusText.style.color = 'var(--accent)';
        statusDot.classList.add('running');
    } else {
        statusText.textContent = 'IDLE';
        statusText.style.color = 'var(--text-muted)';
        statusDot.classList.remove('running');
    }
}

// Called by Python to add log lines
function append_log(message, typeOverride) {
    if (!logContainer) return;

    const text = typeof message === 'string' ? message : JSON.stringify(message);
    const line = document.createElement('div');
    line.classList.add('log-line');

    if (typeOverride) {
        line.classList.add(typeOverride);
    } else if (text.includes('[ERROR]')) {
        line.classList.add('error');
    } else if (text.includes('[SUCCESS]')) {
        line.classList.add('success');
    } else if (text.includes('[INFO]')) {
        line.classList.add('info');
    } else if (text.includes('[WARN]')) {
        line.classList.add('info'); // Warn shares info color for now, or add .warn class
    } else if (text.includes('[ACTION]')) {
        line.classList.add('action');
    } else if (text.includes('[SOLVER]')) {
        line.classList.add('solver');
    } else if (text.includes('[DEBUG]')) {
        line.classList.add('debug');
    } else {
        line.classList.add('system');
    }

    line.textContent = `> ${text}`;
    logContainer.appendChild(line);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Called by Python to load saved settings
function load_settings(settings) {
    if (!settings || typeof settings !== 'object') return;

    if (apiKeyInput) apiKeyInput.value = settings.apiKey ?? '';
    if (modelNameInput) modelNameInput.value = settings.modelName ?? '';
    if (rateLimitInput) rateLimitInput.value = String(settings.rateLimitSeconds ?? 0);
    if (minDelayInput) minDelayInput.value = String(settings.minDelaySeconds ?? 5.0);
    if (maxDelayInput) maxDelayInput.value = String(settings.maxDelaySeconds ?? 20.0);

    if (stealthToggle) {
        stealthToggle.checked = !!settings.stealthEnabled;
        if (stealthToggle.checked) {
            stealthOptionsDiv.classList.add('active');
        } else {
            stealthOptionsDiv.classList.remove('active');
        }
    }

    if (boosterToggle) {
        boosterToggle.checked = !!settings.boosterEnabled;
    }
}

// Called by Python when browser launches/closes
function set_browser_state(running) {
    isBrowserRunning = !!running;
    console.log('Python commanded Browser state change to:', isBrowserRunning);

    const btnSpan = btnChrome.querySelector('span span');

    if (isBrowserRunning) {
        // Change "Launch Browser" to "Close Browser" and make red outline
        if (btnSpan) btnSpan.textContent = 'Close Browser';
        btnChrome.classList.add('stop');

        // Enable the solve button
        btnSolve.disabled = false;
    } else {
        if (btnSpan) btnSpan.textContent = 'Launch Browser';
        btnChrome.classList.remove('stop');

        // Disable the solve button (cannot solve without browser)
        btnSolve.disabled = true;
    }
}

// Called by Python when solving starts/stops
function set_ui_state(running) {
    const shouldRun = !!running;
    const btnSpan = btnSolve.querySelector('span span');

    if (shouldRun) {
        if (btnSpan) btnSpan.textContent = 'Stop Solving';
        btnSolve.classList.add('stop');
    } else {
        if (btnSpan) btnSpan.textContent = 'Start Solving';
        btnSolve.classList.remove('stop');
    }
    updateStatusLabel(shouldRun);
}

// =========================================
// FRONTEND -> BACKEND BRIDGE
// =========================================

async function handleLaunchChromeClick() {
    if (isBrowserRunning) {
        console.log('JS asking Python to CLOSE browser...');
        try {
            await window.pywebview.api.close_browser();
        } catch (e) {
            console.error('Error calling close_browser:', e);
            append_log('[ERROR] Backend communication failed.');
        }
    } else {
        console.log('JS asking Python to LAUNCH browser...');
        append_log('[INFO] Launching browser...');
        try {
            await window.pywebview.api.launch_chrome();
        } catch (e) {
            console.error('Error calling launch_chrome:', e);
            append_log('[ERROR] Backend communication failed.');
        }
    }
}

async function handleStartSolvingClick() {
    console.log('JS asking Python to toggle solver loop...');
    try {
        await window.pywebview.api.toggle_automation();
    } catch (e) {
        console.error('Error calling toggle_automation:', e);
        append_log('[ERROR] Failed to call backend.');
    }
}

async function handleSaveClick() {
    console.log('JS asking Python to save settings...');

    const btnSpan = btnSave.querySelector('span span');
    const originalText = btnSpan.textContent;
    btnSpan.textContent = 'Saving...';

    const currentSettings = {
        apiKey: apiKeyInput?.value || '',
        modelName: modelNameInput?.value || '',
        rateLimitSeconds: parseFloat(rateLimitInput?.value || '0') || 0,
        stealthEnabled: !!stealthToggle?.checked,
        minDelaySeconds: parseFloat(minDelayInput?.value || '0') || 0,
        maxDelaySeconds: parseFloat(maxDelayInput?.value || '0') || 0,
        boosterEnabled: !!boosterToggle?.checked,
    };

    try {
        const response = await window.pywebview.api.save_settings(currentSettings);
        if (response && response.status === 'success') {
            append_log('[SUCCESS] Settings saved.');
        } else {
            append_log(`[ERROR] Failed to save settings: ${response?.message}`);
        }
    } catch (e) {
        console.error('Error calling save_settings:', e);
        append_log('[ERROR] Save failed exception.');
    }

    setTimeout(() => {
        btnSpan.textContent = originalText;
    }, 1000);
}

// =========================================
// INITIALIZATION
// =========================================

window.addEventListener('pywebviewready', async () => {
    console.log('pywebview ready.');

    if (btnChrome) btnChrome.addEventListener('click', handleLaunchChromeClick);
    if (btnSolve) btnSolve.addEventListener('click', handleStartSolvingClick);
    if (btnSave) btnSave.addEventListener('click', handleSaveClick);

    // Initial State
    set_browser_state(false);

    // Load Settings
    try {
        const response = await window.pywebview.api.load_settings();
        if (response && response.error) {
            append_log(`[ERROR] ${response.error}`);
        } else if (response) {
            load_settings(response);
            append_log('[INFO] Settings loaded from backend.');
        }
    } catch (e) {
        append_log('[ERROR] Backend connection failed.');
    }
});
// =========================================
// AUDIO FEEDBACK
// =========================================

function play_success_sound() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;

        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        // Nice "ding" sound
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
        osc.frequency.exponentialRampToValueAtTime(1046.5, ctx.currentTime + 0.1); // C6

        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);

        osc.start();
        osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
        console.error("Audio playback failed:", e);
    }
}
