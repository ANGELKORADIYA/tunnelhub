/**
 * TunnelHub - Frontend Application
 * Handles RSA encryption, authentication, tunnel management, and auto-refresh
 */

// ============================================
// Global State
// ============================================

const state = {
    sessionToken: null,
    publicKey: null,
    currentUserFilter: 'all',
    tunnels: [],
    users: [],
    autoRefreshEnabled: true,
    autoRefreshInterval: 5000, // Will be updated from server
    refreshTimer: null,
    countdown: 0
};

// ============================================
// Utility Functions
// ============================================

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMessage = document.getElementById('toastMessage');

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };

    toastIcon.textContent = icons[type] || icons.info;
    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'flex';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

/**
 * Format timestamp for display
 */
function formatTime(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('URL copied to clipboard!', 'success');
    } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('URL copied to clipboard!', 'success');
    }
}

// ============================================
// Authentication Functions
// ============================================

/**
 * Fetch RSA public key from server
 */
async function fetchPublicKey() {
    try {
        const response = await fetch('/api/public-key');
        if (!response.ok) {
            throw new Error('Failed to fetch public key');
        }

        const data = await response.json();
        state.publicKey = data.public_key;
        return data.public_key;
    } catch (error) {
        console.error('Error fetching public key:', error);
        showToast('Failed to initialize security. Please refresh.', 'error');
        return null;
    }
}

/**
 * Encrypt password using RSA public key
 */
function encryptPassword(password) {
    if (!state.publicKey) {
        throw new Error('Public key not loaded');
    }

    const encrypt = new JSEncrypt();
    encrypt.setPublicKey(state.publicKey);
    const encrypted = encrypt.encrypt(password);

    if (!encrypted) {
        throw new Error('Encryption failed');
    }

    return encrypted;
}

/**
 * Login with encrypted password
 */
async function login(password) {
    try {
        // Encrypt password
        const encryptedPassword = encryptPassword(password);

        const response = await fetch('/api/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                encrypted_password: encryptedPassword
            })
        });

        const data = await response.json();

        if (data.success) {
            state.sessionToken = data.session_token;
            localStorage.setItem('sessionToken', data.session_token);
            return true;
        } else {
            return false;
        }
    } catch (error) {
        console.error('Login error:', error);
        return false;
    }
}

/**
 * Logout current session
 */
