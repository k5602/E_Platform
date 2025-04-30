from django.contrib import admin
from .models import (
    Post, Like, Comment, Contact, FAQ, Appointment,
    Subject, SubjectMaterial, SubjectEnrollment
)

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('user', 'content', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)

class LikeInline(admin.TabularInline):
    model = Like
    extra = 0
    fields = ('user', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content_preview', 'has_image', 'has_video', 'has_document', 'comment_count', 'like_count', 'created_at')
    list_filter = (
        'created_at',
        'user',
        ('image', admin.EmptyFieldListFilter),
        ('video', admin.EmptyFieldListFilter),
        ('document', admin.EmptyFieldListFilter)
    )
    search_fields = ('content', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    inlines = [CommentInline, LikeInline]
    list_per_page = 20
    raw_id_fields = ('user',)

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Image'

    def has_video(self, obj):
        return bool(obj.video)
    has_video.boolean = True
    has_video.short_description = 'Video'

    def has_document(self, obj):
        return bool(obj.document)
    has_document.boolean = True
    has_document.short_description = 'Doc'

    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = 'Likes'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post_preview', 'content_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'user__username', 'user__email', 'post__content')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'post')
    list_per_page = 25

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def post_preview(self, obj):
        return obj.post.content[:30] + '...' if len(obj.post.content) > 30 else obj.post.content
    post_preview.short_description = 'Post'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'user__email', 'post__content')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'post')
    list_per_page = 25

    def post_preview(self, obj):
        return obj.post.content[:50] + '...' if len(obj.post.content) > 50 else obj.post.content
    post_preview.short_description = 'Post'

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
    raw_id_fields = ('user', 'instructor')

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


# Subject Models Admin
class SubjectMaterialInline(admin.TabularInline):
    model = SubjectMaterial
    extra = 1
    fields = ('title', 'material_type', 'file', 'external_url', 'is_active')


class SubjectEnrollmentInline(admin.TabularInline):
    model = SubjectEnrollment
    extra = 0
    fields = ('student', 'enrolled_at', 'is_active')
    readonly_fields = ('enrolled_at',)
    raw_id_fields = ('student',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'instructor', 'is_active', 'enrolled_students_count', 'created_at')
    list_filter = ('is_active', 'instructor', 'created_at')
    search_fields = ('name', 'code', 'description', 'instructor__username')
    prepopulated_fields = {'code': ('name',)}
    date_hierarchy = 'created_at'
    inlines = [SubjectMaterialInline, SubjectEnrollmentInline]
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Icons', {
            'fields': ('icon_name', 'background_icon'),
            'description': 'Enter Material Icons names (see https://fonts.google.com/icons)'
        }),
        ('Instructor', {
            'fields': ('instructor',)
        }),
    )

    def enrolled_students_count(self, obj):
        return obj.get_enrolled_students_count()
    enrolled_students_count.short_description = 'Enrolled Students'


@admin.register(SubjectMaterial)
class SubjectMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'material_type', 'is_active', 'created_at')
    list_filter = ('material_type', 'is_active', 'subject', 'created_at')
    search_fields = ('title', 'description', 'subject__name')
    date_hierarchy = 'created_at'
    list_editable = ('is_active',)
    list_per_page = 25

    fieldsets = (
        ('Basic Information', {
            'fields': ('subject', 'title', 'description', 'material_type', 'is_active', 'order', 'content')
        }),
        ('Content', {
            'fields': ('file', 'external_url'),
            'description': 'Upload a file or provide an external URL depending on the material type'
        }),
    )


@admin.register(SubjectEnrollment)
class SubjectEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'enrolled_at', 'is_active')
    list_filter = ('is_active', 'enrolled_at', 'subject')
    search_fields = ('student__username', 'student__email', 'subject__name', 'subject__code')
    date_hierarchy = 'enrolled_at'
    list_editable = ('is_active',)
    raw_id_fields = ('student', 'subject')
    list_per_page = 25
