/**
 * Dark mode toggle functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggle');
    const body = document.body;
    
    // Check if dark mode preference is stored in localStorage
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    
    // Apply dark mode if it was previously enabled
    if (isDarkMode) {
        body.classList.add('darkmode');
    }
    
    // Toggle dark mode when the button is clicked
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            body.classList.toggle('darkmode');
            
            // Store the preference in localStorage
            localStorage.setItem('darkMode', body.classList.contains('darkmode'));
        });
    }
});
