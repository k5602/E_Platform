/**
 * Drag and Drop functionality for chat file uploads
 * Enables intuitive file uploading via drag and drop with visual feedback
 */

// Configuration
const DRAG_DROP_CONFIG = {
    maxFileSize: 5 * 1024 * 1024, // 5MB
    allowedFileTypes: null, // Will be set based on CONFIG.FILE.ALLOWED_TYPES
    dropZoneId: 'drop-zone',
    chatContainerId: 'chat-container',
    fileInputId: 'file-input',
    attachmentPreviewId: 'attachment-preview',
    attachmentPreviewWrapperId: 'attachment-preview-wrapper',
    dragActiveClass: 'active',
    dragOverClass: 'file-over'
};

// State management
const DragDropState = {
    isDragging: false,
    dragCounter: 0,
    currentFile: null,
    isEnabled: true
};

/**
 * Initialize the drag and drop functionality
 */
function initializeDragAndDrop() {
    // Get the main CONFIG from the chat.js if available
    if (window.CONFIG && window.CONFIG.FILE && window.CONFIG.FILE.ALLOWED_TYPES) {
        DRAG_DROP_CONFIG.allowedFileTypes = window.CONFIG.FILE.ALLOWED_TYPES;
    }

    const dropZone = document.getElementById(DRAG_DROP_CONFIG.dropZoneId);
    const chatContainer = document.querySelector('.chat-container');
    const fileInput = document.getElementById(DRAG_DROP_CONFIG.fileInputId);
    const messageForm = document.getElementById('message-form');
    const previewWrapper = document.getElementById(DRAG_DROP_CONFIG.attachmentPreviewWrapperId);

    if (!dropZone || !chatContainer || !fileInput || !messageForm || !previewWrapper) {
        console.error('Required drag and drop elements not found');
        return;
    }

    // Setup drag and drop events on chat container
    setupDragEvents(chatContainer, dropZone);

    // Handle drag events on drop zone
    setupDropZoneEvents(dropZone, fileInput);

    // Expose functionality to global scope for external access
    window.DragDrop = {
        showPreview: showFilePreview,
        clearPreview: clearFilePreview,
        enable: () => { DragDropState.isEnabled = true; },
        disable: () => { DragDropState.isEnabled = false; },
        getCurrentFile: () => DragDropState.currentFile // Expose function to get current file
    };

    console.log('Drag and drop functionality initialized');
}

/**
 * Set up drag events on a container element
 * @param {HTMLElement} container - The container element to watch for drag events
 * @param {HTMLElement} dropZone - The drop zone element
 */
function setupDragEvents(container, dropZone) {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        container.addEventListener(eventName, preventDefaults, false);
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    // Container drag enter/leave tracking
    container.addEventListener('dragenter', handleContainerDragEnter, false);
    container.addEventListener('dragleave', handleContainerDragLeave, false);

    // Handle drops on container
    container.addEventListener('drop', handleContainerDrop, false);

    // Handle paste events for images (for development convenience)
    document.addEventListener('paste', handlePaste, false);
}

/**
 * Set up events specific to the drop zone
 * @param {HTMLElement} dropZone - The drop zone element
 * @param {HTMLElement} fileInput - The file input element
 */
function setupDropZoneEvents(dropZone, fileInput) {
    // Highlight drop zone when item is dragged over it
    dropZone.addEventListener('dragover', function() {
        dropZone.classList.add(DRAG_DROP_CONFIG.dragOverClass);
    });

    dropZone.addEventListener('dragleave', function() {
        dropZone.classList.remove(DRAG_DROP_CONFIG.dragOverClass);
    });

    // Handle drops on the drop zone
    dropZone.addEventListener('drop', function(e) {
        handleDroppedFiles(e.dataTransfer.files);
    });

    // Make drop zone clickable as fallback
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });
}

/**
 * Prevent default drag and drop behaviors
 * @param {Event} e - The event object
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Handle dragenter event on container
 * @param {DragEvent} e - The drag event
 */
function handleContainerDragEnter(e) {
    if (!DragDropState.isEnabled) return;
    
    // Only react to items that have files
    if (!e.dataTransfer.types.includes('Files')) return;

    DragDropState.dragCounter++;
    const dropZone = document.getElementById(DRAG_DROP_CONFIG.dropZoneId);
    
    if (DragDropState.dragCounter === 1) {
        DragDropState.isDragging = true;
        dropZone.classList.add(DRAG_DROP_CONFIG.dragActiveClass);
        
        // Announce for screen readers
        announceForScreenReaders('File drop zone activated. Drop files to send or press Escape to cancel.');
    }
}

/**
 * Handle dragleave event on container
 * @param {DragEvent} e - The drag event
 */
