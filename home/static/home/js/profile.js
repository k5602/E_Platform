document.addEventListener('DOMContentLoaded', function() {
    // Initialize profile picture upload preview
    initProfilePictureUpload();
    
    // Initialize delete confirmations
    initDeleteConfirmations();
    
    // Initialize form validations
    initFormValidations();
    
    // Initialize drag and drop reordering
    initDragAndDrop();
});

/**
 * Initialize profile picture upload with preview
 */
function initProfilePictureUpload() {
    const profilePictureInput = document.getElementById('id_profile_picture');
    const profilePicturePreview = document.getElementById('profile-picture-preview');
    
    if (profilePictureInput && profilePicturePreview) {
        profilePictureInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    profilePicturePreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

/**
 * Initialize delete confirmations for various profile items
 */
function initDeleteConfirmations() {
    // Get all delete buttons
    const deleteButtons = document.querySelectorAll('.delete-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const itemType = this.dataset.itemType || 'item';
            const confirmMessage = `Are you sure you want to delete this ${itemType}? This action cannot be undone.`;
            
            if (confirm(confirmMessage)) {
                // If confirmed, get the form and submit it
                const form = this.closest('form');
                if (form) {
                    form.submit();
                } else {
                    // If no form, follow the link
                    window.location.href = this.href;
                }
            }
        });
    });
}

/**
 * Initialize form validations
 */
function initFormValidations() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize drag and drop reordering for sortable lists
 */
function initDragAndDrop() {
    const sortableLists = document.querySelectorAll('.sortable-list');
    
    sortableLists.forEach(list => {
        // Check if Sortable library is available
        if (typeof Sortable !== 'undefined') {
            Sortable.create(list, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function(evt) {
                    // Update order after drag and drop
                    updateItemsOrder(list);
                }
            });
        }
    });
}

/**
 * Update the order of items after drag and drop
 * @param {HTMLElement} list - The sortable list element
 */
function updateItemsOrder(list) {
    const items = list.querySelectorAll('.sortable-item');
    const itemType = list.dataset.itemType;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Prepare data for AJAX request
    const orderData = [];
    items.forEach((item, index) => {
        orderData.push({
            id: item.dataset.itemId,
            order: index
        });
    });
    
    // Send AJAX request to update order
    fetch(`/home/profile/${itemType}/reorder/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ items: orderData })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Show success message
            showToast('Order updated successfully', 'success');
        } else {
            // Show error message
            showToast('Failed to update order', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating order:', error);
        showToast('An error occurred while updating order', 'error');
    });
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of toast (success, error, info, warning)
 */
function showToast(message, type = 'info') {
    // Check if toast function exists (from toast.js)
    if (typeof showToastNotification === 'function') {
        showToastNotification(message, type);
    } else {
        // Fallback to alert if toast function is not available
        alert(message);
    }
}

/**
 * Toggle visibility of a section
 * @param {string} sectionId - The ID of the section to toggle
 */
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.toggle('hidden');
        
        // Toggle the icon if exists
        const icon = document.querySelector(`[data-toggle="${sectionId}"] i`);
        if (icon) {
            if (section.classList.contains('hidden')) {
                icon.textContent = 'expand_more';
            } else {
                icon.textContent = 'expand_less';
            }
        }
    }
}

/**
 * Initialize inline editing for profile fields
 */
function initInlineEditing() {
    const editableFields = document.querySelectorAll('.editable-field');
    
    editableFields.forEach(field => {
        const editBtn = field.querySelector('.edit-btn');
        const displayValue = field.querySelector('.display-value');
        const editForm = field.querySelector('.edit-form');
        const cancelBtn = field.querySelector('.cancel-btn');
        
        if (editBtn && displayValue && editForm) {
            // Show edit form when edit button is clicked
            editBtn.addEventListener('click', function() {
                displayValue.classList.add('hidden');
                editForm.classList.remove('hidden');
            });
            
            // Hide edit form when cancel button is clicked
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    displayValue.classList.remove('hidden');
                    editForm.classList.add('hidden');
                });
            }
        }
    });
}
