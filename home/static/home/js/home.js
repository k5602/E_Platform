document.addEventListener('DOMContentLoaded', function() {
    // Initialize Read More functionality for posts
    initializeReadMore();

    // Initialize mobile menu functionality
    initializeMobileMenu();

    // Initialize file preview functionality
    initializeFilePreview();

    // Initialize post creation
    initializePostCreation();

    // Initialize like functionality
    initializeLikes();

    // Initialize comment functionality
    initializeComments();

    // Initialize delete functionality
    initializeDeleteButtons();

    // Initialize toast test button
    initializeToastTest();

    // Initialize real-time polling for comments and likes
    initializeRealtimePolling();
});

// Read More functionality
function initializeReadMore() {
    const posts = document.querySelectorAll('.post');
    const maxWords = 50;

    posts.forEach(post => {
        const content = post.querySelector('.content');
        const readMoreBtn = post.querySelector('.read-more-btn');

        if (!content || !readMoreBtn) return;

        const wordCount = countWords(content);

        if (wordCount <= maxWords) {
            readMoreBtn.style.display = 'none';
            content.classList.remove('collapsed');
        } else {
            readMoreBtn.addEventListener('click', function() {
                if (content.classList.contains('collapsed')) {
                    content.classList.remove('collapsed');
                    this.textContent = 'Read Less';
                    post.classList.add('expanded');
                } else {
                    content.classList.add('collapsed');
                    this.textContent = 'Read More';
                    post.classList.remove('expanded');
                }
            });
        }
    });
}

// Helper function to count words
function countWords(element) {
    if (!element) return 0;
    const text = element.textContent || element.innerText;
    return text.split(/\s+/).filter(word => word.length > 0).length;
}

// Mobile menu functionality
function initializeMobileMenu() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sideNav = document.getElementById('side-nav');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const body = document.body;

    if (hamburgerBtn && sideNav) {
        // Toggle sidebar when hamburger button is clicked
        hamburgerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // Toggle sidebar open class on body
            body.classList.toggle('sidebar-open');

            // Toggle active class on sidebar
            sideNav.classList.toggle('active');

            // Toggle active class on overlay
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }

            // Update ARIA attributes for accessibility
            const isExpanded = body.classList.contains('sidebar-open');
            hamburgerBtn.setAttribute('aria-expanded', isExpanded);
        });

        // Close sidebar when overlay is clicked
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                body.classList.remove('sidebar-open');
                sideNav.classList.remove('active');
                sidebarOverlay.classList.remove('active');
                hamburgerBtn.setAttribute('aria-expanded', 'false');
            });
        }

        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 &&
                body.classList.contains('sidebar-open') &&
                !sideNav.contains(e.target) &&
                !hamburgerBtn.contains(e.target)) {
                body.classList.remove('sidebar-open');
                sideNav.classList.remove('active');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('active');
                }
                hamburgerBtn.setAttribute('aria-expanded', 'false');
            }
        });

        // Handle escape key to close sidebar
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && body.classList.contains('sidebar-open')) {
                body.classList.remove('sidebar-open');
                sideNav.classList.remove('active');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('active');
                }
                hamburgerBtn.setAttribute('aria-expanded', 'false');
            }
        });

        // Add scrollbar to sidebar content on low-resolution screens
        if (window.matchMedia('(max-height: 700px)').matches) {
            const mainMenu = sideNav.querySelector('.main-menu');
            if (mainMenu) {
                mainMenu.classList.add('low-res-scroll');
            }
        }
    }
}

