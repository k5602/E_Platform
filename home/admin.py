from django.contrib import admin
from .models import Post, Like, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

class LikeInline(admin.TabularInline):
    model = Like
    extra = 0

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content_preview', 'has_image', 'has_video', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'user__username')
    date_hierarchy = 'created_at'
    inlines = [CommentInline, LikeInline]

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True

    def has_video(self, obj):
        return bool(obj.video)
    has_video.boolean = True

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'content_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'user__username')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username',)
