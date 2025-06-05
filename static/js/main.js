/* News02 Main JavaScript */

// Global variables
let generationStatusInterval = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize theme system
    loadTheme();
    setupThemeListener();
    
    // Only check generation status if we're actively generating (not on page reload)
    const isActiveGeneration = sessionStorage.getItem('news02_generation_active') === 'true';
    if (isActiveGeneration) {
        checkGenerationStatus();
    }
});

// Generation functions
function startGeneration() {
    if (confirm('Start generating a new news digest? This may take several minutes.')) {
        const btn = document.getElementById('generateBtn');
        if (btn) {
            btn.innerHTML = '<i class="bi bi-arrow-repeat spinning"></i> Starting...';
            btn.disabled = true;
        }
        
        // Mark that we're starting an active generation
        sessionStorage.setItem('news02_generation_active', 'true');
        
        fetch('/api/generate_digest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Digest generation started!', 'info');
                startStatusUpdates();
            } else {
                showAlert('Failed to start generation: ' + data.error, 'danger');
                resetGenerateButton();
                sessionStorage.removeItem('news02_generation_active');
            }
        })
        .catch(error => {
            showAlert('Error starting generation: ' + error.message, 'danger');
            resetGenerateButton();
            sessionStorage.removeItem('news02_generation_active');
        });
    }
}

function startStatusUpdates() {
    if (generationStatusInterval) {
        clearInterval(generationStatusInterval);
    }
    
    generationStatusInterval = setInterval(checkGenerationStatus, 2000);
    document.getElementById('generationStatus').style.display = 'block';
}

function checkGenerationStatus() {
    fetch('/api/generation_status')
        .then(response => response.json())
        .then(data => {
            updateStatusDisplay(data);
            
            if (!data.running) {
                if (generationStatusInterval) {
                    clearInterval(generationStatusInterval);
                    generationStatusInterval = null;
                    
                    // Clear the active generation flag
                    sessionStorage.removeItem('news02_generation_active');
                    
                    // Only show completion notification if we were actively monitoring
                    setTimeout(() => {
                        document.getElementById('generationStatus').style.display = 'none';
                        resetGenerateButton();
                        
                        if (data.error) {
                            showAlert('Generation failed: ' + data.error, 'danger');
                        } else if (data.result_file) {
                            showAlert('Digest generated successfully!', 'success');
                            showGenerationResult(data.result_file);
                        }
                    }, 2000);
                }
            }
        })
        .catch(error => {
            console.error('Error checking status:', error);
        });
}

function updateStatusDisplay(status) {
    const statusEl = document.getElementById('generationStatus');
    const stageEl = document.getElementById('statusStage');
    const progressEl = document.getElementById('statusProgress');
    const percentEl = document.getElementById('statusPercent');
    
    if (statusEl && stageEl && progressEl && percentEl) {
        stageEl.textContent = status.stage || 'Initializing';
        progressEl.style.width = (status.progress || 0) + '%';
        percentEl.textContent = (status.progress || 0) + '%';
        
        // Update alert class based on status
        if (status.error) {
            statusEl.className = 'alert alert-danger';
        } else if (status.progress === 100) {
            statusEl.className = 'alert alert-success';
        } else {
            statusEl.className = 'alert alert-info';
        }
    }
}

function resetGenerateButton() {
    const btn = document.getElementById('generateBtn');
    if (btn) {
        btn.innerHTML = '<i class="bi bi-play-circle"></i> Generate Digest';
        btn.disabled = false;
    }
}

function showGenerationResult(resultFile) {
    if (resultFile.digest || resultFile.audio) {
        const resultHtml = `
            <div class="alert alert-success">
                <h5><i class="bi bi-check-circle"></i> Generation Complete!</h5>
                <p>Your news digest has been generated successfully.</p>
                <div class="btn-group" role="group">
                    ${resultFile.digest ? `
                        <a href="/api/download/digest/${resultFile.digest.split('/').pop()}" 
                           class="btn btn-outline-primary">
                            <i class="bi bi-file-text"></i> Download Text
                        </a>
                    ` : ''}
                    ${resultFile.audio ? `
                        <a href="/api/download/audio/${resultFile.audio.split('/').pop()}" 
                           class="btn btn-outline-success">
                            <i class="bi bi-volume-up"></i> Download Audio
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Insert result into page or show in modal
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertAdjacentHTML('afterbegin', resultHtml);
            setTimeout(() => {
                document.querySelector('.alert-success').remove();
            }, 10000);
        }
    }
}