// File preview functionality
function initializeFilePreview() {
    const imageInput = document.getElementById('add-img');
    const videoInput = document.getElementById('add-video');
    const documentInput = document.getElementById('add-document');
    const addPostForm = document.getElementById('add-post-form');
    const contentTextarea = document.querySelector('.add-post');

    // Create preview container
    const previewContainer = document.createElement('div');
    previewContainer.className = 'preview-container';

    // Create character counter
    const charCounter = document.createElement('div');
    charCounter.className = 'char-counter';
    charCounter.innerHTML = '<span>0</span>/500';

    // Create media type indicator
    const mediaTypeIndicator = document.createElement('div');
    mediaTypeIndicator.className = 'media-type-indicator';
    mediaTypeIndicator.innerHTML = '<span class="media-icon"></span><span class="media-text"></span>';
    mediaTypeIndicator.style.display = 'none';

    // Create drop zone
    const dropZone = document.createElement('div');
    dropZone.className = 'drop-zone';
    dropZone.innerHTML = '<div class="drop-zone-text">Drop your image, video, or document here</div>';

    // Find where to insert the elements
    if (addPostForm) {
        const addBtn = addPostForm.querySelector('.add-btn');
        const addPostInputs = addPostForm.querySelector('.addpost-inputs');

        if (addBtn && addPostInputs) {
            // Make the form container position relative for absolute positioning of drop zone
            addPostForm.style.position = 'relative';

            // Insert elements
            addPostInputs.appendChild(charCounter);
            addPostInputs.appendChild(mediaTypeIndicator);
            addPostForm.appendChild(dropZone);
            addPostForm.insertBefore(previewContainer, addBtn);

            // Initialize character counter
            if (contentTextarea) {
                contentTextarea.addEventListener('input', function() {
                    const currentLength = this.value.length;
                    const counterSpan = charCounter.querySelector('span');
                    counterSpan.textContent = currentLength;

                    // Update counter color based on length
                    if (currentLength > 400) {
                        charCounter.classList.add('warning');
                    } else {
                        charCounter.classList.remove('warning');
                    }

                    if (currentLength > 480) {
                        charCounter.classList.add('danger');
                    } else {
                        charCounter.classList.remove('danger');
                    }
                });
            }
        }
    }

    // Handle drag and drop
    if (addPostForm) {
        // Counter to track drag enter/leave events
        let dragCounter = 0;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            addPostForm.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        // Add global drag event listeners to detect files being dragged from outside
        document.addEventListener('dragenter', function(e) {
            if (e.dataTransfer && e.dataTransfer.types &&
                (e.dataTransfer.types.indexOf('Files') !== -1 || e.dataTransfer.types.includes('Files'))) {
                // Increment counter and show drop zone
                dragCounter++;
                dropZone.classList.add('highlight');
            }
        }, false);

        document.addEventListener('dragleave', function(e) {
            // Check if the drag leave event is leaving the document
            if (e.clientX <= 0 || e.clientY <= 0 ||
                e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
                dragCounter = 0;
                dropZone.classList.remove('highlight');
            }
        }, false);

        document.addEventListener('drop', function() {
            // Reset counter on global drop
            dragCounter = 0;
            dropZone.classList.remove('highlight');
        }, false);

        // Handle drag enter
        addPostForm.addEventListener('dragenter', function(e) {
            dragCounter++;

            // Check if the dragged item is a file
            if (e.dataTransfer && e.dataTransfer.types &&
                (e.dataTransfer.types.indexOf('Files') !== -1 || e.dataTransfer.types.includes('Files'))) {
                dropZone.classList.add('highlight');
            }
        }, false);

        // Handle drag over
        addPostForm.addEventListener('dragover', function(e) {
            // Prevent default to allow drop
            e.preventDefault();

            // Set the dropEffect to copy
            e.dataTransfer.dropEffect = 'copy';

            // Check if the dragged item is a file
            if (e.dataTransfer && e.dataTransfer.types &&
                (e.dataTransfer.types.indexOf('Files') !== -1 || e.dataTransfer.types.includes('Files'))) {
                dropZone.classList.add('highlight');
            }
        }, false);

        // Handle drag leave
        addPostForm.addEventListener('dragleave', function() {
            dragCounter--;

            // Only remove highlight when counter reaches 0
            if (dragCounter === 0) {
                dropZone.classList.remove('highlight');
            }
        }, false);

        // Handle drop
        addPostForm.addEventListener('drop', function() {
            // Reset counter and remove highlight
            dragCounter = 0;
            dropZone.classList.remove('highlight');
        }, false);

        // Handle dropped files
        addPostForm.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                const file = files[0]; // Take only the first file

                if (file.type.match('image.*')) {
                    // Clear other inputs
                    if (videoInput) videoInput.value = '';
                    if (documentInput) documentInput.value = '';

                    // Handle the file directly without DataTransfer API
                    if (imageInput) {
                        // Create a direct file preview
                        handleImagePreview(file);
                    }
                } else if (file.type.match('video.*')) {
                    // Clear other inputs
                    if (imageInput) imageInput.value = '';
                    if (documentInput) documentInput.value = '';

                    // Handle the file directly without DataTransfer API
                    if (videoInput) {
                        // Create a direct file preview
                        handleVideoPreview(file);
                    }
                } else {
                    // Check if it's a supported document type
                    const fileExt = file.name.split('.').pop().toLowerCase();
                    const supportedDocTypes = ['pdf', 'md', 'docx', 'xlsx', 'tex', 'pptx'];

                    if (supportedDocTypes.includes(fileExt)) {
                        // Clear other inputs
                        if (imageInput) imageInput.value = '';
                        if (videoInput) videoInput.value = '';

                        // Handle document preview
                        if (documentInput) {
                            handleDocumentPreview(file);
                        }
                    } else {
                        if (typeof window.showToast === 'function') {
                        window.showToast('Unsupported file type. Please upload an image, video, or document (PDF, MD, DOCX, XLSX, TEX, PPTX).', 'error');
                    } else {
                        showError('Unsupported file type. Please upload an image, video, or document (PDF, MD, DOCX, XLSX, TEX, PPTX).');
                    }
                    }
                }
            }
        }, false);
    }

    // Handle image preview
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            // Clear other inputs
            if (videoInput) videoInput.value = '';
            if (documentInput) documentInput.value = '';

            // Remove any hidden inputs
            const hiddenVideoInput = document.getElementById('hidden-video-input');
            if (hiddenVideoInput) {
                hiddenVideoInput.remove();
            }

            const hiddenDocumentInput = document.getElementById('hidden-document-input');
            if (hiddenDocumentInput) {
                hiddenDocumentInput.remove();
            }

            if (this.files && this.files[0]) {
                const file = this.files[0];

                // Check if the file is an image
                if (file.type.match('image.*')) {
                    handleImagePreview(file);
                }
            } else {
                mediaTypeIndicator.style.display = 'none';
                clearPreviews();
            }
        });
    }

    // Handle video preview
    if (videoInput) {
        videoInput.addEventListener('change', function() {
            // Clear other inputs
            if (imageInput) imageInput.value = '';
            if (documentInput) documentInput.value = '';

            // Remove any hidden inputs
            const hiddenImageInput = document.getElementById('hidden-image-input');
            if (hiddenImageInput) {
                hiddenImageInput.remove();
            }

            const hiddenDocumentInput = document.getElementById('hidden-document-input');
            if (hiddenDocumentInput) {
                hiddenDocumentInput.remove();
            }

            if (this.files && this.files[0]) {
                const file = this.files[0];

                // Check if the file is a video
                if (file.type.match('video.*')) {
                    handleVideoPreview(file);
                }
            } else {
                mediaTypeIndicator.style.display = 'none';
                clearPreviews();
            }
        });
    }

    // Handle document preview
    if (documentInput) {
        documentInput.addEventListener('change', function() {
            // Clear other inputs
            if (imageInput) imageInput.value = '';
            if (videoInput) videoInput.value = '';

            // Remove any hidden inputs
            const hiddenImageInput = document.getElementById('hidden-image-input');
            if (hiddenImageInput) {
                hiddenImageInput.remove();
            }

            const hiddenVideoInput = document.getElementById('hidden-video-input');
            if (hiddenVideoInput) {
                hiddenVideoInput.remove();
            }

            if (this.files && this.files[0]) {
                const file = this.files[0];
                const fileExt = file.name.split('.').pop().toLowerCase();
                const supportedDocTypes = ['pdf', 'md', 'docx', 'xlsx', 'tex', 'pptx'];

                if (supportedDocTypes.includes(fileExt)) {
                    handleDocumentPreview(file);
                } else {
                    if (typeof window.showToast === 'function') {
                        window.showToast('Unsupported document type. Please upload PDF, MD, DOCX, XLSX, TEX, or PPTX files.', 'error');
                    } else {
                        showError('Unsupported document type. Please upload PDF, MD, DOCX, XLSX, TEX, or PPTX files.');
                    }
                    this.value = '';
                }
            } else {
                mediaTypeIndicator.style.display = 'none';
                clearPreviews();
            }
        });
    }

    // Helper function to create a remove button
    function createRemoveButton(clickHandler) {
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-preview-btn';
        removeBtn.innerHTML = '&times;';
        removeBtn.title = 'Remove';
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            clickHandler();
        });
        return removeBtn;
    }

    // Helper function to clear all previews
    function clearPreviews() {
        // Animate removal
        const previews = previewContainer.querySelectorAll('.file-preview');
        previews.forEach(preview => {
            preview.style.opacity = '0';
            preview.style.transform = 'translateY(10px)';
        });

        // Remove after animation
        setTimeout(() => {
            while (previewContainer.firstChild) {
                previewContainer.removeChild(previewContainer.firstChild);
            }
        }, 300);
    }

    // Helper function to prevent default drag behaviors
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Helper function to format file size
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }

    // Helper function to truncate filename
    function truncateFilename(filename, maxLength) {
        if (filename.length <= maxLength) return filename;

        const extension = filename.split('.').pop();
        const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));

        const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 3) + '...';
        return truncatedName + '.' + extension;
    }

    // Helper function to update media type indicator
    function updateMediaTypeIndicator(type, filename) {
        const icon = mediaTypeIndicator.querySelector('.media-icon');
        const text = mediaTypeIndicator.querySelector('.media-text');

        icon.className = 'media-icon ' + type + '-icon';

        if (type === 'image') {
            text.textContent = 'Image: ';
        } else if (type === 'video') {
            text.textContent = 'Video: ';
        } else if (type === 'document') {
            text.textContent = 'Document: ';
        }

        text.textContent += truncateFilename(filename, 15);

        mediaTypeIndicator.style.display = 'flex';
    }

    // Helper function to show error
    function showError(message) {
        // Create error element
        const errorElement = document.createElement('div');
        errorElement.className = 'upload-error';
        errorElement.textContent = message;

        // Add to form
        if (addPostForm) {
            addPostForm.insertBefore(errorElement, previewContainer);

            // Remove after 5 seconds
            setTimeout(() => {
                errorElement.style.opacity = '0';
                setTimeout(() => {
                    errorElement.remove();
                }, 300);
            }, 5000);
        }
    }

    // Helper function to handle image preview directly
    function handleImagePreview(file) {
        // Check file size
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            showError(`Image size exceeds the maximum allowed (${formatFileSize(maxSize)})`);
            return;
        }

        // Clear any existing previews
        clearPreviews();

        // Update media type indicator
        updateMediaTypeIndicator('image', file.name);

        // Create a blob URL for the file
        const blobUrl = URL.createObjectURL(file);

        // Create preview element
        const preview = document.createElement('div');
        preview.className = 'file-preview image-preview';

        const img = document.createElement('img');
        img.src = blobUrl;
        img.alt = 'Image Preview';

        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        fileInfo.innerHTML = `
            <span class="file-name">${truncateFilename(file.name, 20)}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
        `;

        const removeBtn = createRemoveButton(() => {
            preview.remove();
            URL.revokeObjectURL(blobUrl);
            if (imageInput) imageInput.value = '';
            mediaTypeIndicator.style.display = 'none';

            // Also clear the form data
            const formData = new FormData();
            formData.delete('image');
        });

        preview.appendChild(img);
        preview.appendChild(fileInfo);
        preview.appendChild(removeBtn);

        // Add with animation
        preview.style.opacity = '0';
        preview.style.transform = 'translateY(10px)';
        previewContainer.appendChild(preview);

        // Trigger reflow
        preview.offsetHeight;

        // Add animation class
        preview.style.opacity = '1';
        preview.style.transform = 'translateY(0)';

        // Store the file in a FormData object for submission
        const formData = new FormData(addPostForm);
        formData.append('image', file);

        // Create a hidden input to store the file for form submission
        let hiddenInput = document.getElementById('hidden-image-input');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'file';
            hiddenInput.id = 'hidden-image-input';
            hiddenInput.name = 'image';
            hiddenInput.style.display = 'none';
            addPostForm.appendChild(hiddenInput);
        }

        // Use the File API to set the file
        const dT = new DataTransfer();
        dT.items.add(file);
        hiddenInput.files = dT.files;
    }

    // Helper function to handle video preview directly
    function handleVideoPreview(file) {
        // Check file size
        const maxSize = 20 * 1024 * 1024; // 20MB
        if (file.size > maxSize) {
            showError(`Video size exceeds the maximum allowed (${formatFileSize(maxSize)})`);
            return;
        }

        // Clear any existing previews
        clearPreviews();

        // Update media type indicator
        updateMediaTypeIndicator('video', file.name);

        // Create a blob URL for the file
        const blobUrl = URL.createObjectURL(file);

        // Create preview element
        const preview = document.createElement('div');
        preview.className = 'file-preview video-preview';

        const video = document.createElement('video');
        video.src = blobUrl;
        video.controls = true;

        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        fileInfo.innerHTML = `
            <span class="file-name">${truncateFilename(file.name, 20)}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
        `;

        const removeBtn = createRemoveButton(() => {
            preview.remove();
            URL.revokeObjectURL(blobUrl);
            if (videoInput) videoInput.value = '';
            mediaTypeIndicator.style.display = 'none';

            // Also clear the form data
            const formData = new FormData();
            formData.delete('video');
        });

        preview.appendChild(video);
        preview.appendChild(fileInfo);
        preview.appendChild(removeBtn);

        // Add with animation
        preview.style.opacity = '0';
        preview.style.transform = 'translateY(10px)';
        previewContainer.appendChild(preview);

        // Trigger reflow
        preview.offsetHeight;

        // Add animation class
        preview.style.opacity = '1';
        preview.style.transform = 'translateY(0)';

        // Store the file in a FormData object for submission
        const formData = new FormData(addPostForm);
        formData.append('video', file);

        // Create a hidden input to store the file for form submission
        let hiddenInput = document.getElementById('hidden-video-input');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'file';
            hiddenInput.id = 'hidden-video-input';
            hiddenInput.name = 'video';
            hiddenInput.style.display = 'none';
            addPostForm.appendChild(hiddenInput);
        }

        // Use the File API to set the file
        const dT = new DataTransfer();
        dT.items.add(file);
        hiddenInput.files = dT.files;
    }

    // Helper function to handle document preview
    function handleDocumentPreview(file) {
        // Check file size
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            showError(`Document size exceeds the maximum allowed (${formatFileSize(maxSize)})`);
            return;
        }

        // Clear any existing previews
        clearPreviews();

        // Update media type indicator
        updateMediaTypeIndicator('document', file.name);

        // Get file extension
        const fileExt = file.name.split('.').pop().toLowerCase();

        // Create preview element
        const preview = document.createElement('div');
        preview.className = 'file-preview document-preview-container';

        // Create document icon based on file type
        const docIcon = document.createElement('div');
        docIcon.className = 'document-icon';

        // Set appropriate icon based on file extension
        let iconSrc = '';
        switch(fileExt) {
            case 'pdf':
                iconSrc = '/static/home/images/pdf-icon.svg';
                break;
            case 'md':
                iconSrc = '/static/home/images/markdown-icon.svg';
                break;
            case 'docx':
                iconSrc = '/static/home/images/word-icon.svg';
                break;
            case 'xlsx':
                iconSrc = '/static/home/images/excel-icon.svg';
                break;
            case 'tex':
                iconSrc = '/static/home/images/latex-icon.svg';
                break;
            case 'pptx':
                iconSrc = '/static/home/images/powerpoint-icon.svg';
                break;
            default:
                iconSrc = '/static/home/images/document-icon.svg';
        }

        const iconImg = document.createElement('img');
        iconImg.src = iconSrc;
        iconImg.alt = fileExt.toUpperCase();
        docIcon.appendChild(iconImg);

        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        fileInfo.innerHTML = `
            <span class="file-name">${truncateFilename(file.name, 20)}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
        `;

        const removeBtn = createRemoveButton(() => {
            preview.remove();
            if (documentInput) documentInput.value = '';
            mediaTypeIndicator.style.display = 'none';

            // Also clear the form data
            const formData = new FormData();
            formData.delete('document');
        });

        preview.appendChild(docIcon);
        preview.appendChild(fileInfo);
        preview.appendChild(removeBtn);

        // Add with animation
        preview.style.opacity = '0';
        preview.style.transform = 'translateY(10px)';
        previewContainer.appendChild(preview);

        // Trigger reflow
        preview.offsetHeight;

        // Add animation class
        preview.style.opacity = '1';
        preview.style.transform = 'translateY(0)';

        // Store the file in a FormData object for submission
        const formData = new FormData(addPostForm);
        formData.append('document', file);

        // Create a hidden input to store the file for form submission
        let hiddenInput = document.getElementById('hidden-document-input');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'file';
            hiddenInput.id = 'hidden-document-input';
            hiddenInput.name = 'document';
            hiddenInput.style.display = 'none';
            addPostForm.appendChild(hiddenInput);
        }

        // Use the File API to set the file
        const dT = new DataTransfer();
        dT.items.add(file);
        hiddenInput.files = dT.files;
    }
}

