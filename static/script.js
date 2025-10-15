// Global state
let uploadedFileId = null;
let ws = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    connectWebSocket();
    setupOAuthMessageListener();
});

function setupEventListeners() {
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);
    document.getElementById('connectSheetsBtn').addEventListener('click', connectSheets);
    document.getElementById('saveDefaultsBtn').addEventListener('click', saveDefaults);
    document.getElementById('runUpdateBtn').addEventListener('click', runUpdate);
}

function showStatus(message, type = 'info') {
    const statusBar = document.getElementById('statusBar');
    const statusMessage = document.getElementById('statusMessage');
    const statusIcon = document.getElementById('statusIcon');
    
    const icons = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ️'
    };
    
    statusIcon.textContent = icons[type] || 'ℹ️';
    statusMessage.textContent = message;
    statusBar.className = 'status-bar';
    statusBar.classList.add(type);
    statusBar.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => statusBar.classList.add('hidden'), 5000);
    }
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
    document.getElementById('dropZone').classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById('dropZone').classList.remove('drag-over');
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
    
    showStatus('Uploading credentials...', 'info');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload-credentials', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            uploadedFileId = data.file_id;
            
            const dropContent = document.getElementById('dropContent');
            const fileInfo = document.getElementById('fileInfo');
            
            document.getElementById('fileName').textContent = `✓ ${file.name}`;
            dropContent.classList.add('hidden');
            fileInfo.classList.remove('hidden');
            document.getElementById('connectSheetsBtn').disabled = false;
            
            showStatus('✓ Credentials uploaded successfully', 'success');
        }
    } catch (error) {
        showStatus('Upload failed: ' + error.message, 'error');
    }
}

function clearFile() {
    uploadedFileId = null;
    document.getElementById('dropContent').classList.remove('hidden');
    document.getElementById('fileInfo').classList.add('hidden');
    document.getElementById('connectSheetsBtn').disabled = true;
    document.getElementById('fileInput').value = '';
}

// Setup listener for OAuth popup messages
function setupOAuthMessageListener() {
    window.addEventListener('message', (event) => {
        // Security: only accept messages from same origin
        if (event.origin !== window.location.origin) {
            return;
        }
        
        if (event.data.type === 'oauth-success') {
            showStatus('✓ Successfully connected to Google Sheets!', 'success');
        } else if (event.data.type === 'oauth-error') {
            showStatus('Connection failed: ' + event.data.error, 'error');
        }
    });
}

async function connectSheets() {
    if (!uploadedFileId) {
        showStatus('Please upload credentials first', 'error');
        return;
    }
    
    showStatus('Opening Google authentication...', 'info');
    
    try {
        // Get the OAuth URL from the server
        const response = await fetch(`/api/oauth-start?file_id=${uploadedFileId}`);
        const data = await response.json();
        
        if (data.success && data.authorization_url) {
            // Open OAuth URL in a popup
            const width = 600;
            const height = 700;
            const left = (screen.width - width) / 2;
            const top = (screen.height - height) / 2;
            
            const popup = window.open(
                data.authorization_url,
                'Google Authentication',
                `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
            );
            
            if (!popup) {
                showStatus('Popup blocked! Please allow popups for this site.', 'error');
            } else {
                showStatus('Complete authentication in the popup window...', 'info');
            }
        } else {
            showStatus('Failed to start authentication', 'error');
        }
    } catch (error) {
        showStatus('Connection failed: ' + error.message, 'error');
    }
}

async function saveDefaults() {
    const spreadsheet = document.getElementById('spreadsheetUrl').value.trim();
    const worksheet = document.getElementById('worksheetName').value.trim();
    
    if (!spreadsheet || !worksheet) {
        showStatus('Please enter both spreadsheet URL and worksheet name', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('spreadsheet', spreadsheet);
        formData.append('worksheet', worksheet);
        
        const response = await fetch('/api/set-defaults', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            showStatus('✓ Defaults saved successfully', 'success');
        }
    } catch (error) {
        showStatus('Failed to save defaults: ' + error.message, 'error');
    }
}

async function runUpdate() {
    const spreadsheet = document.getElementById('spreadsheetUrl').value.trim();
    const worksheet = document.getElementById('worksheetName').value.trim();
    const disableColumns = document.getElementById('disableColumns').value.trim();
    const rowRange = document.getElementById('rowRange').value.trim();
    const override = document.getElementById('overrideData').checked;
    
    const btnRun = document.getElementById('runUpdateBtn');
    const btnText = document.getElementById('runBtnText');
    const btnSpinner = document.getElementById('runBtnSpinner');
    
    btnRun.disabled = true;
    btnText.classList.add('hidden');
    btnSpinner.classList.remove('hidden');
    showStatus('⏳ Update in progress...', 'info');
    
    try {
        const formData = new FormData();
        if (spreadsheet) formData.append('spreadsheet', spreadsheet);
        if (worksheet) formData.append('worksheet', worksheet);
        if (uploadedFileId) formData.append('file_id', uploadedFileId);
        if (disableColumns) formData.append('disable_columns', disableColumns);
        formData.append('override', override);
        
        if (rowRange) {
            const parts = rowRange.split(':');
            if (parts.length === 2) {
                formData.append('start_row', parseInt(parts[0]));
                formData.append('end_row', parseInt(parts[1]));
            }
        }
        
        const response = await fetch('/api/update-sheets', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            showStatus('✓ Sheet updated successfully!', 'success');
        } else {
            showStatus('Update failed', 'error');
        }
    } catch (error) {
        showStatus('✗ Update failed: ' + error.message, 'error');
    } finally {
        btnRun.disabled = false;
        btnText.classList.remove('hidden');
        btnSpinner.classList.add('hidden');
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = protocol + '//' + window.location.host + '/ws';
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onclose = () => {
        setTimeout(connectWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
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
