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
    // Auth
    const googleBtn = document.getElementById('googleSignInBtn');
    if (googleBtn) {
        googleBtn.addEventListener('click', handleGoogleSignIn);
    }
    
    // Credentials Setup Page
    const setupDropZone = document.getElementById('setupDropZone');
    if (setupDropZone) {
        setupDropZone.addEventListener('click', () => document.getElementById('setupFileInput').click());
        setupDropZone.addEventListener('dragover', handleSetupDragOver);
        setupDropZone.addEventListener('dragleave', handleSetupDragLeave);
        setupDropZone.addEventListener('drop', handleSetupDrop);
    }
    
    const setupFileInput = document.getElementById('setupFileInput');
    if (setupFileInput) {
        setupFileInput.addEventListener('change', handleSetupFileSelect);
    }
    
    const setupChooseBtn = document.getElementById('setupChooseFileBtn');
    if (setupChooseBtn) {
        setupChooseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('setupFileInput').click();
        });
    }
    
    const setupClearBtn = document.getElementById('setupClearFileBtn');
    if (setupClearBtn) {
        setupClearBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            clearSetupFile();
        });
    }
    
    const continueBtn = document.getElementById('continueBtn');
    if (continueBtn) {
        continueBtn.addEventListener('click', handleContinueFromSetup);
    }
    
    // Dashboard buttons
    const addSheetBtn = document.getElementById('addSheetBtn');
    if (addSheetBtn) {
        addSheetBtn.addEventListener('click', showAddSheetModal);
    }
    
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', showSettingsModal);
    }
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Sheet Modal
    const closeSheetModalBtn = document.getElementById('closeSheetModalBtn');
    if (closeSheetModalBtn) {
        closeSheetModalBtn.addEventListener('click', closeSheetModal);
    }
    
    const cancelSheetBtn = document.getElementById('cancelSheetBtn');
    if (cancelSheetBtn) {
        cancelSheetBtn.addEventListener('click', closeSheetModal);
    }
    
    const saveSheetBtn = document.getElementById('saveSheetBtn');
    if (saveSheetBtn) {
        saveSheetBtn.addEventListener('click', saveSheet);
    }
    
    // Settings Modal
    const closeSettingsBtn = document.getElementById('closeSettingsModalBtn');
    if (closeSettingsBtn) {
        closeSettingsBtn.addEventListener('click', closeSettingsModal);
    }
    
    const chooseCredBtn = document.getElementById('chooseCredFileBtn');
    if (chooseCredBtn) {
        chooseCredBtn.addEventListener('click', () => document.getElementById('credentialsFile').click());
    }
    
    const credFile = document.getElementById('credentialsFile');
    if (credFile) {
        credFile.addEventListener('change', handleCredentialsUpload);
    }
    
    const connectBtn = document.getElementById('connectSheetsBtn');
    if (connectBtn) {
        connectBtn.addEventListener('click', connectToGoogleSheets);
    }
    
    const deleteBtn = document.getElementById('deleteCredentialsBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteCredentials);
    }
    
    // Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterSheets);
    }
}

// ========================================
// AUTH FUNCTIONS
// ========================================

async function handleGoogleSignIn() {
    try {
        showToast('Signing in with Google...', 'info');
        await window.firebase.signInWithGoogle();
        // Firebase will trigger onFirebaseAuthChanged
    } catch (error) {
        console.error('Google sign-in error:', error);
        if (error.code === 'auth/popup-closed-by-user') {
            showToast('Sign-in cancelled', 'info');
        } else {
            showToast(`Sign-in failed: ${error.message}`, 'error');
        }
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
}

async function onUserSignedIn(user) {
    console.log('User signed in:', user.email);
    
    // Check if user has credentials
    const hasCredentials = await window.firebase.hasCredentials();
    
    if (!hasCredentials) {
        // First time user - show credentials setup page
        document.getElementById('authPage').classList.add('hidden');
        document.getElementById('credentialsSetupPage').classList.remove('hidden');
        document.getElementById('adminDashboard').classList.add('hidden');
        showToast('Welcome! Please upload your credentials to continue.', 'info');
    } else {
        // Returning user - go straight to dashboard
        document.getElementById('authPage').classList.add('hidden');
        document.getElementById('credentialsSetupPage').classList.add('hidden');
        document.getElementById('adminDashboard').classList.remove('hidden');
        
        showToast(`Welcome back, ${user.email}!`, 'success');
        
        // Check credentials status
        await checkCredentialsStatus();
        
        // Load user's sheets
        await loadSheets();
    }
}

// ========================================
// CREDENTIALS SETUP PAGE
// ========================================

let setupFile = null;

function handleSetupDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('setupDropZone').classList.add('drag-over');
}

function handleSetupDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('setupDropZone').classList.remove('drag-over');
}

function handleSetupDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('setupDropZone').classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processSetupFile(files[0]);
    }
}

function handleSetupFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processSetupFile(files[0]);
    }
}

function processSetupFile(file) {
    if (!file.name.endsWith('.json')) {
        showToast('Please upload a JSON file', 'error');
        return;
    }
    
    setupFile = file;
    
    // Update UI
    document.getElementById('setupDropContent').classList.add('hidden');
    document.getElementById('setupFileInfo').classList.remove('hidden');
    document.getElementById('setupFileName').textContent = `✓ ${file.name}`;
    document.getElementById('continueBtn').disabled = false;
}

function clearSetupFile() {
    setupFile = null;
    document.getElementById('setupDropContent').classList.remove('hidden');
    document.getElementById('setupFileInfo').classList.add('hidden');
    document.getElementById('setupFileInput').value = '';
    document.getElementById('continueBtn').disabled = true;
}

async function handleContinueFromSetup() {
    if (!setupFile) {
        showToast('Please select a file first', 'error');
        return;
    }
    
    try {
        showToast('Uploading credentials...', 'info');
        
        await window.firebase.uploadCredentials(setupFile);
        
        showToast('Credentials saved! Now connecting to Google Sheets...', 'success');
        
        // Automatically start OAuth flow
        await connectToGoogleSheetsOnSetup();
        
    } catch (error) {
        console.error('Upload error:', error);
        showToast(`Upload failed: ${error.message}`, 'error');
    }
}

async function connectToGoogleSheetsOnSetup() {
    try {
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
            
            const popup = window.open(
                data.auth_url,
                'Google OAuth',
                `width=${width},height=${height},left=${left},top=${top}`
            );
            
            // Listen for OAuth completion
            window.addEventListener('message', async (event) => {
                if (event.data.type === 'oauth_success') {
                    showToast('Google Sheets connected! Loading dashboard...', 'success');
                    
                    // Now show dashboard
                    document.getElementById('credentialsSetupPage').classList.add('hidden');
                    document.getElementById('adminDashboard').classList.remove('hidden');
                    
                    // Load user's sheets
                    await loadSheets();
                } else if (event.data.type === 'oauth_error') {
                    showToast(`OAuth failed: ${event.data.message}`, 'error');
                }
            }, { once: true });
            
            showToast('Complete authorization in the popup window...', 'info');
        } else {
            throw new Error(data.message || 'Failed to start OAuth');
        }
    } catch (error) {
        console.error('OAuth error:', error);
        showToast(`Connection failed: ${error.message}`, 'error');
        
        // Still show dashboard even if OAuth fails
        document.getElementById('credentialsSetupPage').classList.add('hidden');
        document.getElementById('adminDashboard').classList.remove('hidden');
        await loadSheets();
    }
}

// ========================================
// SHEETS MANAGEMENT
// ========================================

