from django.urls import path
from .views import api

urlpatterns = [
    # Auth Routes
    path('auth/register', api.register),          # POST /auth/register
    path('auth/login', api.login),               # POST /auth/login

    # Profile Routes 
    path('profile/<int:user_id>', api.get_profile),  # GET /profile/{user_id}
    path('profile', api.update_profile),             # PUT /profile

    # Category Routes
    path('categories', api.list_categories),      # GET /categories

    # Post Routes
    path('posts', api.list_posts),               # GET /posts
    path('posts', api.create_post),              # POST /posts
    path('posts/<str:slug>', api.get_post),      # GET /posts/{slug}
    path('posts/edit/<int:post_id>', api.update_post),  # PUT /posts/edit/{post_id}
    path('posts/remove/<int:post_id>', api.delete_post), # DELETE /posts/remove/{post_id}

    # Interaction Routes
    path('posts/<int:post_id>/like', api.toggle_like),      # POST /posts/{post_id}/like
    path('posts/<int:post_id>/comment', api.create_comment), # POST /posts/{post_id}/comment
    path('posts/<int:post_id>/comments', api.list_comments), # GET /posts/{post_id}/comments

    # Notification Routes
    path('notifications', api.list_notifications),           # GET /notifications
    path('notifications/<int:notification_id>/seen', api.mark_notification_seen), # POST /notifications/{notification_id}/seen

    # Dashboard Routes
    path('dashboard/stats', api.get_dashboard_stats),        # GET /dashboard/stats
]