function handleContainerDragLeave(e) {
    if (!DragDropState.isEnabled || !DragDropState.isDragging) return;
    
    DragDropState.dragCounter--;
    
    if (DragDropState.dragCounter === 0) {
        DragDropState.isDragging = false;
        const dropZone = document.getElementById(DRAG_DROP_CONFIG.dropZoneId);
        dropZone.classList.remove(DRAG_DROP_CONFIG.dragActiveClass);
        dropZone.classList.remove(DRAG_DROP_CONFIG.dragOverClass);
        
        // Announce for screen readers
        announceForScreenReaders('File drop zone deactivated.');
    }
}

/**
 * Handle drop event on container
 * @param {DragEvent} e - The drop event
 */
function handleContainerDrop(e) {
    if (!DragDropState.isEnabled) return;
    
    const dropZone = document.getElementById(DRAG_DROP_CONFIG.dropZoneId);
    dropZone.classList.remove(DRAG_DROP_CONFIG.dragActiveClass);
    dropZone.classList.remove(DRAG_DROP_CONFIG.dragOverClass);
    
    DragDropState.isDragging = false;
    DragDropState.dragCounter = 0;
    
    handleDroppedFiles(e.dataTransfer.files);
}

/**
 * Handle dropped files
 * @param {FileList} files - The dropped files
 */
function handleDroppedFiles(files) {
    if (!files || files.length === 0) return;
    
    // Currently we only handle the first file
    const file = files[0];
    
    // Validate the file
    if (!validateFile(file)) return;
    
    // Store the current file
    DragDropState.currentFile = file;
    
    // Show preview
    showFilePreview(file);
    
    // Focus the message input for adding a message with the file
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.focus();
    }
    
    // Announce for screen readers
    announceForScreenReaders(`File ${file.name} selected and ready to send. Type an optional message and press Enter, or Tab to review the attachment.`);
}

/**
 * Handle paste events (for images)
 * @param {ClipboardEvent} e - The paste event
 */
function handlePaste(e) {
    if (!DragDropState.isEnabled) return;
    
    // Check if we're in an input or textarea
    const target = e.target;
    const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
    
    if (!isInInput) {
        // If we're not in an input, we don't want to process this paste
        return;
    }
    
    // Check if there are any images in the clipboard
    const items = e.clipboardData.items;
    
    if (!items) return;
    
    for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
            // Get the image file
            const file = items[i].getAsFile();
            
            // Validate and process the file
            if (validateFile(file)) {
                // Store the current file
                DragDropState.currentFile = file;
                
                // Show preview
                showFilePreview(file);
                
                // Prevent default paste behavior for images
                e.preventDefault();
                break;
            }
        }
    }
}

/**
 * Validate a file before upload
 * @param {File} file - The file to validate
 * @returns {boolean} Whether the file is valid
 */
function validateFile(file) {
    // Check file size
    if (file.size > DRAG_DROP_CONFIG.maxFileSize) {
        const maxSizeMB = DRAG_DROP_CONFIG.maxFileSize / (1024 * 1024);
        showToast(`File size exceeds ${maxSizeMB}MB limit`, 'error');
        return false;
    }
    
    // Check file type if we have restrictions
    if (DRAG_DROP_CONFIG.allowedFileTypes) {
        const allowedTypes = DRAG_DROP_CONFIG.allowedFileTypes.split(',');
        
        // First check MIME type
        const mimeTypeMatch = allowedTypes.some(type => {
            // Handle wildcards like "image/*"
            if (type.endsWith('/*')) {
                const category = type.split('/')[0];
                return file.type.startsWith(category + '/');
            }
            return file.type === type;
        });
        
        // Then check extension
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        const extensionMatch = allowedTypes.some(type => type === fileExtension);
        
        if (!mimeTypeMatch && !extensionMatch) {
            showToast('File type not supported', 'error');
            return false;
        }
    }
    
    return true;
}

/**
 * Show file preview in the UI
 * @param {File} file - The file to preview
 */
