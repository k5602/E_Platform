// Show or hide access code input based on user type selection
    const userTypeSelect = document.querySelector('select[name="userType"]');
    const adminCodeContainer = document.querySelector('.access-code-admin');
    const instructorCodeContainer = document.querySelector('.access-code-instructor');

    function updateAccessCodeVisibility() {
        if (userTypeSelect.value === 'admin') {
            adminCodeContainer.style.display = 'block';
            instructorCodeContainer.style.display = 'none';
        } else if (userTypeSelect.value === 'instructor') {
            adminCodeContainer.style.display = 'none';
            instructorCodeContainer.style.display = 'block';
        } else {
            adminCodeContainer.style.display = 'none';
            instructorCodeContainer.style.display = 'none';
        }
    }

    if (userTypeSelect) {
        userTypeSelect.addEventListener('change', updateAccessCodeVisibility);
        updateAccessCodeVisibility(); // Set initial state
    }