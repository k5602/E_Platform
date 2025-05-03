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

        // Clear any previous error messages
        const existingErrors = document.querySelectorAll('.field-error');
        existingErrors.forEach(error => error.remove());

        let hasErrors = false;

        if (!username) {
            e.preventDefault();
            hasErrors = true;
            displayFieldError(usernameInput, 'Username is required');
        }

        if (!password) {
            e.preventDefault();
            hasErrors = true;
            displayFieldError(passwordInput, 'Password is required');
        }

        if (hasErrors) {
            return false;
        }
    });

    // Function to display field-specific errors
    function displayFieldError(field, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error alert alert-danger';
        errorDiv.textContent = message;

        // Insert error after the field
        field.parentNode.insertBefore(errorDiv, field.nextSibling);

        // Add error class to the input
        field.classList.add('input-error');

        // Remove error when field is focused
        field.addEventListener('focus', function() {
            const error = this.parentNode.querySelector('.field-error');
            if (error) {
                error.remove();
            }
            this.classList.remove('input-error');
        }, { once: true });
    }

    // Show/hide password logic with eye icon
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function () {
            // Find the closest password-wrapper parent and then find the input inside it
            const passwordWrapper = this.closest('.password-wrapper');
            if (passwordWrapper) {
                const passwordInput = passwordWrapper.querySelector('input[type="password"], input[type="text"]');
                if (passwordInput) {
                    // Toggle password visibility
                    const isVisible = passwordInput.type === 'text';
                    passwordInput.type = isVisible ? 'password' : 'text';

                    // Toggle the password-visible class for styling
                    passwordWrapper.classList.toggle('password-visible', !isVisible);
                }
            }
        });
    });
});
