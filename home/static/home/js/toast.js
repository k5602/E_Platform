/**
 * Global Toast Notification System
 */

// Create toast container if it doesn't exist
function createToastContainer() {
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
        
        // Add styles if not already in CSS
        const style = document.createElement('style');
        style.textContent = `
            .toast-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 300px;
            }
            
            .toast {
                padding: 12px 16px;
                border-radius: 4px;
                color: white;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                display: flex;
                align-items: center;
                justify-content: space-between;
                animation: toast-in 0.3s ease-out forwards;
                opacity: 0;
                transform: translateX(50px);
            }
            
            .toast.info {
                background-color: #3498db;
            }
            
            .toast.success {
                background-color: #2ecc71;
            }
            
            .toast.warning {
                background-color: #f39c12;
            }
            
            .toast.error {
                background-color: #e74c3c;
            }
            
            .toast-close {
                background: transparent;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                margin-left: 10px;
                opacity: 0.7;
            }
            
            .toast-close:hover {
                opacity: 1;
            }
            
            @keyframes toast-in {
                0% {
                    opacity: 0;
                    transform: translateX(50px);
                }
                100% {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes toast-out {
                0% {
                    opacity: 1;
                    transform: translateX(0);
                }
                100% {
                    opacity: 0;
                    transform: translateX(50px);
                }
            }
            
            .toast.removing {
                animation: toast-out 0.3s ease-in forwards;
            }
            
            @media (max-width: 768px) {
                .toast-container {
                    top: 10px;
                    right: 10px;
                    left: 10px;
                    max-width: none;
                }
            }
        `;
        document.head.appendChild(style);
    }
    return toastContainer;
}

// Global toast function
window.showToast = function(message, type = 'info') {
    console.log(`Showing toast: ${message} (${type})`);
    
    // Create toast container if it doesn't exist
    const toastContainer = createToastContainer();
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Create toast content
    toast.innerHTML = `
        <span>${message}</span>
        <button class="toast-close">&times;</button>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Add close button functionality
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', function() {
        removeToast(toast);
    });
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        removeToast(toast);
    }, 5000);
    
    // Function to remove toast with animation
    function removeToast(toast) {
        if (!toast.classList.contains('removing')) {
            toast.classList.add('removing');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }
};

// Initialize toast system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Toast notification system initialized');
    createToastContainer();
});
