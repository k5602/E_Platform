/**
 * File utilities for chat application
 */

/**
 * Determine the file type category based on MIME type and extension
 * @param {string} mimeType - The MIME type of the file
 * @param {string} [filename] - Optional filename for fallback detection
 * @returns {string} The file type category ('image', 'audio', 'video', 'document', or 'other')
 */
function determineFileType(mimeType, filename = '') {
    // Default file type
    let fileType = 'other';
    
    // First try using the MIME type
    if (mimeType) {
        const lowerMimeType = mimeType.toLowerCase();
        
        if (lowerMimeType.startsWith('image/')) {
            return 'image';
        }
        if (lowerMimeType.startsWith('audio/')) {
            return 'audio';
        }
        if (lowerMimeType.startsWith('video/')) {
            return 'video';
        }
        if (lowerMimeType.startsWith('application/') || lowerMimeType.startsWith('text/')) {
            // Text and application types are generally documents
            fileType = 'document';
        }
    }
    
    // If we have a filename and didn't conclusively determine the type, check extension
    if (filename && fileType === 'other') {
        const lowerFilename = filename.toLowerCase();
        
        // Check file extension
        if (/\.(jpg|jpeg|png|gif|webp|svg|bmp)$/i.test(lowerFilename)) {
            return 'image';
        }
        if (/\.(mp3|wav|ogg|m4a|flac|aac)$/i.test(lowerFilename)) {
            return 'audio';
        }
        if (/\.(mp4|webm|avi|mov|wmv|mkv)$/i.test(lowerFilename)) {
            return 'video';
        }
        if (/\.(pdf|doc|docx|txt|rtf|md|xls|xlsx|ppt|pptx|csv|json)$/i.test(lowerFilename)) {
            return 'document';
        }
    }
    
    return fileType;
}

/**
 * Calculate human-readable file size
 * @param {number} bytes - File size in bytes
 * @returns {string} Human readable file size (e.g., "1.5 MB")
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get appropriate icon class for a file type
 * @param {string} fileType - The file type ('image', 'audio', 'video', 'document', 'other')
 * @returns {string} Font Awesome icon class
 */
function getFileIcon(fileType) {
    switch (fileType.toLowerCase()) {
        case 'image':
            return 'fa-image';
        case 'audio':
            return 'fa-music';
        case 'video':
            return 'fa-video';
        case 'document':
            return 'fa-file-alt';
        default:
            return 'fa-file';
    }
}

/**
 * Check if a file should be displayed as a preview
 * @param {string} fileType - The file type
 * @param {number} fileSize - The file size in bytes
 * @returns {boolean} Whether the file should be displayed as a preview
 */
function shouldShowPreview(fileType, fileSize) {
    // Only show previews for images under 5MB
    return fileType === 'image' && fileSize < 5 * 1024 * 1024;
}

/**
 * Creates a preview element for a file
 * @param {File} file - The file object
 * @returns {Promise<HTMLElement>} A promise that resolves to the preview element
 */
function createFilePreviewElement(file) {
    return new Promise((resolve) => {
        const fileType = determineFileType(file.type, file.name);
        const container = document.createElement('div');
        container.className = 'file-preview';
        
        if (fileType === 'image') {
            // For images, create a thumbnail
            const img = document.createElement('img');
            img.className = 'file-thumbnail';
            img.alt = 'File preview';
            
            const reader = new FileReader();
            reader.onload = function(e) {
                img.src = e.target.result;
                container.appendChild(img);
                
                const fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                fileInfo.textContent = `${file.name} (${formatFileSize(file.size)})`;
                container.appendChild(fileInfo);
                
                resolve(container);
            };
            reader.readAsDataURL(file);
        } else {
            // For other file types, show an icon
            const iconWrapper = document.createElement('div');
            iconWrapper.className = 'file-icon';
            
            const icon = document.createElement('i');
            icon.className = `fas ${getFileIcon(fileType)}`;
            iconWrapper.appendChild(icon);
            container.appendChild(iconWrapper);
            
            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';
            fileInfo.textContent = `${file.name} (${formatFileSize(file.size)})`;
            container.appendChild(fileInfo);
            
            resolve(container);
        }
    });
}

// Export utilities for use in other modules
window.FileUtils = {
    determineFileType,
    formatFileSize,
    getFileIcon,
    shouldShowPreview,
    createFilePreviewElement
};