// Post creation functionality
function initializePostCreation() {
    const addPostForm = document.getElementById('add-post-form');

    if (addPostForm) {
        // Create loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="spinner"></div>
            <div class="loading-text">Posting...</div>
        `;
        document.body.appendChild(loadingOverlay);

        // Create toast notification container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        // Add submit event listener
        addPostForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form elements
            const contentTextarea = this.querySelector('.add-post');
            const imageInput = document.getElementById('add-img');
            const videoInput = document.getElementById('add-video');
            const submitButton = this.querySelector('.add-btn');

            // Validate content
            if (!contentTextarea.value.trim()) {
                showToast('Please enter some content for your post.', 'error');
                contentTextarea.focus();
                return;
            }

            // Disable submit button and show loading
            submitButton.disabled = true;
            submitButton.classList.add('loading');
            submitButton.innerHTML = '<span class="btn-spinner"></span> Posting...';

            // Show loading overlay with animation
            loadingOverlay.style.display = 'flex';
            setTimeout(() => {
                loadingOverlay.style.opacity = '1';
            }, 10);

            // Create form data
            const formData = new FormData(this);

            // Send the request
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Show success message
                    showToast('Post created successfully!', 'success');

                    // Clear form
                    contentTextarea.value = '';
                    if (imageInput) imageInput.value = '';
                    if (videoInput) videoInput.value = '';

                    // Clear preview
                    const previewContainer = addPostForm.querySelector('.preview-container');
                    if (previewContainer) {
                        while (previewContainer.firstChild) {
                            previewContainer.removeChild(previewContainer.firstChild);
                        }
                    }

                    // Clear media type indicator
                    const mediaTypeIndicator = addPostForm.querySelector('.media-type-indicator');
                    if (mediaTypeIndicator) {
                        mediaTypeIndicator.style.display = 'none';
                    }

                    // Reset character counter
                    const charCounter = addPostForm.querySelector('.char-counter span');
                    if (charCounter) {
                        charCounter.textContent = '0';
                    }

                    // Create new post element and add it to the DOM
                    createNewPostElement(data);

                } else {
                    // Show error message
                    if (data.errors) {
                        // Display specific field errors
                        Object.keys(data.errors).forEach(field => {
                            showToast(`${field}: ${data.errors[field]}`, 'error');
                        });
                    } else {
                        showToast(data.message || 'An error occurred while creating the post.', 'error');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred while creating the post.', 'error');
            })
            .finally(() => {
                // Hide loading overlay with animation
                loadingOverlay.style.opacity = '0';
                setTimeout(() => {
                    loadingOverlay.style.display = 'none';
                }, 300);

                // Re-enable submit button
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
                submitButton.textContent = 'Add Post';
            });
        });

        // Function to create a new post element
        function createNewPostElement(postData) {
            // Log the data for debugging purposes
            console.log('Post created successfully:', postData);

            // We'll implement this in a future update to dynamically add the new post
            // For now, we'll just reload the page after a short delay
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }

        // Function to show toast notification using the global toast system
        function showToast(message, type = 'info') {
            // Use the global toast function if available
            if (typeof window.showToast === 'function') {
                window.showToast(message, type);
            } else {
                // Fallback to console if toast system is not available
                console.log(`${type.toUpperCase()}: ${message}`);
            }
        }
    }
}

// Like functionality
function initializeLikes() {
    const likeBtns = document.querySelectorAll('.like_btn');

    likeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = this.dataset.postId;
            const likeCount = this.querySelector('.like-count');

            if (!postId) return;

            fetch(`/home/post/${postId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (data.liked) {
                        this.classList.add('liked');
                    } else {
                        this.classList.remove('liked');
                    }

                    if (likeCount) {
                        likeCount.textContent = data.like_count;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
}

// Comment functionality
function initializeComments() {
    const commentBtns = document.querySelectorAll('.Comment');

    commentBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = this.dataset.postId;
            const post = this.closest('.post');

            if (!postId || !post) return;

            let commentInputContainer = post.querySelector('.comment-input-container');

            if (!commentInputContainer) {
                // Create comment input container
                commentInputContainer = document.createElement('div');
                commentInputContainer.className = 'comment-input-container';

                const commentInput = document.createElement('input');
                commentInput.type = 'text';
                commentInput.className = 'comment-input mentionable';
                commentInput.placeholder = 'Write a comment... (use @ to mention users)';

                const submitBtn = document.createElement('button');
                submitBtn.className = 'submit-comment-btn';
                submitBtn.textContent = 'Add';

                commentInputContainer.appendChild(commentInput);
                commentInputContainer.appendChild(submitBtn);

                // Find where to insert the comment input
                const commentList = post.querySelector('.comment-list');
                if (commentList) {
                    commentList.parentNode.insertBefore(commentInputContainer, commentList);
                } else {
                    // Create comment list if it doesn't exist
                    const newCommentList = document.createElement('ul');
                    newCommentList.className = 'comment-list';
                    post.appendChild(commentInputContainer);
                    post.appendChild(newCommentList);
                }

                // Add event listener to submit button
                submitBtn.addEventListener('click', function() {
                    submitComment(postId, commentInput.value, post);
                });

                // Add event listener for Enter key
                commentInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        submitComment(postId, commentInput.value, post);
                    }
                });
            }

            // Focus on the input
            commentInputContainer.querySelector('.comment-input').focus();
        });
    });
}