// Utility functions
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showAlert('Failed to copy to clipboard', 'danger');
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Theme toggle system
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

// Load saved theme
function loadTheme() {
    // Check for saved theme preference or default to 'auto'
    const savedTheme = localStorage.getItem('theme');
    let theme = savedTheme;
    
    // If no saved theme, detect system preference
    if (!savedTheme) {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            theme = 'dark';
        } else {
            theme = 'light';
        }
    }
    
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
}

// Update theme toggle icon
function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    const themeToggle = document.getElementById('themeToggle');
    
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.className = 'bi bi-sun-fill';
            if (themeToggle) themeToggle.title = 'Switch to Light Mode';
        } else {
            themeIcon.className = 'bi bi-moon-fill';
            if (themeToggle) themeToggle.title = 'Switch to Dark Mode';
        }
    }
}

// Listen for system theme changes
function setupThemeListener() {
    if (window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addListener(function(e) {
            // Only auto-switch if user hasn't manually set a preference
            if (!localStorage.getItem('theme')) {
                const newTheme = e.matches ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
                updateThemeIcon(newTheme);
            }
        });
    }
}

// Audio player controls
function createAudioPlayer(audioUrl, container) {
    const audioHtml = `
        <div class="audio-player-container">
            <audio controls class="w-100">
                <source src="${audioUrl}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <div class="audio-controls mt-2">
                <button class="btn btn-sm btn-outline-primary" onclick="downloadAudio('${audioUrl}')">
                    <i class="bi bi-download"></i> Download
                </button>
                <button class="btn btn-sm btn-outline-secondary" onclick="shareAudio('${audioUrl}')">
                    <i class="bi bi-share"></i> Share
                </button>
            </div>
        </div>
    `;
    
    if (container) {
        container.innerHTML = audioHtml;
    }
}

function downloadAudio(audioUrl) {
    const a = document.createElement('a');
    a.href = audioUrl;
    a.download = audioUrl.split('/').pop();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function shareAudio(audioUrl) {
    if (navigator.share) {
        navigator.share({
            title: 'News Digest Audio',
            url: audioUrl
        });
    } else {
        copyToClipboard(window.location.origin + audioUrl);
    }
}

// Form validation helpers
function validateUrl(url) {
    try {
        new URL(url);
        return url.startsWith('http://') || url.startsWith('https://');
    } catch {
        return false;
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.add('is-invalid');
        
        let feedback = field.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.insertBefore(feedback, field.nextSibling);
        }
        feedback.textContent = message;
    }
}

function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.remove('is-invalid');
        const feedback = field.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.remove();
        }
    }
}

// Loading state management
function setLoading(element, loading = true) {
    if (loading) {
        element.classList.add('loading');
        element.disabled = true;
        
        const originalText = element.innerHTML;
        element.setAttribute('data-original-text', originalText);
        element.innerHTML = '<i class="bi bi-arrow-repeat spinning"></i> Loading...';
    } else {
        element.classList.remove('loading');
        element.disabled = false;
        
        const originalText = element.getAttribute('data-original-text');
        if (originalText) {
            element.innerHTML = originalText;
            element.removeAttribute('data-original-text');
        }
    }
}

// Progress tracking
function updateProgress(progressId, percentage, text = '') {
    const progressBar = document.getElementById(progressId);
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
        
        if (text) {
            progressBar.textContent = text;
        }
    }
}

// Auto-refresh functionality
let autoRefreshInterval = null;

function enableAutoRefresh(intervalSeconds = 30) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        // Refresh page data without full reload
        window.location.reload();
    }, intervalSeconds * 1000);
}

function disableAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to start generation
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        startGeneration();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

// Export functions for global use
window.News02 = {
    startGeneration,
    showAlert,
    copyToClipboard,
    validateUrl,
    validateEmail,
    setLoading,
    updateProgress,
    enableAutoRefresh,
    disableAutoRefresh,
    toggleTheme,
    loadTheme,
    updateThemeIcon
};