async function logout() {
    try {
        if (state.sessionToken) {
            await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${state.sessionToken}`
                }
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        state.sessionToken = null;
        localStorage.removeItem('sessionToken');
        showLoginModal();
        stopAutoRefresh();
    }
}

// ============================================
// API Functions
// ============================================

/**
 * Make authenticated API request
 */
async function apiRequest(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (state.sessionToken) {
        headers['Authorization'] = `Bearer ${state.sessionToken}`;
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Session expired
        state.sessionToken = null;
        localStorage.removeItem('sessionToken');
        showLoginModal();
        throw new Error('Session expired');
    }

    return response;
}

/**
 * Fetch tunnels from server
 */
async function fetchTunnels(userFilter = null) {
    try {
        let url = '/api/tunnels';
        if (userFilter && userFilter !== 'all') {
            url += `?user_id=${encodeURIComponent(userFilter)}`;
        }

        const response = await apiRequest(url);
        const data = await response.json();

        if (data.success) {
            state.tunnels = data.tunnels;
            return data.tunnels;
        } else {
            throw new Error('Failed to fetch tunnels');
        }
    } catch (error) {
        console.error('Error fetching tunnels:', error);
        throw error;
    }
}

/**
 * Fetch users from server
 */
async function fetchUsers() {
    try {
        const response = await apiRequest('/api/users');
        const data = await response.json();

        if (data.success) {
            state.users = data.users;
            return data.users;
        }
    } catch (error) {
        console.error('Error fetching users:', error);
    }
    return [];
}

/**
 * Set custom name for tunnel
 */
async function setTunnelName(tunnelId, customName) {
    try {
        const response = await apiRequest(`/api/tunnels/${encodeURIComponent(tunnelId)}/name`, {
            method: 'PUT',
            body: JSON.stringify({ custom_name: customName })
        });

        const data = await response.json();

        if (data.success) {
            showToast('Custom name updated!', 'success');
            await fetchTunnels(state.currentUserFilter);
            renderTunnels();
        } else {
            showToast(data.message || 'Failed to update name', 'error');
        }
    } catch (error) {
        console.error('Error setting tunnel name:', error);
        showToast('Failed to update name', 'error');
    }
}

// ============================================
// UI Functions
// ============================================

/**
 * Show login modal
 */
function showLoginModal() {
    document.getElementById('loginModal').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
}

/**
 * Show dashboard
 */
function showDashboard() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('dashboard').style.display = 'flex';
}

/**
 * Render users in sidebar
 */
function renderUsers() {
    const userList = document.getElementById('userList');
    const userCount = document.getElementById('userCount');

    if (!userList || !userCount) return;

    userCount.textContent = `${state.users.length} users`;

    // Clear existing users (except "All Users")
    const allUsersItem = userList.querySelector('[data-user-id="all"]');
    userList.innerHTML = '';
    if (allUsersItem) {
        userList.appendChild(allUsersItem);
    }

    // Add each user
    state.users.forEach(user => {
        const tunnelCount = state.tunnels.filter(t => t.user_id === user.id).length;

        const userItem = document.createElement('div');
        userItem.className = 'user-item';
        userItem.dataset.userId = user.id;
        userItem.innerHTML = `
            <span class="user-avatar">👤</span>
            <span class="user-name">${user.name}</span>
            <span class="tunnel-count">${tunnelCount}</span>
        `;

        userItem.addEventListener('click', () => {
            filterByUser(user.id);
        });

        userList.appendChild(userItem);
    });

    // Update "All Users" count
    document.getElementById('allTunnelCount').textContent = state.tunnels.length;
}

/**
 * Render tunnel cards
 */
function renderTunnels() {
    const grid = document.getElementById('tunnelsGrid');
    const emptyState = document.getElementById('emptyState');
    const totalTunnels = document.getElementById('totalTunnels');
    const onlineTunnels = document.getElementById('onlineTunnels');
    const lastUpdate = document.getElementById('lastUpdate');

    // Update stats
    if (totalTunnels) totalTunnels.textContent = state.tunnels.length;
    if (onlineTunnels) onlineTunnels.textContent = state.tunnels.filter(t => t.status === 'online').length;
    if (lastUpdate) lastUpdate.textContent = formatTime(new Date().toISOString());

    if (!grid || !emptyState) return;
    const existingCards = Array.from(grid.querySelectorAll('.tunnel-card'));
    const existingCardIds = existingCards.map(card => card.dataset.tunnelId);

    // Get current tunnel IDs from state
    const currentTunnelIds = state.tunnels.map(t => t.id);

    // Remove cards that no longer exist in state
    existingCards.forEach(card => {
        if (!currentTunnelIds.includes(card.dataset.tunnelId)) {
            card.remove();
        }
    });

    // Handle empty state
    if (state.tunnels.length === 0) {
        emptyState.style.display = 'flex';
        return;
    }

    emptyState.style.display = 'none';

    // Update or create tunnel cards
    state.tunnels.forEach(tunnel => {
        let card = grid.querySelector(`.tunnel-card[data-tunnel-id="${tunnel.id}"]`);

        const displayName = tunnel.custom_name || tunnel.public_url;
        const protocol = tunnel.proto.toUpperCase();
        const statusClass = tunnel.status === 'online' ? '' : 'offline';

        if (card) {
            // Update existing card
            card.querySelector('.tunnel-name').textContent = displayName;
            card.querySelector('.tunnel-url').textContent = tunnel.public_url;
            const statusDiv = card.querySelector('.tunnel-status');
            statusDiv.className = `tunnel-status ${statusClass}`;
            statusDiv.innerHTML = `<span class="status-dot"></span>${tunnel.status}`;
        } else {
            // Create new card
            card = document.createElement('div');
            card.className = 'tunnel-card';
            card.dataset.tunnelId = tunnel.id;

            card.innerHTML = `
                <div class="tunnel-header">
                    <div class="tunnel-title">
                        <div class="tunnel-name">${displayName}</div>
                        <div class="tunnel-url">${tunnel.public_url}</div>
                    </div>
                    <div class="tunnel-status ${statusClass}">
                        <span class="status-dot"></span>
                        ${tunnel.status}
                    </div>
                </div>
                <div class="tunnel-info">
                    <div class="tunnel-info-row">
                        <span>🔗</span>
                        <span>${protocol}</span>
                    </div>
                    <div class="tunnel-info-row">
                        <span>📍</span>
                        <span>${tunnel.region}</span>
                    </div>
                    <div class="tunnel-info-row">
                        <span>👤</span>
                        <span>${tunnel.user_name}</span>
                    </div>
                </div>
                <div class="tunnel-actions">
                    <button class="btn btn-primary btn-sm" onclick="copyTunnelUrl('${tunnel.public_url}')">
                        📋 Copy URL
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="openNameModal('${tunnel.id}', '${tunnel.custom_name || ''}')">
                        ✏️ Rename
                    </button>
                    <a href="${tunnel.public_url}" target="_blank" class="btn btn-secondary btn-sm">
                        🔗 Open
                    </a>
                </div>
            `;

            grid.appendChild(card);
        }
    });
}

/**
 * Filter tunnels by user
 */
async function filterByUser(userId) {
    state.currentUserFilter = userId;

    // Update active state in sidebar
    document.querySelectorAll('.user-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.userId === userId) {
            item.classList.add('active');
        }
    });

    // Update header
    const currentView = document.getElementById('currentView');
    if (userId === 'all') {
        currentView.textContent = 'All Tunnels';
    } else {
        const user = state.users.find(u => u.id === userId);
        currentView.textContent = user ? `${user.name}'s Tunnels` : 'Tunnels';
    }

    // Fetch and render filtered tunnels
    await fetchTunnels(userId);
    renderTunnels();
}

/**
 * Copy tunnel URL
 */
function copyTunnelUrl(url) {
    copyToClipboard(url);
}

// ============================================
// Modal Functions
// ============================================

/**
 * Open custom name modal
 */
function openNameModal(tunnelId, currentName) {
    document.getElementById('nameTunnelId').value = tunnelId;
    document.getElementById('customName').value = currentName;
    document.getElementById('nameModal').style.display = 'flex';
    document.getElementById('customName').focus();
}

/**
 * Close custom name modal
 */
function closeNameModal() {
    document.getElementById('nameModal').style.display = 'none';
}

// ============================================
// Auto-Refresh Functions
// ============================================

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
    }

    // Initialize countdown
    state.countdown = state.autoRefreshInterval / 1000;

    // Update UI immediately
    const refreshIntervalEl = document.getElementById('refreshInterval');
    if (refreshIntervalEl) {
        refreshIntervalEl.textContent = `${state.countdown}s`;
    }

    state.refreshTimer = setInterval(async () => {
        if (!state.autoRefreshEnabled || !state.sessionToken) return;

        state.countdown--;

        // Update UI
        if (refreshIntervalEl) {
            refreshIntervalEl.textContent = `${state.countdown}s`;
        }

        if (state.countdown <= 0) {
            // Reset countdown
            state.countdown = state.autoRefreshInterval / 1000;

            // Fetch and render
            await fetchTunnels(state.currentUserFilter);
            renderTunnels();
            renderUsers();

            // Reset UI after fetch
            if (refreshIntervalEl) {
                refreshIntervalEl.textContent = `${state.countdown}s`;
            }
        }
    }, 1000);

    // Update UI
    const toggleBtn = document.getElementById('toggleRefresh');
    if (toggleBtn) toggleBtn.textContent = '⏸️';
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
    }
}

