/**
 * Mention system functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize mention system for all text inputs and textareas
    initializeMentionSystem();

    // Initialize notification bell
    initializeNotificationBell();

    // Format existing mentions in the page
    formatExistingMentions();
});

/**
 * Initialize mention system for text inputs and textareas
 */
function initializeMentionSystem() {
    // Find all textareas and contenteditable elements that should support mentions
    const mentionableElements = document.querySelectorAll('.mentionable');

    console.log('Found mentionable elements:', mentionableElements.length);

    mentionableElements.forEach(element => {
        // Create a mention controller for each element
        console.log('Initializing mention controller for:', element);
        new MentionController(element);
    });

    // Add a mutation observer to detect dynamically added mentionable elements
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        // Check if the node itself is mentionable
                        if (node.classList && node.classList.contains('mentionable')) {
                            console.log('New mentionable element detected:', node);
                            new MentionController(node);
                        }

                        // Check for mentionable elements inside the added node
                        const mentionables = node.querySelectorAll('.mentionable');
                        mentionables.forEach(element => {
                            console.log('New mentionable element detected inside added node:', element);
                            new MentionController(element);
                        });
                    }
                });
            }
        });
    });

    // Start observing the document body for changes
    observer.observe(document.body, { childList: true, subtree: true });
}

/**
 * MentionController class to handle mentions in a text element
 */
class MentionController {
    constructor(element) {
        this.element = element;
        this.dropdown = null;
        this.users = [];
        this.query = '';
        this.selectedIndex = 0;
        this.mentionStart = -1;
        this.active = false;

        this.initEvents();
    }

    /**
     * Initialize events for the mention controller
     */
    initEvents() {
        // Handle input events
        this.element.addEventListener('input', this.handleInput.bind(this));

        // Handle keydown events for navigation
        this.element.addEventListener('keydown', this.handleKeydown.bind(this));

        // Handle blur events to close dropdown
        this.element.addEventListener('blur', (e) => {
            // Delay closing to allow for clicks on dropdown items
            setTimeout(() => {
                this.closeDropdown();
            }, 200);
        });
    }

    /**
     * Handle input events
     */
    handleInput(e) {
        const text = this.element.value || this.element.innerText;
        const caretPos = this.getCaretPosition();

        // Find the @ symbol before the caret
        const beforeCaret = text.substring(0, caretPos);
        const atIndex = beforeCaret.lastIndexOf('@');

        // Debug information
        console.log('Input detected:', {
            text: text,
            caretPos: caretPos,
            atIndex: atIndex,
            beforeCaret: beforeCaret
        });

        // Check if we're in a potential mention (@ exists and is either at the start or preceded by whitespace)
        if (atIndex >= 0 && (atIndex === 0 || /\s/.test(beforeCaret.charAt(atIndex - 1)))) {
            // Extract the query (text between @ and caret)
            this.query = beforeCaret.substring(atIndex + 1);
            this.mentionStart = atIndex;

            console.log('Mention detected:', {
                query: this.query,
                mentionStart: this.mentionStart
            });

            // Always search for users, even with empty query
            this.searchUsers(this.query);
        } else {
            this.closeDropdown();
        }
    }

    /**
     * Handle keydown events for navigation
     */
    handleKeydown(e) {
        // Only handle keys if dropdown is active
        if (!this.active || !this.dropdown) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.users.length - 1);
                this.updateSelectedItem();
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.updateSelectedItem();
                break;

            case 'Enter':
            case 'Tab':
                e.preventDefault();
                this.selectUser(this.users[this.selectedIndex]);
                break;

