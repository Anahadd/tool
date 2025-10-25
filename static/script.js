// Global state
let currentUser = null;
let currentEditingSheetId = null;

// Wait for Firebase to initialize
window.onFirebaseAuthChanged = async (user) => {
    if (user) {
        currentUser = user;
        await onUserSignedIn(user);
    } else {
        currentUser = null;
        showAuthPage();
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    
    // Show loading while Firebase initializes
    showToast('Loading...', 'info');
});

function setupEventListeners() {
    // Auth forms
    document.getElementById('signInForm').addEventListener('submit', handleSignIn);
    document.getElementById('createAccountForm').addEventListener('submit', handleCreateAccount);
    document.getElementById('forgotPasswordForm').addEventListener('submit', handleForgotPassword);
    
    // Dashboard buttons
    document.getElementById('addSheetBtn').addEventListener('click', showAddSheetModal);
    document.getElementById('settingsBtn').addEventListener('click', showSettingsModal);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    
    // Settings
    document.getElementById('credentialsFile').addEventListener('change', handleCredentialsUpload);
    document.getElementById('connectSheetsBtn').addEventListener('click', connectToGoogleSheets);
    document.getElementById('deleteCredentialsBtn').addEventListener('click', deleteCredentials);
    
    // Search
    document.getElementById('searchInput').addEventListener('input', filterSheets);
}

// ========================================
// AUTH FUNCTIONS
// ========================================

async function handleSignIn(e) {
    e.preventDefault();
    
    const email = document.getElementById('signInEmail').value.trim();
    const password = document.getElementById('signInPassword').value;
    
    if (!email || !password) {
        showToast('Please enter email and password', 'error');
        return;
    }
    
    try {
        showToast('Signing in...', 'info');
        await window.firebase.login(email, password);
        // Firebase will trigger onFirebaseAuthChanged
    } catch (error) {
        console.error('Sign in error:', error);
        if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
            showToast('Invalid email or password', 'error');
        } else {
            showToast(`Sign in failed: ${error.message}`, 'error');
        }
    }
}

async function handleCreateAccount(e) {
    e.preventDefault();
    
    const email = document.getElementById('createEmail').value.trim();
    const password = document.getElementById('createPassword').value;
    const username = document.getElementById('createUsername').value.trim();
    
    if (!email || !password || !username) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    try {
        showToast('Creating account...', 'info');
        await window.firebase.register(email, password, username);
        showToast('Account created successfully!', 'success');
        // Firebase will trigger onFirebaseAuthChanged
    } catch (error) {
        console.error('Registration error:', error);
        if (error.code === 'auth/email-already-in-use') {
            showToast('Email already registered. Try signing in.', 'error');
        } else if (error.code === 'auth/weak-password') {
            showToast('Password should be at least 6 characters', 'error');
        } else {
            showToast(`Registration failed: ${error.message}`, 'error');
        }
    }
}

async function handleForgotPassword(e) {
    e.preventDefault();
    
    const email = document.getElementById('forgotEmail').value.trim();
    
    if (!email) {
        showToast('Please enter your email', 'error');
        return;
    }
    
    try {
        await window.firebase.resetPassword(email);
        showToast('Password reset email sent! Check your inbox.', 'success');
        setTimeout(() => showSignIn(), 2000);
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    }
}

async function handleLogout() {
    try {
        await window.firebase.logout();
        showToast('Signed out successfully', 'success');
        location.reload();
    } catch (error) {
        showToast(`Logout failed: ${error.message}`, 'error');
    }
}

// ========================================
// PAGE NAVIGATION
// ========================================

function showAuthPage() {
    document.getElementById('authPage').classList.remove('hidden');
    document.getElementById('adminDashboard').classList.add('hidden');
    showSignIn();
}

function showSignIn() {
    document.getElementById('signInPage').classList.remove('hidden');
    document.getElementById('createAccountPage').classList.add('hidden');
    document.getElementById('forgotPasswordPage').classList.add('hidden');
}

function showCreateAccount() {
    document.getElementById('signInPage').classList.add('hidden');
    document.getElementById('createAccountPage').classList.remove('hidden');
    document.getElementById('forgotPasswordPage').classList.add('hidden');
}

function showForgotPassword() {
    document.getElementById('signInPage').classList.add('hidden');
    document.getElementById('createAccountPage').classList.add('hidden');
    document.getElementById('forgotPasswordPage').classList.remove('hidden');
}

async function onUserSignedIn(user) {
    console.log('User signed in:', user.email);
    
    // Hide auth page, show dashboard
    document.getElementById('authPage').classList.add('hidden');
    document.getElementById('adminDashboard').classList.remove('hidden');
    
    showToast(`Welcome back, ${user.email}!`, 'success');
    
    // Check credentials status
    await checkCredentialsStatus();
    
    // Load user's sheets
    await loadSheets();
}

