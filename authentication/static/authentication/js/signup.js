document.addEventListener('DOMContentLoaded', function() {
    // This is a modified version of the original signup.js
    // Django will handle the form submission and validation
    // We only need to keep the client-side validation and UI interactions

    const signupForm = document.getElementById('signup-form');

    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            const firstName = document.querySelector('input[name="first_name"]').value.trim();
            const lastName = document.querySelector('input[name="last_name"]').value.trim();
            const password1 = document.querySelector('input[name="password1"]').value.trim();
            const password2 = document.querySelector('input[name="password2"]').value.trim();
            const birthdate = document.querySelector('input[name="birthdate"]').value;
            const userType = document.querySelector('select[name="user_type"]').value;

            if (!firstName || !lastName || !password1 || !password2 || !birthdate || !userType) {
                e.preventDefault();
                alert('Please fill all fields');
                return;
            }

            if (password1 !== password2) {
                e.preventDefault();
                alert('Passwords do not match');
                return;
            }
        });
    }

    // Show/hide password logic
    const showPasswordCheckboxes = document.querySelectorAll('.show-password-checkbox');
    showPasswordCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Find the closest password-wrapper parent and then find the input inside it
            const passwordWrapper = this.closest('.password-wrapper');
            if (passwordWrapper) {
                const passwordInput = passwordWrapper.querySelector('input[type="password"], input[type="text"]');
                if (passwordInput) {
                    passwordInput.type = this.checked ? 'text' : 'password';
                }
            }
        });
    });
});