function showFilePreview(file) {
    if (!file) return;
    
    const previewWrapper = document.getElementById(DRAG_DROP_CONFIG.attachmentPreviewWrapperId);
    const previewContainer = document.getElementById(DRAG_DROP_CONFIG.attachmentPreviewId);
    
    if (!previewWrapper || !previewContainer) return;
    
    // Clear any existing preview
    previewContainer.innerHTML = '';
    
    // Create preview content based on file type
    const fileType = window.FileUtils ? 
        window.FileUtils.determineFileType(file.type, file.name) : 
        (file.type.startsWith('image/') ? 'image' : 'document');
    
    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    // Create the preview element
    const previewElem = document.createElement('div');
    previewElem.className = 'file-preview';
    
    if (fileType === 'image') {
        // For images, create a thumbnail
        const reader = new FileReader();
        reader.onload = function(e) {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'file-thumbnail-container';
            
            const img = document.createElement('img');
            img.className = 'file-thumbnail';
            img.src = e.target.result;
            img.alt = 'Image preview';
            imgContainer.appendChild(img);
            
            previewElem.appendChild(imgContainer);
            
            // Add file info
            const infoContainer = document.createElement('div');
            infoContainer.className = 'flex-grow';
            
            const fileName = document.createElement('div');
            fileName.className = 'file-info';
            fileName.textContent = file.name;
            infoContainer.appendChild(fileName);
            
            const fileSize = document.createElement('div');
            fileSize.className = 'file-size';
            fileSize.textContent = formatFileSize(file.size);
            infoContainer.appendChild(fileSize);
            
            previewElem.appendChild(infoContainer);
            
            // Add remove button
            addRemoveButton(previewElem);
            
            // Show the preview
            previewContainer.appendChild(previewElem);
            previewWrapper.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    } else {
        // For other file types, show an icon
        const iconContainer = document.createElement('div');
        iconContainer.className = 'file-icon';
        
        const icon = document.createElement('i');
        icon.className = 'fas ' + getFileIconClass(fileType);
        iconContainer.appendChild(icon);
        
        previewElem.appendChild(iconContainer);
        
        // Add file info
        const infoContainer = document.createElement('div');
        infoContainer.className = 'flex-grow';
        
        const fileName = document.createElement('div');
        fileName.className = 'file-info';
        fileName.textContent = file.name;
        infoContainer.appendChild(fileName);
        
        const fileSize = document.createElement('div');
        fileSize.className = 'file-size';
        fileSize.textContent = formatFileSize(file.size);
        infoContainer.appendChild(fileSize);
        
        previewElem.appendChild(infoContainer);
        
        // Add remove button
        addRemoveButton(previewElem);
        
        // Show the preview
        previewContainer.appendChild(previewElem);
        previewWrapper.classList.remove('hidden');
    }
    
    // Update the file input
    updateFileInput(file);
}

/**
 * Get the appropriate Font Awesome icon class for a file type
 * @param {string} fileType - The file type
 * @returns {string} The icon class
 */
function getFileIconClass(fileType) {
    if (window.FileUtils && window.FileUtils.getFileIcon) {
        return window.FileUtils.getFileIcon(fileType);
    }
    
    switch (fileType) {
        case 'image': return 'fa-image';
        case 'audio': return 'fa-music';
        case 'video': return 'fa-video';
        case 'document': return 'fa-file-alt';
        default: return 'fa-file';
    }
}

/**
 * Add a remove button to a preview element
 * @param {HTMLElement} previewElem - The preview element
 */
function addRemoveButton(previewElem) {
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-attachment';
    removeBtn.setAttribute('aria-label', 'Remove attachment');
    removeBtn.setAttribute('type', 'button');
    removeBtn.innerHTML = '<i class="fas fa-times-circle"></i>';
    
    removeBtn.addEventListener('click', function() {
        clearFilePreview();
    });
    
    previewElem.appendChild(removeBtn);
}

/**
 * Clear the file preview
 */
function clearFilePreview() {
    const previewWrapper = document.getElementById(DRAG_DROP_CONFIG.attachmentPreviewWrapperId);
    const previewContainer = document.getElementById(DRAG_DROP_CONFIG.attachmentPreviewId); // Get preview container

    if (previewWrapper) {
        previewWrapper.classList.add('hidden');
    }
    if (previewContainer) { // Clear preview content
        previewContainer.innerHTML = '';
    }
    
    // Clear the stored file
    DragDropState.currentFile = null;
    
    // Reset the main file input as a safety measure, though drag-drop doesn't directly populate it
    const fileInput = document.getElementById(DRAG_DROP_CONFIG.fileInputId);
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Announce for screen readers
    announceForScreenReaders('File attachment removed. Drop zone is active again.');
}

/**
 * Update the file input with the current file
 * @param {File} file - The file to set
 */
function updateFileInput(file) {
    // This is tricky because you can't directly set a file input's value for security reasons
    // We'll need to use the sendFileMessage function if it exists
    if (window.sendFileMessage && DragDropState.currentFile) {
        // The file will be sent when the form is submitted
        // The actual file input update is handled by the form submission logic
    }
}

/**
 * Announce a message for screen readers
 * @param {string} message - The message to announce
 */
function announceForScreenReaders(message) {
    // Create a live region if it doesn't exist
    let liveRegion = document.getElementById('sr-live-region');
    if (!liveRegion) {
        liveRegion = document.createElement('div');
        liveRegion.id = 'sr-live-region';
        liveRegion.className = 'sr-only'; // Use the sr-only class
        liveRegion.setAttribute('aria-live', 'assertive');
        liveRegion.setAttribute('aria-atomic', 'true');
        document.body.appendChild(liveRegion);
    }
    
    // Update the live region
    liveRegion.textContent = message;
    
    // Clear it after a short delay
    setTimeout(() => {
        liveRegion.textContent = '';
    }, 3000);
}

/**
 * Show a toast message
 * @param {string} message - The message to show
 * @param {string} type - The type of toast ('info', 'success', 'warning', 'error')
 */
function showToast(message, type) {
    // Use the existing showToast function if available
    if (window.showToast) {
        window.showToast(message, type);
    } else {
        // Fallback toast implementation
        console.log(`[${type}] ${message}`);
    }
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', initializeDragAndDrop);

// Expose the API globally
window.DragDrop = window.DragDrop || {};