// Global state
let ws = null;
let currentUser = null;

// Wait for Firebase to initialize
window.onFirebaseAuthChanged = async (user) => {
    if (user) {
        currentUser = user;
        await onUserSignedIn(user);
    } else {
        currentUser = null;
        showLoginModal();
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    connectWebSocket();
    setupOAuthMessageListener();
    
    // Show loading while Firebase initializes
    if (!window.firebaseUser) {
        showStatus('Loading...', 'info');
    }
});

async function onUserSignedIn(user) {
    console.log('User signed in:', user.email);
    hideLoginModal();
    
    showStatus(`Welcome back, ${user.email}!`, 'success');
    
    // Check if user has credentials stored
    try {
        const hasCredentials = await window.firebase.hasCredentials();
        
        if (hasCredentials) {
            showStatus('✓ Credentials loaded from your account', 'success');
            document.getElementById('credentialsStatus').classList.remove('hidden');
            document.getElementById('connectSheetsBtn').disabled = false;
        } else {
            showStatus('Please upload your credentials.json file', 'info');
        }
    } catch (error) {
        console.error('Error checking credentials:', error);
    }
    
    // Load user preferences (default sheet URL, etc.)
    try {
        const prefs = await window.firebase.getPreferences();
        
        if (prefs && prefs.spreadsheet_url) {
            document.getElementById('spreadsheetUrl').value = prefs.spreadsheet_url;
            document.getElementById('worksheetName').value = prefs.worksheet_name || 'Sheet1';
            showStatus('✓ Default sheet settings loaded', 'success');
            
            // Show "Clear Defaults" button
            document.getElementById('clearDefaultsBtn').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error loading preferences:', error);
    }
}

function showLoginModal() {
    document.getElementById('authModal').classList.remove('hidden');
}

function hideLoginModal() {
    document.getElementById('authModal').classList.add('hidden');
}

// Auth functions
async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const username = document.getElementById('registerUsername').value.trim();
    
    if (!email || !password || !username) {
        showStatus('Please fill in all fields', 'error');
        return;
    }
    
    try {
        showStatus('Creating account...', 'info');
        await window.firebase.register(email, password, username);
        showStatus('✓ Account created! You are now signed in.', 'success');
        // Firebase will auto-trigger onFirebaseAuthChanged
    } catch (error) {
        if (error.code === 'auth/email-already-in-use') {
            showStatus('⚠️ Email already registered. Try logging in.', 'warning');
            showLoginForm();
        } else if (error.code === 'auth/weak-password') {
            showStatus('Password should be at least 6 characters', 'error');
        } else {
            showStatus(`Registration failed: ${error.message}`, 'error');
        }
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        showStatus('Please enter email and password', 'error');
        return;
    }
    
    try {
        showStatus('Signing in...', 'info');
        await window.firebase.login(email, password);
        showStatus('✓ Signed in successfully!', 'success');
        // Firebase will auto-trigger onFirebaseAuthChanged
    } catch (error) {
        if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
            showStatus('Invalid email or password', 'error');
        } else {
            showStatus(`Login failed: ${error.message}`, 'error');
        }
    }
}

async function handleLogout() {
    try {
        await window.firebase.logout();
        showStatus('✓ Signed out', 'success');
        location.reload(); // Reload to reset everything
    } catch (error) {
        showStatus(`Logout failed: ${error.message}`, 'error');
    }
}

async function handleForgotPassword(event) {
    event.preventDefault();
    
    const email = document.getElementById('forgotEmail').value.trim();
    
    if (!email) {
        showStatus('Please enter your email', 'error');
        return;
    }
    
    try {
        await window.firebase.resetPassword(email);
        showStatus('✓ Password reset email sent! Check your inbox.', 'success');
        setTimeout(() => showLoginForm(), 2000);
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

function showLoginForm() {
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById('forgotPasswordForm').classList.add('hidden');
}

function showRegisterForm() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.remove('hidden');
    document.getElementById('forgotPasswordForm').classList.add('hidden');
}

function showForgotPassword() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById('forgotPasswordForm').classList.remove('hidden');
}

