/**
 * Accessibility enhancements for the E-Platform
 * Improves keyboard navigation and focus management
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize keyboard navigation for interactive elements
    initializeKeyboardNavigation();
    
    // Initialize focus trap for modal dialogs
    initializeFocusTraps();
    
    // Add skip to content link
    addSkipToContentLink();
});

/**
 * Improves keyboard navigation for interactive elements
 */
function initializeKeyboardNavigation() {
    // Make post actions keyboard accessible
    const actionButtons = document.querySelectorAll('.post-actions button');
    
    actionButtons.forEach(button => {
        // Ensure all buttons have proper tabindex
        if (!button.hasAttribute('tabindex')) {
            button.setAttribute('tabindex', '0');
        }
        
        // Add keyboard event listeners
        button.addEventListener('keydown', function(e) {
            // Enter or Space key
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });
    
    // Hamburger menu keyboard accessibility moved to home.js for consolidation
    // const hamburgerBtn = document.getElementById('hamburger-btn');
    // if (hamburgerBtn) {
    //     hamburgerBtn.addEventListener('keydown', function(e) {
    //         if (e.key === 'Enter' || e.key === ' ') {
    //             e.preventDefault();
    //             this.click();
    //             
    //             // Update aria-expanded state
    //             const expanded = this.getAttribute('aria-expanded') === 'true';
    //             this.setAttribute('aria-expanded', !expanded);
    //         }
    //     });
    // }
    
    // Make sidebar links keyboard accessible
    const sidebarLinks = document.querySelectorAll('.side_nav a');
    sidebarLinks.forEach(link => {
        link.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.click();
            }
        });
    });
}

/**
 * Initializes focus traps for modal dialogs
 * Keeps focus within modal when open
 */
function initializeFocusTraps() {
    // This will be used when modals are implemented
    // For now, it's a placeholder for future implementation
    
    // Example implementation:
    // const modals = document.querySelectorAll('.modal');
    // modals.forEach(modal => {
    //     const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    //     const firstElement = focusableElements[0];
    //     const lastElement = focusableElements[focusableElements.length - 1];
    //     
    //     modal.addEventListener('keydown', function(e) {
    //         if (e.key === 'Tab') {
    //             if (e.shiftKey && document.activeElement === firstElement) {
    //                 e.preventDefault();
    //                 lastElement.focus();
    //             } else if (!e.shiftKey && document.activeElement === lastElement) {
    //                 e.preventDefault();
    //                 firstElement.focus();
    //             }
    //         }
    //     });
    // });
}

/**
 * Adds a skip to content link for keyboard users
 * Allows keyboard users to skip navigation and go directly to main content
 */
function addSkipToContentLink() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to content';
    skipLink.classList.add('skip-link');
    document.body.prepend(skipLink);
    
    // Add id to main content area
    const mainContent = document.querySelector('.main-content-area');
    if (mainContent) {
        mainContent.id = 'main-content';
        mainContent.setAttribute('tabindex', '-1'); // Makes it focusable but not in tab order
    }
}
