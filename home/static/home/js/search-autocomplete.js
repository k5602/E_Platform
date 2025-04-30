document.addEventListener('DOMContentLoaded', function() {
    initializeSearchAutocomplete();
});

function initializeSearchAutocomplete() {
    const searchInput = document.getElementById('search-input');
    const suggestionsContainer = document.getElementById('search-suggestions');

    if (!searchInput || !suggestionsContainer) return;

    let debounceTimer;
    const debounceDelay = 300; // milliseconds

    // Add event listener for input changes
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();

        // Clear previous timer
        clearTimeout(debounceTimer);

        // Hide suggestions if query is too short
        if (query.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        // Set new timer
        debounceTimer = setTimeout(() => {
            fetchSuggestions(query);
        }, debounceDelay);
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });

    // Show suggestions when input is focused
    searchInput.addEventListener('focus', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            fetchSuggestions(query);
        }
    });

    // Function to fetch suggestions from API
    function fetchSuggestions(query) {
        // Log the request URL for debugging
        console.log(`Fetching suggestions for: ${query}`);

        // Try multiple possible URLs for search suggestions
        fetch(`/home/search/suggestions/?q=${encodeURIComponent(query)}`)
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Suggestions data:', data);
                displaySuggestions(data.suggestions);
            })
            .catch(error => {
                console.error('Error fetching suggestions:', error);
            });
    }

    // Function to display suggestions
    function displaySuggestions(suggestions) {
        // Clear previous suggestions
        suggestionsContainer.innerHTML = '';

        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        // Create suggestion elements
        suggestions.forEach(suggestion => {
            const item = document.createElement('a');
            item.href = suggestion.url;
            item.className = 'search-suggestion-item';

            const avatar = document.createElement('img');
            avatar.className = 'suggestion-avatar';
            if (suggestion.profile_pic) {
                avatar.src = suggestion.profile_pic;
            } else {
                avatar.src = '/static/home/images/student.jpeg';
            }
            avatar.alt = suggestion.username;

            const info = document.createElement('div');
            info.className = 'suggestion-info';

            const name = document.createElement('div');
            name.className = 'suggestion-name';
            name.textContent = suggestion.full_name;

            const username = document.createElement('div');
            username.className = 'suggestion-username';
            username.textContent = '@' + suggestion.username;

            const userType = document.createElement('span');
            userType.className = 'suggestion-type';
            userType.textContent = suggestion.user_type;

            info.appendChild(name);
            info.appendChild(username);

            item.appendChild(avatar);
            item.appendChild(info);
            item.appendChild(userType);

            suggestionsContainer.appendChild(item);
        });

        // Show suggestions container
        suggestionsContainer.style.display = 'block';
    }

    // Handle keyboard navigation
    searchInput.addEventListener('keydown', function(e) {
        if (!suggestionsContainer.style.display || suggestionsContainer.style.display === 'none') return;

        const items = suggestionsContainer.querySelectorAll('.search-suggestion-item');
        if (items.length === 0) return;

        const currentIndex = Array.from(items).findIndex(item => item.classList.contains('active'));

        // Arrow down
        if (e.key === 'ArrowDown') {
            e.preventDefault();

            if (currentIndex < 0) {
                // No item selected, select first
                items[0].classList.add('active');
                items[0].focus();
            } else if (currentIndex < items.length - 1) {
                // Select next item
                items[currentIndex].classList.remove('active');
                items[currentIndex + 1].classList.add('active');
                items[currentIndex + 1].focus();
            }
        }

        // Arrow up
        else if (e.key === 'ArrowUp') {
            e.preventDefault();

            if (currentIndex > 0) {
                // Select previous item
                items[currentIndex].classList.remove('active');
                items[currentIndex - 1].classList.add('active');
                items[currentIndex - 1].focus();
            }
        }

        // Enter key
        else if (e.key === 'Enter') {
            const activeItem = suggestionsContainer.querySelector('.search-suggestion-item.active');
            if (activeItem) {
                e.preventDefault();
                window.location.href = activeItem.href;
            }
        }

        // Escape key
        else if (e.key === 'Escape') {
            suggestionsContainer.style.display = 'none';
        }
    });
}
