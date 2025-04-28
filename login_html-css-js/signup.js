document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const firstName = document.querySelector('input[name="first_name"]').value.trim();
            const lastName = document.querySelector('input[name="last_name"]').value.trim();
            const password = document.querySelector('input[name="password"]').value.trim();
            const confirmPassword = document.querySelector('input[name="confirm_password"]').value.trim();
            const birthdate = document.querySelector('input[name="Birthdate"]').value;
            const userId = Date.now().toString();
            const userType = document.querySelector('select[name="userType"]').value;
            let accessCode = '';
            if (userType === 'admin') {
                accessCode = document.querySelector('input[name="adminAccessCode"]').value.trim();
                if (accessCode !== 'KFS2025') {
                    alert('access code is incorrect');
                    return;
                }
            } else if (userType === 'instructor') {
                accessCode = document.querySelector('input[name="instructorAccessCode"]').value.trim();
                if (accessCode !== 'INS2025') {
                    alert('instructor access code is incorrect');
                    return;
                }
            }
            if (!firstName || !lastName || !password || !confirmPassword || !birthdate || !userType) {
                alert('Please fill all fields');
                return;
            }
            if (password !== confirmPassword) {
                alert('Passwords do not match');
                return;
            }
            const userData = {
                id: userId,
                firstName,
                lastName,
                username: firstName + ' ' + lastName,
                password,
                birthdate,
                userType,
                createdAt: new Date().toISOString()
            };
            // Store all users in an array in localStorage
            const users = JSON.parse(localStorage.getItem('users') || '[]');
            users.push(userData);
            localStorage.setItem('users', JSON.stringify(users));
            alert('User registered successfully!');
            signupForm.reset();
        });
    }

    // Show/hide password logic
    const showPasswordCheckboxes = document.querySelectorAll('.show-password-checkbox');
    showPasswordCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const passwordInput = this.closest('label').previousElementSibling.querySelector('input[type="password"], input[type="text"]');
            if (passwordInput) {
                passwordInput.type = this.checked ? 'text' : 'password';
            }
        });
    });
});