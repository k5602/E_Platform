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

    if (hamburgerBtn && sideNav) {
        hamburgerBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            sideNav.classList.toggle('active');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
        });

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                hamburgerBtn.classList.remove('active');
                sideNav.classList.remove('active');
                this.classList.remove('active');
            });
        }
    }
}

// File preview functionality
function initializeFilePreview() {
    const imageInput = document.getElementById('add-img');
    const videoInput = document.getElementById('add-video');
    const previewContainer = document.createElement('div');
    previewContainer.className = 'preview-container';

    // Find where to insert the preview container
    const addPostForm = document.getElementById('add-post-form');
    if (addPostForm) {
        const addBtn = addPostForm.querySelector('.add-btn');
        if (addBtn) {
            addBtn.parentNode.insertBefore(previewContainer, addBtn);
        }
    }

    // Handle image preview
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            // Clear any existing previews
            clearPreviews();

            if (this.files && this.files[0]) {
                const file = this.files[0];

                // Check if the file is an image
                if (file.type.match('image.*')) {
                    const reader = new FileReader();

                    reader.onload = function(e) {
                        const preview = document.createElement('div');
                        preview.className = 'file-preview image-preview';

                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.alt = 'Image Preview';

                        const removeBtn = createRemoveButton(() => {
                            preview.remove();
                            imageInput.value = '';
                        });

                        preview.appendChild(img);
                        preview.appendChild(removeBtn);
                        previewContainer.appendChild(preview);
                    };

                    reader.readAsDataURL(file);
                }
            }
        });
    }

    // Handle video preview
    if (videoInput) {
        videoInput.addEventListener('change', function() {
            // Clear any existing previews
            clearPreviews();

            if (this.files && this.files[0]) {
                const file = this.files[0];

                // Check if the file is a video
                if (file.type.match('video.*')) {
                    const reader = new FileReader();

                    reader.onload = function(e) {
                        const preview = document.createElement('div');
                        preview.className = 'file-preview video-preview';

                        const video = document.createElement('video');
                        video.src = e.target.result;
                        video.controls = true;

                        const removeBtn = createRemoveButton(() => {
                            preview.remove();
                            videoInput.value = '';
                        });

                        preview.appendChild(video);
                        preview.appendChild(removeBtn);
                        previewContainer.appendChild(preview);
                    };

                    reader.readAsDataURL(file);
                }
            }
        });
    }

    // Helper function to create a remove button
    function createRemoveButton(clickHandler) {
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-preview-btn';
        removeBtn.innerHTML = '&times;';
        removeBtn.title = 'Remove';
        removeBtn.addEventListener('click', clickHandler);
        return removeBtn;
    }

    // Helper function to clear all previews
    function clearPreviews() {
        while (previewContainer.firstChild) {
            previewContainer.removeChild(previewContainer.firstChild);
        }
    }
}

// Post creation functionality
function initializePostCreation() {
    const addPostForm = document.getElementById('add-post-form');

    if (addPostForm) {
        addPostForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Reload the page to show the new post
                    window.location.reload();
                } else {
                    // Show error message
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while creating the post.');
            });
        });
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
                commentInput.className = 'comment-input';
                commentInput.placeholder = 'Write a comment...';

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

                const commenterImg = document.createElement('img');
                commenterImg.src = document.querySelector('.user-img').src;
                commenterImg.alt = 'commenter';

                const commenterName = document.createElement('span');
                commenterName.textContent = data.user;

                commenterInfo.appendChild(commenterImg);
                commenterInfo.appendChild(commenterName);

                const commentText = document.createElement('span');
                commentText.textContent = data.content;

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
                    } else {
                        alert('Error: ' + data.message);
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
            } else {
                alert('Error: ' + data.message);
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
