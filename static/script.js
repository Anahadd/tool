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
    
    // Service Account Info Page
    const copyEmailBtn = document.getElementById('copyEmailBtn');
    if (copyEmailBtn) {
        copyEmailBtn.addEventListener('click', copyServiceAccountEmail);
    }
    
    const continueBtn = document.getElementById('continueBtn');
    if (continueBtn) {
        continueBtn.addEventListener('click', () => {
            document.getElementById('credentialsSetupPage').classList.add('hidden');
            document.getElementById('adminDashboard').classList.remove('hidden');
            loadSheets();
        });
    }
    
    // Dashboard buttons
    const addSheetBtn = document.getElementById('addSheetBtn');
    if (addSheetBtn) {
        addSheetBtn.addEventListener('click', showAddSheetModal);
    }
    
    const howToUseBtn = document.getElementById('howToUseBtn');
    if (howToUseBtn) {
        howToUseBtn.addEventListener('click', showSettingsModal);
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
    
    // How To Use Modal
    const closeHowToUseBtn = document.getElementById('closeHowToUseModalBtn');
    if (closeHowToUseBtn) {
        closeHowToUseBtn.addEventListener('click', closeHowToUseModal);
    }
    
    const copyEmailHowToUseBtn = document.getElementById('copyEmailSettingsBtn');
    if (copyEmailHowToUseBtn) {
        copyEmailHowToUseBtn.addEventListener('click', copyServiceAccountEmail);
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
    
    // Check if user is new (no sheets saved) or returning
    try {
        const db = window.firebaseDB;
        const sheetsRef = window.firebase.collection(db, 'user_sheets');
        const q = window.firebase.query(
            sheetsRef, 
            window.firebase.where('user_id', '==', user.uid)
        );
        const querySnapshot = await window.firebase.getDocs(q);
        
        if (querySnapshot.empty) {
            // First time user - show service account info page
            document.getElementById('authPage').classList.add('hidden');
            document.getElementById('credentialsSetupPage').classList.remove('hidden');
            document.getElementById('adminDashboard').classList.add('hidden');
            showToast('Welcome! Please share your Google Sheet with our service account.', 'info');
        } else {
            // Returning user - go straight to dashboard
            document.getElementById('authPage').classList.add('hidden');
            document.getElementById('credentialsSetupPage').classList.add('hidden');
            document.getElementById('adminDashboard').classList.remove('hidden');
            
            showToast(`Welcome back, ${user.email}!`, 'success');
            
            // Load user's sheets
            await loadSheets();
        }
    } catch (error) {
        console.error('Error checking sheets:', error);
        // On error, just show the info page to be safe
        document.getElementById('authPage').classList.add('hidden');
        document.getElementById('credentialsSetupPage').classList.remove('hidden');
        document.getElementById('adminDashboard').classList.add('hidden');
    }
}

// ========================================
// CREDENTIALS SETUP PAGE
// ========================================

// No setup files needed anymore - using shared service account!

// OAuth functions removed - using shared service account instead!

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
                <input type="checkbox" class="sheet-checkbox" data-sheet-id="${sheet.id}">
            </td>
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
        
        showToast(`⏳ Processing ${sheet.name}... This may take several minutes for large sheets. The update will continue even if your browser times out.`, 'info');
        
        // Get ID token for API auth
        const idToken = await window.firebase.getIdToken();
        
        const formData = new FormData();
        formData.append('spreadsheet', sheet.spreadsheet_url);
        formData.append('worksheet', sheet.worksheet_name);
        formData.append('override', 'true');
        
        // Create AbortController with a very long timeout (30 minutes)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30 * 60 * 1000);
        
        try {
            const response = await fetch('/api/update-sheets', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${idToken}`
                },
                body: formData,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            // Handle 502 Bad Gateway (server crashed) or 504 Gateway Timeout
            if (response.status === 502 || response.status === 504) {
                const isTimeout = response.status === 504;
                const message = isTimeout 
                    ? `⏱️ Update timed out for ${sheet.name}. For large sheets (1000+ URLs), try processing in smaller batches using row ranges. Partial data may have been updated.`
                    : `⚠️ Server became overloaded processing ${sheet.name}. For large sheets (1000+ URLs), try processing in batches using row ranges. Partial data may have been updated.`;
                
                showToast(message, 'error');
                await updateSheetStatus(sheetId, 'error', new Date());
                await loadSheets();
                return;
            }
            
            // Handle other non-200 status codes
            if (!response.ok && response.status !== 200) {
                let errorMessage = `Server error (${response.status})`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorMessage;
                } catch {
                    // If can't parse JSON, use default message
                }
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Set status to COMPLETE with timestamp
                await updateSheetStatus(sheetId, 'complete', new Date());
                showToast(`✅ ${sheet.name} updated successfully!`, 'success');
            } else {
                // Set status to ERROR
                await updateSheetStatus(sheetId, 'error', new Date());
                throw new Error(data.message || 'Update failed');
            }
        } catch (fetchError) {
            clearTimeout(timeoutId);
            
            // Check if it's a network timeout/protocol error
            if (fetchError.name === 'AbortError' || 
                fetchError.message.includes('Failed to fetch') || 
                fetchError.message.includes('NetworkError')) {
                
                // The connection timed out, but the server is still processing
                showToast(`⚠️ Connection timed out, but ${sheet.name} is still being processed on the server. Check back in a few minutes and refresh the page.`, 'info');
                
                // Keep status as PENDING instead of ERROR
                await updateSheetStatus(sheetId, 'pending');
                await loadSheets();
                return; // Don't throw error
            }
            
            // For other errors, rethrow
            throw fetchError;
        }
        
    } catch (error) {
        console.error('Update error:', error);
        // Set status to ERROR only for real errors
        await updateSheetStatus(sheetId, 'error', new Date());
        showToast(`❌ Update failed: ${error.message}`, 'error');
    } finally {
        // Reload to show updated status
        await loadSheets();
    }
}

// ========================================
// SETTINGS & CREDENTIALS
// ========================================

function showSettingsModal() {
    document.getElementById('howToUseModal').classList.remove('hidden');
}

function closeHowToUseModal() {
    document.getElementById('howToUseModal').classList.add('hidden');
}

// Service account email (no credentials needed!)
const SERVICE_ACCOUNT_EMAIL = 'kalshitoolsalman@gen-lang-client-0071269503.iam.gserviceaccount.com';

async function copyServiceAccountEmail() {
    try {
        await navigator.clipboard.writeText(SERVICE_ACCOUNT_EMAIL);
        showToast('Email copied to clipboard!', 'success');
        console.log('SERVICE ACCOUNT EMAIL:', SERVICE_ACCOUNT_EMAIL);
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showToast('Failed to copy. Check console for email.', 'error');
        console.log('='.repeat(60));
        console.log('SERVICE ACCOUNT EMAIL (copy this):');
        console.log(SERVICE_ACCOUNT_EMAIL);
        console.log('='.repeat(60));
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
        'success': '',
        'error': '',
        'info': ''
    };
    
    toast.className = `status-toast ${type}`;
    icon.textContent = icons[type] || '';
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
        showToast('Google Sheets connected successfully!', 'success');
    } else if (event.data.type === 'oauth_error') {
        showToast(`OAuth failed: ${event.data.message}`, 'error');
    }
});