            case 'Escape':
                e.preventDefault();
                this.closeDropdown();
                break;
        }
    }

    /**
     * Search for users matching the query
     */
    searchUsers(query) {
        console.log('Searching users with query:', query);

        fetch(`/home/api/users/search/?q=${encodeURIComponent(query)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            console.log('Search response status:', response.status);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Search results:', data);
            if (data.status === 'success' && data.users && data.users.length > 0) {
                this.users = data.users;
                this.selectedIndex = 0;
                this.showDropdown();
            } else {
                console.log('No users found or empty response');
                this.closeDropdown();
            }
        })
        .catch(error => {
            console.error('Error searching users:', error);
            this.closeDropdown();
        });
    }

    /**
     * Show the mention dropdown
     */
    showDropdown() {
        // Create dropdown if it doesn't exist
        if (!this.dropdown) {
            this.dropdown = document.createElement('div');
            this.dropdown.className = 'mention-dropdown';
            document.body.appendChild(this.dropdown);
        }

        // Position dropdown below the textarea
        const rect = this.element.getBoundingClientRect();

        // Position dropdown below the textarea
        this.dropdown.style.top = `${window.scrollY + rect.bottom + 5}px`;
        this.dropdown.style.left = `${window.scrollX + rect.left}px`;

        // Make sure dropdown is visible
        this.dropdown.style.zIndex = '9999';

        // Populate dropdown with users
        this.dropdown.innerHTML = this.users.map((user, index) => `
            <div class="mention-dropdown-item ${index === this.selectedIndex ? 'active' : ''}" data-index="${index}">
                <div class="mention-dropdown-item-avatar">${user.first_name.charAt(0)}${user.last_name.charAt(0)}</div>
                <div class="mention-dropdown-item-info">
                    <p class="mention-dropdown-item-name">${user.first_name} ${user.last_name}</p>
                    <p class="mention-dropdown-item-username">@${user.username}</p>
                </div>
                <span class="mention-dropdown-item-type">${user.user_type}</span>
            </div>
        `).join('');

        // Add click event listeners to dropdown items
        const items = this.dropdown.querySelectorAll('.mention-dropdown-item');
        items.forEach(item => {
            item.addEventListener('click', (e) => {
                const index = parseInt(item.dataset.index);
                this.selectUser(this.users[index]);
            });

            item.addEventListener('mouseenter', (e) => {
                this.selectedIndex = parseInt(item.dataset.index);
                this.updateSelectedItem();
            });
        });

        this.active = true;
    }

    /**
     * Close the mention dropdown
     */
    closeDropdown() {
        if (this.dropdown) {
            this.dropdown.remove();
            this.dropdown = null;
        }

        this.active = false;
        this.users = [];
        this.query = '';
        this.mentionStart = -1;
    }

    /**
     * Update the selected item in the dropdown
     */
    updateSelectedItem() {
        if (!this.dropdown) return;

        // Remove active class from all items
        const items = this.dropdown.querySelectorAll('.mention-dropdown-item');
        items.forEach(item => item.classList.remove('active'));

        // Add active class to selected item
        if (items[this.selectedIndex]) {
            items[this.selectedIndex].classList.add('active');

            // Scroll to selected item if needed
            const itemTop = items[this.selectedIndex].offsetTop;
            const itemHeight = items[this.selectedIndex].offsetHeight;
            const dropdownScrollTop = this.dropdown.scrollTop;
            const dropdownHeight = this.dropdown.offsetHeight;

            if (itemTop < dropdownScrollTop) {
                this.dropdown.scrollTop = itemTop;
            } else if (itemTop + itemHeight > dropdownScrollTop + dropdownHeight) {
                this.dropdown.scrollTop = itemTop + itemHeight - dropdownHeight;
            }
        }
    }

    /**
     * Select a user from the dropdown
     */
    selectUser(user) {
        if (!user) return;

        const text = this.element.value || this.element.innerText;
        const beforeMention = text.substring(0, this.mentionStart);
        const afterMention = text.substring(this.getCaretPosition());
        const mention = `@${user.username}`;

        // Replace the @query with @username
        if (this.element.tagName.toLowerCase() === 'textarea' || this.element.tagName.toLowerCase() === 'input') {
            this.element.value = beforeMention + mention + ' ' + afterMention;

            // Set caret position after the mention
            const newCaretPos = this.mentionStart + mention.length + 1;
            this.element.setSelectionRange(newCaretPos, newCaretPos);
        } else {
            // For contenteditable elements
            const range = document.createRange();
            const sel = window.getSelection();

            this.element.innerText = beforeMention + mention + ' ' + afterMention;

            range.setStart(this.element.firstChild, this.mentionStart + mention.length + 1);
            range.collapse(true);

            sel.removeAllRanges();
            sel.addRange(range);
        }

        this.closeDropdown();
        this.element.focus();
    }

    /**
     * Get the current caret position
     */
    getCaretPosition() {
        if (this.element.tagName.toLowerCase() === 'textarea' || this.element.tagName.toLowerCase() === 'input') {
            return this.element.selectionStart;
        } else {
            // For contenteditable elements
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                return range.startOffset;
            }
            return 0;
        }
    }

    /**
     * Get the coordinates of the caret
     */
    getCaretCoordinates() {
        if (this.element.tagName.toLowerCase() === 'textarea' || this.element.tagName.toLowerCase() === 'input') {
            // For input/textarea elements
            const rect = this.element.getBoundingClientRect();
            return {
                top: rect.top,
                left: rect.left
            };
        } else {
            // For contenteditable elements
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0).cloneRange();
                range.collapse(true);

                const rect = range.getClientRects()[0];
                if (rect) {
                    return {
                        top: rect.top,
                        left: rect.left
                    };
                }
            }

            // Fallback to element position
            const rect = this.element.getBoundingClientRect();
            return {
                top: rect.top,
                left: rect.left
            };
        }
    }
}

/**
 * Initialize notification bell
 */
function initializeNotificationBell() {
    // This function is now empty as the notification bell is handled by notification-panel.js
    console.log('Notification bell initialization is now handled by notification-panel.js');
}

// Notification functions have been moved to notification-panel.js

/**
 * Format existing mentions in the page
 */
function formatExistingMentions() {
    // Find all elements with the class 'format-mentions'
    const elements = document.querySelectorAll('.format-mentions');

    elements.forEach(element => {
        // Get the text content
        let content = element.innerHTML;

        // Replace @username with styled mention that links to the user's profile
        content = content.replace(/@(\w+)/g, '<a href="/home/profile/$1/" class="mention" data-username="$1">@$1</a>');

        // Update the element
        element.innerHTML = content;
    });

    // Add click event listeners to all mentions
    document.querySelectorAll('.mention').forEach(mention => {
        mention.addEventListener('click', function(e) {
            // Navigate to the user's profile
            window.location.href = `/home/profile/${this.dataset.username}/`;
        });
    });
}

/**
 * Helper function to get CSRF token
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