// Function to submit a comment
function submitComment(postId, content, post) {
    if (!content.trim()) return;

    const formData = new FormData();
    formData.append('content', content);

    fetch(`/home/post/${postId}/comment/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Clear input
            post.querySelector('.comment-input').value = '';

            // Add comment to the list
            const commentList = post.querySelector('.comment-list');
            if (commentList) {
                const li = document.createElement('li');

                const commenterInfo = document.createElement('span');
                commenterInfo.className = 'commenter-info';

                // Create link to user profile
                const profileLink = document.createElement('a');
                profileLink.href = `/profile/${data.user}/`;
                profileLink.style.display = 'flex';
                profileLink.style.alignItems = 'center';
                profileLink.style.textDecoration = 'none';
                profileLink.style.color = 'inherit';

                const commenterImg = document.createElement('img');
                // Get the current user's profile picture from the sidebar
                const userImg = document.querySelector('.user-img');
                if (userImg) {
                    commenterImg.src = userImg.src;
                    commenterImg.alt = 'commenter';
                    commenterImg.style.objectFit = 'cover';
                    commenterImg.style.cursor = 'pointer';
                } else {
                    commenterImg.src = '/static/home/images/student.jpeg';
                    commenterImg.alt = 'commenter';
                    commenterImg.style.cursor = 'pointer';
                }

                const commenterName = document.createElement('span');
                commenterName.textContent = data.user;

                profileLink.appendChild(commenterImg);
                profileLink.appendChild(commenterName);
                commenterInfo.appendChild(profileLink);

                const commentText = document.createElement('span');
                commentText.className = 'format-mentions';

                // Use formatted_content if available, otherwise use regular content
                if (data.formatted_content) {
                    commentText.innerHTML = data.formatted_content;
                } else {
                    commentText.textContent = data.content;
                }

                const removeBtn = document.createElement('button');
                removeBtn.className = 'remove-comment-btn';
                removeBtn.textContent = 'X';
                removeBtn.dataset.commentId = data.comment_id;
                removeBtn.addEventListener('click', function() {
                    deleteComment(data.comment_id, li);
                });

                li.appendChild(commenterInfo);
                li.appendChild(commentText);
                li.appendChild(removeBtn);

                commentList.prepend(li);
            }
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Delete functionality
function initializeDeleteButtons() {
    // Delete post buttons
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this post?')) {
                const postId = this.dataset.postId;
                const post = this.closest('.post');

                if (!postId || !post) return;

                fetch(`/home/post/${postId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        post.remove();
                        // Show success toast
                        if (typeof window.showToast === 'function') {
                            window.showToast('Post deleted successfully', 'success');
                        }
                    } else {
                        if (typeof window.showToast === 'function') {
                            window.showToast('Error: ' + data.message, 'error');
                        } else {
                            alert('Error: ' + data.message);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
        });
    });

    // Delete comment buttons
    document.querySelectorAll('.remove-comment-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const comment = this.closest('li');

            if (!commentId || !comment) return;

            deleteComment(commentId, comment);
        });
    });
}