/**
 * Toggle auto-refresh
 */
function toggleAutoRefresh() {
    state.autoRefreshEnabled = !state.autoRefreshEnabled;

    const btn = document.getElementById('toggleRefresh');
    const status = document.getElementById('refreshStatus');

    if (state.autoRefreshEnabled) {
        btn.textContent = '⏸️';
        status.style.opacity = '1';
    } else {
        btn.textContent = '▶️';
        status.style.opacity = '0.5';
    }
}

/**
 * Manual refresh
 */
async function manualRefresh() {
    if (state.sessionToken) {
        await fetchTunnels(state.currentUserFilter);
        renderTunnels();
        renderUsers();
        showToast('Refreshed!', 'success');
    }
}

// ============================================
// Initialization
// ============================================

/**
 * Initialize application
 */
async function init() {
    // Check for existing session
    const existingToken = localStorage.getItem('sessionToken');
    if (existingToken) {
        state.sessionToken = existingToken;
    }

    // Fetch public key
    await fetchPublicKey();

    // If we have a session, try to fetch data
    if (state.sessionToken) {
        try {
            await fetchUsers();
            await fetchTunnels();
            showDashboard();
            renderUsers();
            renderTunnels();
            startAutoRefresh();
        } catch (error) {
            // Session invalid, show login
            showLoginModal();
        }
    } else {
        showLoginModal();
    }
}

// ============================================
// Event Listeners
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    // Get auto-refresh interval from template
    const refreshIntervalEl = document.getElementById('refreshInterval');
    const refreshIntervalFromServer = parseInt(refreshIntervalEl?.dataset.autoRefreshInterval || '5');
    state.autoRefreshInterval = refreshIntervalFromServer * 1000;

    // Initialize app
    await init();

    // Login form
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const password = document.getElementById('password').value;
        const btn = e.target.querySelector('button[type="submit"]');
        const btnText = btn.querySelector('.btn-text');
        const btnLoader = btn.querySelector('.btn-loader');
        const errorMsg = document.getElementById('loginError');

        // Show loading state
        btn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline';
        errorMsg.style.display = 'none';

        try {
            const success = await login(password);

            if (success) {
                // Fetch data and show dashboard
                await fetchUsers();
                await fetchTunnels();
                showDashboard();
                renderUsers();
                renderTunnels();
                startAutoRefresh();
                showToast('Login successful!', 'success');
            } else {
                errorMsg.textContent = 'Invalid password. Please try again.';
                errorMsg.style.display = 'block';
                btn.disabled = false;
                btnText.style.display = 'inline';
                btnLoader.style.display = 'none';
            }
        } catch (error) {
            errorMsg.textContent = 'Login failed. Please try again.';
            errorMsg.style.display = 'block';
            btn.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    });

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', logout);

    // Toggle refresh button
    document.getElementById('toggleRefresh').addEventListener('click', toggleAutoRefresh);

    // Manual refresh button
    document.getElementById('manualRefresh').addEventListener('click', manualRefresh);

    // Custom name form
    document.getElementById('nameForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const tunnelId = document.getElementById('nameTunnelId').value;
        const customName = document.getElementById('customName').value.trim();

        if (customName) {
            await setTunnelName(tunnelId, customName);
            closeNameModal();
        }
    });
});

// Make functions globally available
window.copyTunnelUrl = copyTunnelUrl;
window.openNameModal = openNameModal;
window.closeNameModal = closeNameModal;
