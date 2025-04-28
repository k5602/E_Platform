const validCredentials = {
    username: 'admin',
    password: 'admin123'
};

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.querySelector('input[name="username"]');
    const passwordInput = document.querySelector('input[name="password"]');
    const rememberCheckbox = document.getElementById('remember-checkbox');

    const lastRegisteredUser = JSON.parse(sessionStorage.getItem('lastRegisteredUser') || '{}');
    if (lastRegisteredUser.username) {
        usernameInput.value = lastRegisteredUser.username;
        passwordInput.value = lastRegisteredUser.password;
        sessionStorage.removeItem('lastRegisteredUser');
    }

    if (localStorage.getItem('saved_username')) {
        usernameInput.value = localStorage.getItem('saved_username');
        passwordInput.value = localStorage.getItem('saved_password');
        rememberCheckbox.checked = true;
    }

    loginForm.onsubmit = (e) => {
        e.preventDefault();

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            alert('pleease fill in all fields');
            return false;
        }

        //search for the user in local storage
        const users = [];
        for (let i = 0; i < localStorage.length; i++) {
            try {
                const user = JSON.parse(localStorage.getItem(localStorage.key(i)));
                if (user && user.username && user.password) {
                    users.push(user);
                }
            } catch {}
        }

        const user = users.find(u => (u.username === username || u.id === username) && u.password === password);

        if (user) {
            if (rememberCheckbox.checked) {
                localStorage.setItem('saved_username', username);
                localStorage.setItem('saved_password', password);
            } else {
                localStorage.removeItem('saved_username');
                localStorage.removeItem('saved_password');
            }

            localStorage.setItem('currentUser', JSON.stringify({
                id: user.id,
                name: user.firstName + ' ' + user.lastName,
                type: user.userType
            }));

            // instructor and admin redirect to the quiz page
            // student redirect to the home page
            if (user.userType === 'admin') {
                window.location.href = '../quiz.html';
            } else if (user.userType === 'instructor') {
                window.location.href = '../home/home.html';
            } else {
                window.location.href = '../home/home.html';
            }
        } else {
            alert('invalid username or password');
        }

        return false;
    };
});