from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Category, Post, Comment, Bookmark, Notification

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'full_name', 'is_staff', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
        ('Personal info', {'fields': ('full_name',)}),
    )

admin.site.register(User, CustomUserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'author', 'country', 'date']
    search_fields = ['user__email', 'user__username', 'full_name']
    list_filter = ['author']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'image']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'status', 'date']
    search_fields = ['title', 'user__email', 'category__title']
    list_filter = ['status', 'category', 'date']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'name', 'email', 'comment', 'date']
    search_fields = ['post__title', 'name', 'email']
    list_filter = ['date']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'date']
    search_fields = ['user__email', 'post__title']
    list_filter = ['date']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'post', 'seen', 'date']
    search_fields = ['user__email', 'post__title', 'type']
    list_filter = ['seen', 'date']
