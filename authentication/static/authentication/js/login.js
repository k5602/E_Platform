document.addEventListener('DOMContentLoaded', () => {
    // This is a modified version of the original login.js
    // Django will handle the authentication, so we only need to keep
    // the client-side validation and UI interactions

    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.querySelector('input[name="username"]');
    const passwordInput = document.querySelector('input[name="password"]');

    // Form validation
    loginForm.addEventListener('submit', (e) => {
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            e.preventDefault();
            alert('Please fill in all fields');
            return false;
        }
    });

    // Show/hide password logic
    const showPasswordCheckbox = document.querySelector('.show-password-checkbox');
    if (showPasswordCheckbox) {
        showPasswordCheckbox.addEventListener('change', function() {
            // Find the closest password-wrapper parent and then find the input inside it
            const passwordWrapper = this.closest('.password-wrapper');
            if (passwordWrapper) {
                const passwordInput = passwordWrapper.querySelector('input[type="password"], input[type="text"]');
                if (passwordInput) {
                    passwordInput.type = this.checked ? 'text' : 'password';
                }
            }
        });
    }
});
