from django.contrib import admin
from .models import Post, Like, Comment, Contact, FAQ, Appointment

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

# Register Contact model
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

# Register FAQ model
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer', 'category')
    ordering = ('order', 'question')
    list_editable = ('order', 'is_active')
    fieldsets = (
        (None, {'fields': ('question', 'answer')}),
        ('Categorization', {'fields': ('category', 'order')}),
        ('Status', {'fields': ('is_active',)}),
    )

# Register Appointment model
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'appointment_date', 'appointment_time', 'appointment_type', 'status', 'instructor')
    list_filter = ('status', 'appointment_type', 'appointment_date')
    search_fields = ('name', 'email', 'message')
    date_hierarchy = 'appointment_date'
    ordering = ('-appointment_date', '-appointment_time')
    list_editable = ('status',)
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('name', 'email', 'phone', 'appointment_date', 'appointment_time', 'appointment_type')
        }),
        ('Status Information', {
            'fields': ('status', 'user', 'instructor')
        }),
        ('Additional Information', {
            'fields': ('message',)
        }),
    )
    
    def get_queryset(self, request):
        """Customize the queryset based on user role."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # If user is an instructor, only show their appointments
        return qs.filter(instructor=request.user)