// ========================================
// SHEETS MANAGEMENT
// ========================================

async function loadSheets() {
    try {
        const user = window.firebase.getCurrentUser();
        if (!user) return;
        
        const db = window.firebaseDB;
        const sheetsRef = window.firebase.collection(db, 'user_sheets');
        const q = window.firebase.query(sheetsRef, 
            window.firebase.where('user_id', '==', user.uid),
            window.firebase.orderBy('created_at', 'desc')
        );
        
        const querySnapshot = await window.firebase.getDocs(q);
        const sheets = [];
        querySnapshot.forEach((doc) => {
            sheets.push({ id: doc.id, ...doc.data() });
        });
        
        renderSheets(sheets);
    } catch (error) {
        console.error('Error loading sheets:', error);
        showToast('Failed to load sheets', 'error');
    }
}

function renderSheets(sheets) {
    const tbody = document.getElementById('sheetsTableBody');
    
    if (sheets.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    <p>No Google Sheets added yet</p>
                    <button onclick="showAddSheetModal()" class="btn btn-primary">
                        <span class="btn-icon">+</span> Add Your First Sheet
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = sheets.map((sheet, index) => `
        <tr data-sheet-id="${sheet.id}">
            <td class="checkbox-col">
                <input type="checkbox" data-sheet-id="${sheet.id}">
            </td>
            <td class="number-col">${index + 1}</td>
            <td class="name-col">
                <div class="sheet-name">${escapeHtml(sheet.name)}</div>
                <div class="sheet-id">${sheet.id.substring(0, 10)}</div>
            </td>
            <td class="description-col">
                <span class="description-text ${sheet.description ? '' : 'placeholder'}">
                    ${sheet.description ? escapeHtml(sheet.description) : 'Add description here'}
                </span>
            </td>
            <td class="status-col">
                <button onclick="runUpdate('${sheet.id}')" class="btn run-update-btn" id="run-${sheet.id}">
                    Run Update
                </button>
            </td>
        </tr>
    `).join('');
    
    // Add double-click to edit
    tbody.querySelectorAll('tr[data-sheet-id]').forEach(row => {
        row.addEventListener('dblclick', () => {
            const sheetId = row.getAttribute('data-sheet-id');
            editSheet(sheetId);
        });
    });
}

function filterSheets() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#sheetsTableBody tr[data-sheet-id]');
    
    rows.forEach(row => {
        const name = row.querySelector('.sheet-name')?.textContent.toLowerCase() || '';
        const description = row.querySelector('.description-text')?.textContent.toLowerCase() || '';
        
        if (name.includes(searchTerm) || description.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// ========================================
// SHEET MODAL
// ========================================

function showAddSheetModal() {
    currentEditingSheetId = null;
    document.getElementById('modalTitle').textContent = 'Add Google Sheet';
    document.getElementById('sheetName').value = '';
    document.getElementById('sheetUrl').value = '';
    document.getElementById('sheetWorksheet').value = 'Sheet1';
    document.getElementById('sheetDescription').value = '';
    document.getElementById('sheetModal').classList.remove('hidden');
}

async function editSheet(sheetId) {
    try {
        const db = window.firebaseDB;
        const sheetDoc = await window.firebase.getDoc(window.firebase.doc(db, 'user_sheets', sheetId));
        
        if (!sheetDoc.exists()) {
            showToast('Sheet not found', 'error');
            return;
        }
        
        const sheet = sheetDoc.data();
        currentEditingSheetId = sheetId;
        
        document.getElementById('modalTitle').textContent = 'Edit Google Sheet';
        document.getElementById('sheetName').value = sheet.name;
        document.getElementById('sheetUrl').value = sheet.spreadsheet_url;
        document.getElementById('sheetWorksheet').value = sheet.worksheet_name || 'Sheet1';
        document.getElementById('sheetDescription').value = sheet.description || '';
        document.getElementById('sheetModal').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading sheet:', error);
        showToast('Failed to load sheet', 'error');
    }
}

function closeSheetModal() {
    document.getElementById('sheetModal').classList.add('hidden');
    currentEditingSheetId = null;
}

async function saveSheet() {
    const name = document.getElementById('sheetName').value.trim();
    const url = document.getElementById('sheetUrl').value.trim();
    const worksheet = document.getElementById('sheetWorksheet').value.trim() || 'Sheet1';
    const description = document.getElementById('sheetDescription').value.trim();
    
    if (!name || !url) {
        showToast('Please enter name and URL', 'error');
        return;
    }
    
    try {
        const user = window.firebase.getCurrentUser();
        if (!user) {
            showToast('Not authenticated', 'error');
            return;
        }
        
        const db = window.firebaseDB;
        const sheetData = {
            name,
            spreadsheet_url: url,
            worksheet_name: worksheet,
            description,
            user_id: user.uid
        };
        
        if (currentEditingSheetId) {
            // Update existing
            await window.firebase.updateDoc(window.firebase.doc(db, 'user_sheets', currentEditingSheetId), sheetData);
            showToast('Sheet updated successfully!', 'success');
        } else {
            // Create new
            sheetData.created_at = new Date();
            await window.firebase.addDoc(window.firebase.collection(db, 'user_sheets'), sheetData);
            showToast('Sheet added successfully!', 'success');
        }
        
        closeSheetModal();
        await loadSheets();
    } catch (error) {
        console.error('Error saving sheet:', error);
        showToast(`Failed to save: ${error.message}`, 'error');
    }
}

// ========================================
// RUN UPDATE
// ========================================

async function runUpdate(sheetId) {
    const btn = document.getElementById(`run-${sheetId}`);
    if (!btn || btn.disabled) return;
    
    try {
        btn.disabled = true;
        btn.classList.add('running');
        btn.textContent = 'Running...';
        
        // Get sheet data
        const db = window.firebaseDB;
        const sheetDoc = await window.firebase.getDoc(window.firebase.doc(db, 'user_sheets', sheetId));
        
        if (!sheetDoc.exists()) {
            throw new Error('Sheet not found');
        }
        
        const sheet = sheetDoc.data();
        
        showToast(`Updating ${sheet.name}...`, 'info');
        
        // Get ID token for API auth
        const idToken = await window.firebase.getIdToken();
        
        const formData = new FormData();
        formData.append('spreadsheet', sheet.spreadsheet_url);
        formData.append('worksheet', sheet.worksheet_name);
        formData.append('override', 'true');
        
        const response = await fetch('/api/update-sheets', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${idToken}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✓ ${sheet.name} updated successfully!`, 'success');
        } else {
            throw new Error(data.message || 'Update failed');
        }
        
    } catch (error) {
        console.error('Update error:', error);
        showToast(`Update failed: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.classList.remove('running');
        btn.textContent = 'Run Update';
    }
}

// ========================================
// SETTINGS & CREDENTIALS
// ========================================

function showSettingsModal() {
    document.getElementById('settingsModal').classList.remove('hidden');
    checkCredentialsStatus();
}

function closeSettingsModal() {
    document.getElementById('settingsModal').classList.add('hidden');
}

async function checkCredentialsStatus() {
    try {
        const hasCredentials = await window.firebase.hasCredentials();
        
        const statusBox = document.getElementById('credentialsStatus');
        const connectBtn = document.getElementById('connectSheetsBtn');
        
        if (hasCredentials) {
            statusBox.classList.remove('hidden');
            connectBtn.disabled = false;
        } else {
            statusBox.classList.add('hidden');
            connectBtn.disabled = true;
        }
    } catch (error) {
        console.error('Error checking credentials:', error);
    }
}

async function handleCredentialsUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.json')) {
        showToast('Please upload a JSON file', 'error');
        return;
    }
    
    try {
        showToast('Uploading credentials...', 'info');
        await window.firebase.uploadCredentials(file);
        showToast('✓ Credentials saved to your account!', 'success');
        await checkCredentialsStatus();
    } catch (error) {
        console.error('Upload error:', error);
        showToast(`Upload failed: ${error.message}`, 'error');
    }
}

async function connectToGoogleSheets() {
    try {
        showToast('Connecting to Google Sheets...', 'info');
        
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
            
            showToast('Complete authorization in popup...', 'info');
        } else {
            throw new Error('Failed to start OAuth');
        }
    } catch (error) {
        console.error('Connection error:', error);
        showToast(`Connection failed: ${error.message}`, 'error');
    }
}

async function deleteCredentials() {
    if (!confirm('Are you sure you want to delete your saved credentials? You\'ll need to upload them again.')) {
        return;
    }
    
    try {
        showToast('Deleting credentials...', 'info');
        await window.firebase.deleteCredentials();
        showToast('✓ Credentials deleted', 'success');
        await checkCredentialsStatus();
    } catch (error) {
        console.error('Delete error:', error);
        showToast(`Delete failed: ${error.message}`, 'error');
    }
}

// ========================================
// UTILITIES
// ========================================

function showToast(message, type = 'info') {
    const toast = document.getElementById('statusToast');
    const icon = document.getElementById('toastIcon');
    const msg = document.getElementById('toastMessage');
    
    const icons = {
        'success': '✓',
        'error': '✗',
        'info': 'ℹ'
    };
    
    toast.className = `status-toast ${type}`;
    icon.textContent = icons[type] || 'ℹ';
    msg.textContent = message;
    toast.classList.remove('hidden');
    
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 5000);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// OAuth callback listener
window.addEventListener('message', async (event) => {
    if (event.data.type === 'oauth_success') {
        showToast('✓ Google Sheets connected successfully!', 'success');
    } else if (event.data.type === 'oauth_error') {
        showToast(`OAuth failed: ${event.data.message}`, 'error');
    }
});


