/**
 * Notification Sync
 * 
 * This script synchronizes the notification badges between mobile and desktop views
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize notification sync
    initNotificationSync();
});

/**
 * Initialize notification synchronization between mobile and desktop
 */
function initNotificationSync() {
    // Get notification elements
    const desktopBell = document.getElementById('notification-bell');
    const mobileBell = document.getElementById('notification-bell-mobile');
    const desktopBadge = document.getElementById('notification-badge');
    const mobileBadge = document.getElementById('notification-badge-mobile');
    
    if (!desktopBell || !mobileBell || !desktopBadge || !mobileBadge) {
        console.error('Notification elements not found');
        return;
    }
    
    // Create a MutationObserver to watch for changes to the desktop badge
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' || mutation.type === 'childList') {
                // Sync the mobile badge with the desktop badge
                syncBadges(desktopBadge, mobileBadge);
            }
        });
    });
    
    // Start observing the desktop badge
    observer.observe(desktopBadge, { 
        attributes: true, 
        childList: true,
        characterData: true
    });
    
    // Make mobile bell click trigger the same action as desktop bell
    mobileBell.addEventListener('click', function(event) {
        event.preventDefault();
        // Trigger click on desktop bell
        desktopBell.click();
    });
    
    // Initial sync
    syncBadges(desktopBadge, mobileBadge);
}

/**
 * Synchronize notification badges
 * @param {HTMLElement} source - Source badge element
 * @param {HTMLElement} target - Target badge element
 */
function syncBadges(source, target) {
    // Copy text content
    target.textContent = source.textContent;
    
    // Copy visibility
    if (source.classList.contains('hidden')) {
        target.classList.add('hidden');
    } else {
        target.classList.remove('hidden');
    }
}
