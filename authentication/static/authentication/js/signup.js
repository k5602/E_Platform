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

    // Password strength evaluation
    const passwordInput = document.getElementById('id_password1');
    const strengthMeter = document.getElementById('password-strength-meter');
    const feedbackElement = document.getElementById('password-feedback');

    if (passwordInput && strengthMeter && feedbackElement) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = evaluatePasswordStrength(password);

            // Update the meter value
            strengthMeter.value = strength.score;

            // Update feedback text and class
            feedbackElement.textContent = strength.feedback;
            feedbackElement.className = strength.className;
        });
    }

    /**
     * Evaluates password strength based on various criteria
     * @param {string} password - The password to evaluate
     * @returns {Object} - Object containing score, feedback, and className
     */
    function evaluatePasswordStrength(password) {
        let score = 0;
        let feedback = '';
        let className = '';

        // Check if password is empty
        if (!password) {
            return { score: 0, feedback: '', className: '' };
        }

        // Check length
        if (password.length >= 8) score += 1;
        if (password.length >= 12) score += 1;

        // Check for uppercase letters
        if (/[A-Z]/.test(password)) score += 1;

        // Check for lowercase letters
        if (/[a-z]/.test(password)) score += 1;

        // Check for numbers
        if (/[0-9]/.test(password)) score += 1;

        // Check for special characters
        if (/[^A-Za-z0-9]/.test(password)) score += 1;

        // Provide feedback based on score
        if (score <= 1) {
            feedback = 'Very weak password. Try making it longer with numbers and special characters.';
            className = 'text-danger';
        } else if (score <= 3) {
            feedback = 'Weak password. Add uppercase letters and special characters.';
            className = 'text-danger';
        } else if (score <= 4) {
            feedback = 'Moderate password. Consider making it longer.';
            className = 'text-warning';
        } else if (score === 5) {
            feedback = 'Strong password!';
            className = 'text-success';
        } else {
            feedback = 'Very strong password!';
            className = 'text-success';
        }

        return { score, feedback, className };
    }
});