async function loadSheets() {
    try {
        const user = window.firebase.getCurrentUser();
        if (!user) {
            console.log('No user signed in');
            renderSheets([]);
            return;
        }
        
        console.log('Loading sheets for user:', user.uid);
        
        const db = window.firebaseDB;
        const sheetsRef = window.firebase.collection(db, 'user_sheets');
        
        // Query sheets for this user
        const q = window.firebase.query(
            sheetsRef, 
            window.firebase.where('user_id', '==', user.uid)
        );
        
        const querySnapshot = await window.firebase.getDocs(q);
        const sheets = [];
        
        querySnapshot.forEach((doc) => {
            const data = doc.data();
            sheets.push({ 
                id: doc.id, 
                ...data,
                created_at: data.created_at?.toDate?.() || new Date()
            });
        });
        
        // Sort by created_at descending
        sheets.sort((a, b) => b.created_at - a.created_at);
        
        console.log(`Loaded ${sheets.length} sheets`);
        renderSheets(sheets);
        
    } catch (error) {
        console.error('Error loading sheets:', error);
        showToast(`Failed to load sheets: ${error.message}`, 'error');
        renderSheets([]);
    }
}

function renderSheets(sheets) {
    const tbody = document.getElementById('sheetsTableBody');
    
    if (sheets.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
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
                <input type="checkbox" class="sheet-checkbox" data-sheet-id="${sheet.id}">
            </td>
            <td class="number-col">${index + 1}</td>
            <td class="name-col">
                <div class="sheet-name">${escapeHtml(sheet.name)}</div>
            </td>
            <td class="description-col">
                <span class="description-text ${sheet.description ? '' : 'placeholder'}">
                    ${sheet.description ? escapeHtml(sheet.description) : 'Add description here'}
                </span>
            </td>
            <td class="status-col">
                ${renderStatusBadge(sheet.status, sheet.last_updated)}
            </td>
            <td class="action-col">
                <button onclick="runUpdate('${sheet.id}')" class="btn run-update-btn" id="run-${sheet.id}">
                    Run Update
                </button>
            </td>
        </tr>
    `).join('');
    
    // Add double-click to edit
    tbody.querySelectorAll('tr[data-sheet-id]').forEach(row => {
        row.addEventListener('dblclick', (e) => {
            // Don't trigger on checkbox or button clicks
            if (e.target.type === 'checkbox' || e.target.tagName === 'BUTTON') return;
            const sheetId = row.getAttribute('data-sheet-id');
            editSheet(sheetId);
        });
    });
    
    // Setup checkbox listeners
    setupCheckboxListeners();
}

function renderStatusBadge(status, lastUpdated) {
    if (!status || status === 'idle') {
        return '<span class="status-badge idle">Never run</span>';
    }
    
    let badgeClass = status;
    let badgeText = status.charAt(0).toUpperCase() + status.slice(1);
    
    if (status === 'complete' && lastUpdated) {
        const timeAgo = getTimeAgo(lastUpdated);
        return `
            <div>
                <span class="status-badge complete">${badgeText}</span>
                <span class="status-time">${timeAgo}</span>
            </div>
        `;
    }
    
    return `<span class="status-badge ${badgeClass}">${badgeText}</span>`;
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const updated = timestamp instanceof Date ? timestamp : new Date(timestamp);
    const diffMs = now - updated;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return updated.toLocaleDateString();
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
        
        console.log('Saving sheet:', { name, url, worksheet, user: user.uid });
        
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
            const docRef = window.firebase.doc(db, 'user_sheets', currentEditingSheetId);
            await window.firebase.updateDoc(docRef, sheetData);
            console.log('Sheet updated:', currentEditingSheetId);
            showToast('Sheet updated successfully!', 'success');
        } else {
            // Create new
            sheetData.created_at = new Date();
            const docRef = await window.firebase.addDoc(
                window.firebase.collection(db, 'user_sheets'), 
                sheetData
            );
            console.log('Sheet created:', docRef.id);
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
// CHECKBOX & DELETE FUNCTIONALITY
// ========================================

function setupCheckboxListeners() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const sheetCheckboxes = document.querySelectorAll('.sheet-checkbox');
    const tableActions = document.getElementById('tableActions');
    
    // Select all functionality
    selectAllCheckbox.addEventListener('change', () => {
        sheetCheckboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
        updateTableActionsVisibility();
    });
    
    // Individual checkbox changes
    sheetCheckboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            const allChecked = Array.from(sheetCheckboxes).every(c => c.checked);
            const someChecked = Array.from(sheetCheckboxes).some(c => c.checked);
            selectAllCheckbox.checked = allChecked;
            selectAllCheckbox.indeterminate = someChecked && !allChecked;
            updateTableActionsVisibility();
        });
    });
}

function updateTableActionsVisibility() {
    const checkedBoxes = document.querySelectorAll('.sheet-checkbox:checked');
    const tableActions = document.getElementById('tableActions');
    tableActions.style.display = checkedBoxes.length > 0 ? 'flex' : 'none';
}

async function deleteSelected() {
    const checkedBoxes = document.querySelectorAll('.sheet-checkbox:checked');
    const sheetIds = Array.from(checkedBoxes).map(cb => cb.getAttribute('data-sheet-id'));
    
    if (sheetIds.length === 0) return;
    
    const confirmed = confirm(`Delete ${sheetIds.length} sheet${sheetIds.length > 1 ? 's' : ''}?`);
    if (!confirmed) return;
    
    try {
        const db = window.firebaseDB;
        
        // Delete all selected sheets
        for (const sheetId of sheetIds) {
            await window.firebase.deleteDoc(window.firebase.doc(db, 'user_sheets', sheetId));
        }
        
        showToast(`Deleted ${sheetIds.length} sheet${sheetIds.length > 1 ? 's' : ''}`, 'success');
        
        // Reload sheets
        await loadSheets();
        
        // Reset checkboxes
        document.getElementById('selectAll').checked = false;
        updateTableActionsVisibility();
        
    } catch (error) {
        console.error('Delete error:', error);
        showToast(`Failed to delete: ${error.message}`, 'error');
    }
}

// ========================================
// RUN UPDATE
// ========================================

async function updateSheetStatus(sheetId, status, lastUpdated = new Date()) {
    try {
        const db = window.firebaseDB;
        const docRef = window.firebase.doc(db, 'user_sheets', sheetId);
        
        await window.firebase.updateDoc(docRef, {
            status: status,
            last_updated: lastUpdated
        });
        
        console.log(`Updated status for ${sheetId}: ${status}`);
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

async function runUpdate(sheetId) {
    const btn = document.getElementById(`run-${sheetId}`);
    if (!btn || btn.disabled) return;
    
    try {
        // Disable button
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
        
        // Set status to PENDING
        await updateSheetStatus(sheetId, 'pending');
        await loadSheets(); // Refresh to show PENDING badge
        
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
            // Set status to COMPLETE with timestamp
            await updateSheetStatus(sheetId, 'complete', new Date());
            showToast(`${sheet.name} updated successfully!`, 'success');
        } else {
            // Set status to ERROR
            await updateSheetStatus(sheetId, 'error', new Date());
            throw new Error(data.message || 'Update failed');
        }
        
    } catch (error) {
        console.error('Update error:', error);
        // Set status to ERROR
        await updateSheetStatus(sheetId, 'error', new Date());
        showToast(`Update failed: ${error.message}`, 'error');
    } finally {
        // Reload to show updated status
        await loadSheets();
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
        console.log('ID Token retrieved:', idToken ? 'Yes' : 'No');
        
        if (!idToken) {
            throw new Error('Not authenticated - please refresh and sign in again');
        }
        
        const response = await fetch('/api/oauth-start', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${idToken}`
            }
        });
        
        console.log('OAuth start response status:', response.status);
        
        const data = await response.json();
        console.log('OAuth start response data:', data);
        
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
            throw new Error(data.message || 'Failed to start OAuth');
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

// Make functions globally accessible for onclick handlers
window.runUpdate = runUpdate;
window.deleteSelected = deleteSelected;
window.showAddSheetModal = showAddSheetModal;
window.editSheet = editSheet;

// OAuth callback listener
window.addEventListener('message', async (event) => {
    if (event.data.type === 'oauth_success') {
        showToast('✓ Google Sheets connected successfully!', 'success');
    } else if (event.data.type === 'oauth_error') {
        showToast(`OAuth failed: ${event.data.message}`, 'error');
    }
});


