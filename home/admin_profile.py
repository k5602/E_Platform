from django.contrib import admin
from .models_profile import ProfileUserProfile, ProfileEducation, ProfileExperience, ProfileSkill, ProfileProject, ProfileCertification


@admin.register(ProfileUserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProfileEducation)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'is_visible')
    search_fields = ('user__username', 'institution', 'degree', 'field_of_study')
    list_filter = ('is_visible', 'start_date', 'end_date')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProfileExperience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'position', 'location', 'start_date', 'end_date', 'is_visible')
    search_fields = ('user__username', 'company', 'position', 'location')
    list_filter = ('is_visible', 'start_date', 'end_date')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProfileSkill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'proficiency', 'is_visible')
    search_fields = ('user__username', 'name')
    list_filter = ('is_visible', 'proficiency')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProfileProject)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'start_date', 'end_date', 'is_visible')
    search_fields = ('user__username', 'title', 'description', 'technologies')
    list_filter = ('is_visible', 'start_date', 'end_date')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProfileCertification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'is_visible')
    search_fields = ('user__username', 'name', 'issuing_organization', 'credential_id')
    list_filter = ('is_visible', 'issue_date', 'expiration_date')
    readonly_fields = ('created_at', 'updated_at')