// Function to delete a comment
function deleteComment(commentId, commentElement) {
    if (confirm('Are you sure you want to delete this comment?')) {
        fetch(`/home/comment/${commentId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                commentElement.remove();
                // Show success toast
                if (typeof window.showToast === 'function') {
                    window.showToast('Comment deleted successfully', 'success');
                }
            } else {
                if (typeof window.showToast === 'function') {
                    window.showToast('Error: ' + data.message, 'error');
                } else {
                    alert('Error: ' + data.message);
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

// Helper function to get CSRF token
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

// Function to initialize toast test button
function initializeToastTest() {
    const testToastBtn = document.getElementById('test-toast-btn');
    if (testToastBtn) {
        testToastBtn.addEventListener('click', function() {
            console.log('Test toast button clicked');

            // Test if window.showToast exists
            if (typeof window.showToast === 'function') {
                // Show different types of toasts
                window.showToast('This is an info toast notification', 'info');

                setTimeout(() => {
                    window.showToast('This is a success toast notification', 'success');
                }, 1000);

                setTimeout(() => {
                    window.showToast('This is a warning toast notification', 'warning');
                }, 2000);

                setTimeout(() => {
                    window.showToast('This is an error toast notification', 'error');
                }, 3000);
            } else {
                console.error('window.showToast function is not available');
                alert('Toast notification system is not available. Check the console for details.');
            }
        });
    }
}

// Real-time Polling for Comments and Likes
function initializeRealtimePolling() {
    const POLLING_INTERVAL_MS = 5000; // Configurable interval (5 seconds)
    let lastComments = {};
    let lastLikes = {};

    function fetchAndUpdate(postId, postElement) {
        // Fetch comments
        fetch(`/home/post/${postId}/comments/`, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const comments = data.comments;
                    // Compare with lastComments
                    if (!lastComments[postId] || JSON.stringify(lastComments[postId]) !== JSON.stringify(comments)) {
                        updateCommentsUI(postElement, comments);
                        if (lastComments[postId]) {
                            showToast('New comments available!', 'info');
                        }
                        lastComments[postId] = comments;
                    }
                }
            });
        // Fetch likes
        fetch(`/home/post/${postId}/likes/`, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const likeCount = data.like_count;
                    if (lastLikes[postId] !== likeCount) {
                        updateLikesUI(postElement, likeCount);
                        if (lastLikes[postId] !== undefined) {
                            showToast('New likes on this post!', 'success');
                        }
                        lastLikes[postId] = likeCount;
                    }
                }
            });
    }

    function updateCommentsUI(postElement, comments) {
        const commentList = postElement.querySelector('.comment-list');
        if (!commentList) return;
        commentList.innerHTML = '';
        comments.forEach(c => {
            const li = document.createElement('li');
            // Use formatted_content if available, otherwise use regular content
            const contentHtml = c.formatted_content || c.content;
            // Check if we have profile picture information in the comment data
            const profilePicture = c.profile_picture ? `<img src="${c.profile_picture}" alt="${c.user}" style="object-fit:cover;cursor:pointer;">` :
                                                      `<img src="/static/home/images/student.jpeg" alt="${c.user}" style="cursor:pointer;">`;
            li.innerHTML = `<span class="commenter-info"><a href="/profile/${c.user}/" style="display:flex;align-items:center;text-decoration:none;color:inherit;">${profilePicture}<span>${c.user}</span></a></span> <span class="format-mentions">${contentHtml}</span>`;
            commentList.appendChild(li);
        });
    }

    function updateLikesUI(postElement, likeCount) {
        const likeCountSpan = postElement.querySelector('.like-count');
        if (likeCountSpan) {
            likeCountSpan.textContent = likeCount;
        }
    }

    function pollAllPosts() {
        document.querySelectorAll('.post').forEach(post => {
            const postId = post.querySelector('.like_btn')?.dataset.postId;
            if (postId) {
                fetchAndUpdate(postId, post);
            }
        });
    }

    setInterval(pollAllPosts, POLLING_INTERVAL_MS);
}