// File handling
function setupEventListeners() {
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);
    document.getElementById('connectSheetsBtn').addEventListener('click', connectSheets);
    document.getElementById('saveDefaultsBtn').addEventListener('click', saveDefaults);
    document.getElementById('clearDefaultsBtn').addEventListener('click', clearDefaults);
    document.getElementById('deleteCredentialsBtn').addEventListener('click', deleteCredentials);
    document.getElementById('runUpdateBtn').addEventListener('click', runUpdate);
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('dropZone').classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.target.closest('.drop-zone').classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    event.target.closest('.drop-zone').classList.remove('drag-over');
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

async function uploadFile(file) {
    if (!file.name.endsWith('.json')) {
        showStatus('Please upload a JSON file', 'error');
        return;
    }
    
    if (!currentUser) {
        showStatus('Please sign in first', 'error');
        return;
    }
    
    try {
        showStatus('Uploading credentials to your account...', 'info');
        
        // Upload to Firebase Storage
        await window.firebase.uploadCredentials(file);
        
        showStatus('✓ Credentials saved to your account!', 'success');
        
        // Update UI
        const dropContent = document.getElementById('dropContent');
        const fileInfo = document.getElementById('fileInfo');
        
        document.getElementById('fileName').textContent = `✓ ${file.name}`;
        dropContent.classList.add('hidden');
        fileInfo.classList.remove('hidden');
        document.getElementById('credentialsStatus').classList.remove('hidden');
        document.getElementById('connectSheetsBtn').disabled = false;
        
    } catch (error) {
        showStatus(`Upload failed: ${error.message}`, 'error');
    }
}

function clearFile() {
    const dropContent = document.getElementById('dropContent');
    const fileInfo = document.getElementById('fileInfo');
    
    dropContent.classList.remove('hidden');
    fileInfo.classList.add('hidden');
    document.getElementById('fileInput').value = '';
}

async function deleteCredentials() {
    if (!confirm('Are you sure you want to delete your saved credentials? You\'ll need to upload them again.')) {
        return;
    }
    
    try {
        showStatus('Deleting credentials...', 'info');
        await window.firebase.deleteCredentials();
        
        showStatus('✓ Credentials deleted', 'success');
        
        // Reset UI
        clearFile();
        document.getElementById('credentialsStatus').classList.add('hidden');
        document.getElementById('connectSheetsBtn').disabled = true;
        
    } catch (error) {
        showStatus(`Delete failed: ${error.message}`, 'error');
    }
}

