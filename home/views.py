from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Post, Like, Comment
from .forms import PostForm, CommentForm
import json

@login_required
def home_view(request):
    """Main home page view that displays the feed of posts."""
    posts = Post.objects.select_related('user').prefetch_related('likes', 'comments').all()

    # Pagination
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Handle post creation
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('home')
    else:
        form = PostForm()

    context = {
        'page_obj': page_obj,
        'form': form,
    }
    return render(request, 'home/home.html', context)

@login_required
@require_POST
def create_post(request):
    """API endpoint for creating a new post."""
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        post.save()
        return JsonResponse({
            'status': 'success',
            'post_id': post.id,
            'message': 'Post created successfully!'
        })
    return JsonResponse({
        'status': 'error',
        'errors': form.errors,
        'message': 'Failed to create post.'
    }, status=400)

@login_required
@require_POST
def like_post(request, post_id):
    """API endpoint for liking/unliking a post."""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        # User already liked the post, so unlike it
        like.delete()
        liked = False
    else:
        liked = True

    like_count = post.likes.count()

    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'like_count': like_count
    })

@login_required
@require_POST
def add_comment(request, post_id):
    """API endpoint for adding a comment to a post."""
    post = get_object_or_404(Post, id=post_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        comment.save()

        return JsonResponse({
            'status': 'success',
            'comment_id': comment.id,
            'user': comment.user.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({
        'status': 'error',
        'errors': form.errors,
        'message': 'Failed to add comment.'
    }, status=400)

@login_required
@require_POST
def delete_post(request, post_id):
    """API endpoint for deleting a post."""
    post = get_object_or_404(Post, id=post_id)

    # Only allow the post owner to delete it
    if post.user != request.user:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to delete this post.'
        }, status=403)

    post.delete()

    return JsonResponse({
        'status': 'success',
        'message': 'Post deleted successfully!'
    })

@login_required
@require_POST
def delete_comment(request, comment_id):
    """API endpoint for deleting a comment."""
    comment = get_object_or_404(Comment, id=comment_id)

    # Only allow the comment owner to delete it
    if comment.user != request.user:
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to delete this comment.'
        }, status=403)

    comment.delete()

    return JsonResponse({
        'status': 'success',
        'message': 'Comment deleted successfully!'
    })