async function connectSheets() {
    if (!currentUser) {
        showStatus('Please sign in first', 'error');
        return;
    }
    
    try {
        showStatus('Connecting to Google Sheets...', 'info');
        
        // Get ID token for backend auth
        const idToken = await window.firebase.getIdToken();
        
        const response = await fetch('/api/oauth-start', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${idToken}`
            }
        });
        
        const data = await response.json();
        
        if (data.auth_url) {
            const width = 600;
            const height = 700;
            const left = (screen.width / 2) - (width / 2);
            const top = (screen.height / 2) - (height / 2);
            
            window.open(
                data.auth_url,
                'Google OAuth',
                `width=${width},height=${height},left=${left},top=${top}`
            );
            
            showStatus('Complete authorization in popup...', 'info');
        } else {
            showStatus('Failed to start OAuth flow', 'error');
        }
    } catch (error) {
        showStatus(`Connection failed: ${error.message}`, 'error');
    }
}

async function saveDefaults() {
    const spreadsheetUrl = document.getElementById('spreadsheetUrl').value.trim();
    const worksheetName = document.getElementById('worksheetName').value.trim();
    
    if (!spreadsheetUrl) {
        showStatus('Please enter a spreadsheet URL first', 'error');
        return;
    }
    
    if (!currentUser) {
        showStatus('Please sign in first', 'error');
        return;
    }
    
    try {
        showStatus('Saving defaults...', 'info');
        
        await window.firebase.savePreferences({
            spreadsheet_url: spreadsheetUrl,
            worksheet_name: worksheetName || 'Sheet1'
        });
        
        showStatus('✓ Defaults saved! They will auto-load next time.', 'success');
        document.getElementById('clearDefaultsBtn').classList.remove('hidden');
        
    } catch (error) {
        showStatus(`Save failed: ${error.message}`, 'error');
    }
}

async function clearDefaults() {
    if (!confirm('Clear saved defaults? You\'ll need to enter the sheet URL again next time.')) {
        return;
    }
    
    try {
        showStatus('Clearing defaults...', 'info');
        
        await window.firebase.savePreferences({
            spreadsheet_url: '',
            worksheet_name: 'Sheet1'
        });
        
        showStatus('✓ Defaults cleared', 'success');
        document.getElementById('clearDefaultsBtn').classList.add('hidden');
        document.getElementById('spreadsheetUrl').value = '';
        document.getElementById('worksheetName').value = 'Sheet1';
        
    } catch (error) {
        showStatus(`Clear failed: ${error.message}`, 'error');
    }
}

async function runUpdate() {
    const spreadsheetUrl = document.getElementById('spreadsheetUrl').value.trim();
    const worksheetName = document.getElementById('worksheetName').value.trim() || 'Sheet1';
    const disableColumns = document.getElementById('disableColumns').value.trim();
    const rowRange = document.getElementById('rowRange').value.trim();
    const overrideData = document.getElementById('overrideData').checked;
    
    if (!spreadsheetUrl) {
        showStatus('Please enter a spreadsheet URL', 'error');
        return;
    }
    
    if (!currentUser) {
        showStatus('Please sign in first', 'error');
        return;
    }
    
    const runBtn = document.getElementById('runUpdateBtn');
    const btnText = document.getElementById('runBtnText');
    const btnSpinner = document.getElementById('runBtnSpinner');
    
    runBtn.disabled = true;
    btnText.textContent = 'Running...';
    btnSpinner.classList.remove('hidden');
    
    try {
        showStatus('Fetching stats from TikTok, YouTube, and Instagram...', 'info');
        
        // Get ID token for backend auth
        const idToken = await window.firebase.getIdToken();
        
        const formData = new FormData();
        formData.append('spreadsheet', spreadsheetUrl);
        formData.append('worksheet', worksheetName);
        formData.append('disable_columns', disableColumns);
        formData.append('override', overrideData);
        
        if (rowRange) {
            const parts = rowRange.split(':').map(p => parseInt(p.trim()));
            if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
                formData.append('start_row', parts[0]);
                formData.append('end_row', parts[1]);
            }
        }
        
        const response = await fetch('/api/update-sheets', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${idToken}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('✓ Sheet updated successfully!', 'success');
        } else {
            showStatus(`Update failed: ${data.message || 'Unknown error'}`, 'error');
        }
        
    } catch (error) {
        showStatus(`Update failed: ${error.message}`, 'error');
    } finally {
        runBtn.disabled = false;
        btnText.textContent = 'Run Update';
        btnSpinner.classList.add('hidden');
    }
}

function toggleAdvanced() {
    const options = document.getElementById('advancedOptions');
    const toggle = document.getElementById('advancedToggle');
    
    if (options.classList.contains('hidden')) {
        options.classList.remove('hidden');
        toggle.textContent = '▲';
    } else {
        options.classList.add('hidden');
        toggle.textContent = '▼';
    }
}

function showStatus(message, type = 'info') {
    const statusBar = document.getElementById('statusBar');
    const statusMessage = document.getElementById('statusMessage');
    const statusIcon = document.getElementById('statusIcon');
    
    const icons = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ'
    };
    
    statusIcon.textContent = icons[type] || 'ℹ';
    statusMessage.textContent = message;
    statusBar.className = 'status-bar';
    statusBar.classList.add(type);
    statusBar.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => statusBar.classList.add('hidden'), 5000);
    }
}

// WebSocket for real-time updates
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        showStatus(message.message, message.type || 'info');
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        setTimeout(connectWebSocket, 5000);
    };
}

// OAuth callback listener
function setupOAuthMessageListener() {
    window.addEventListener('message', async (event) => {
        if (event.data.type === 'oauth_success') {
            showStatus('✓ Google Sheets connected successfully!', 'success');
            
            // OAuth token is already saved on backend, no action needed
            
        } else if (event.data.type === 'oauth_error') {
            showStatus(`OAuth failed: ${event.data.message}`, 'error');
        }
    });
}

