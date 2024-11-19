from ninja import NinjaAPI, Schema, UploadedFile
from ninja.router import Router
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from typing import Optional, List
import jwt
from datetime import datetime, timedelta, timezone

from . import schemas
from .models import User, Profile, Category, Post, Comment, Notification


api = NinjaAPI( 
    title='Blog API',
    version='1.0.0',
    description='API for Blog application',
    urls_namespace='blog_api_v1',
    csrf=False,
    docs_url='/docs',
    docs_decorator=None,
    openapi_url='/openapi.json',
)

# Auth Bearer
class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            request.user = user
            return token
        except jwt.ExpiredSignatureError:
            return None
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return None

# Input Schemas
class LoginSchema(Schema):
    email: str
    password: str

class ProfileUpdateSchema(Schema):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    about: Optional[str] = None
    country: Optional[str] = None

class PostCreateSchema(Schema):
    title: str
    description: str
    tags: str
    category_id: int

class PostUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    category_id: Optional[int] = None

class CommentCreateSchema(Schema):
    comment: str

# Auth Routes
@api.post("/auth/register")
def register(request, data: schemas.UserCreateSchema):
    try:
        if User.objects.filter(email=data.email).exists():
            return {"success": False, "message": "Email đã tồn tại"}
        
        if data.password != data.password2:
            return {"success": False, "message": "Mật khẩu không khớp"}
        
        user = User.objects.create(
            email=data.email,
            full_name=data.full_name,
            password=make_password(data.password)
        )
        
        token = jwt.encode(
            {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=7)},
            "your-secret-key",
            algorithm="HS256"
        )
        
        return {
            "success": True,
            "data": {
                "token": token,
                "user": schemas.UserOutSchema.from_orm(user).dict()
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.post("/auth/login")
def login(request, data: LoginSchema):
    try:
        user = authenticate(username=data.email, password=data.password)
        if not user:
            return {"success": False, "message": "Email hoặc mật khẩu không đúng"}
        
        token = jwt.encode(
            {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=7)},
            "your-secret-key",
            algorithm="HS256"
        )
        
        return {
            "success": True,
            "data": {
                "token": token,
                "user": schemas.UserOutSchema.from_orm(user).dict()
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# Profile Routes
@api.get("/profile/{user_id}")
def get_profile(request, user_id: int):
    try:
        profile = get_object_or_404(Profile, user_id=user_id)
        return {
            "success": True,
            "data": schemas.ProfileSchema.from_orm(profile)
        }
    except ObjectDoesNotExist:
        return {"success": False, "message": "Không tìm thấy profile"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.put("/profile", auth=AuthBearer())
def update_profile(request, data: ProfileUpdateSchema, image: Optional[UploadedFile] = None):
    try:
        profile = get_object_or_404(Profile, user=request.user)
        
        if data.full_name:
            profile.full_name = data.full_name
        if data.bio:
            profile.bio = data.bio
        if data.about:
            profile.about = data.about
        if data.country:
            profile.country = data.country
        if image:
            profile.image = image
        
        profile.save()
        return {
            "success": True,
            "data": schemas.ProfileSchema.from_orm(profile).dict()
        }
    except ObjectDoesNotExist:
        return {"success": False, "message": "Không tìm thấy profile"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Category Routes
@api.get("/categories")
def list_categories(request):
    try:
        categories = Category.objects.all()
        return {
            "success": True,
            "data": [schemas.CategorySchema(
                id=cat.id,
                title=cat.title,
                slug=cat.slug,
                image=cat.image.url if cat.image else None,
                post_count=Post.objects.filter(category_id=cat.id).count()
            ).dict() for cat in categories]
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# Post Routes
@api.get("/posts")
def list_posts(request, category_id: Optional[int] = None):
    try:
        posts = Post.objects.all()
        if category_id:
            posts = posts.filter(category_id=category_id)
        
        print(f"Total posts: {posts.count()}")
        
        return {
            "success": True,
            "data": [schemas.PostSchema.from_orm(post).dict() for post in posts.order_by('-date')]
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.post("/posts", auth=AuthBearer())
def create_post(request, data: PostCreateSchema, image: Optional[UploadedFile] = None):
    try:
        post = Post.objects.create(
            user=request.user,
            title=data.title,
            description=data.description,
            tags=data.tags,
            category_id=data.category_id,
            image=image if image else None
        )
        return {
            "success": True,
            "data": schemas.PostSchema.from_orm(post).dict()
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.get("/posts/{slug}")
def get_post(request, slug: str):
    try:
        post = get_object_or_404(Post, slug=slug, status="Active")
        post.views += 1
        post.save()
        return {
            "success": True,
            "data": schemas.PostSchema.from_orm(post)
        }
    except ObjectDoesNotExist:
        return {"success": False, "message": "Không tìm thấy bài viết"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.put("/posts/edit/{post_id}", auth=AuthBearer())
def update_post(request, post_id: int, data: PostUpdateSchema, image: Optional[UploadedFile] = None):
    try:
        post = get_object_or_404(Post, id=post_id, user=request.user)
        if data.title:
            post.title = data.title
        if data.description:
            post.description = data.description
        if data.tags:
            post.tags = data.tags
        if data.category_id:
            post.category_id = data.category_id
        if image:
            post.image = image
        post.save()
        return {
            "success": True,
            "data": schemas.PostSchema.from_orm(post)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.delete("/posts/remove/{post_id}", auth=AuthBearer())
def delete_post(request, post_id: int):
    try:
        post = get_object_or_404(Post, id=post_id, user=request.user)
        post.delete()
        return {"success": True, "message": "Đã xóa bài viết"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Interaction Routes
@api.post("/posts/{post_id}/like", auth=AuthBearer())
def toggle_like(request, post_id: int):
    try:
        post = get_object_or_404(Post, id=post_id)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
            if post.user != request.user:
                Notification.objects.create(
                    user=post.user,
                    post=post,
                    type="Like"
                )
        return {
            "success": True,
            "data": {"liked": liked, "likes_count": post.likes.count()}
        }
    except ObjectDoesNotExist:
        return {"success": False, "message": "Không tìm thấy bài viết"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.post("/posts/{post_id}/comment", auth=AuthBearer())
def create_comment(request, post_id: int, data: CommentCreateSchema):
    try:
        post = get_object_or_404(Post, id=post_id)
        
        # Tạo comment mới
        comment = Comment.objects.create(
            post=post,
            name=request.user.full_name,
            email=request.user.email,
            comment=data.comment
        )
        
        # Tạo notification nếu comment không phải của chủ post
        if post.user != request.user:
            Notification.objects.create(
                user=post.user,
                post=post,
                type="Comment"
            )
        
        # Trả về comment đã được format
        comment_data = {
            "id": comment.id,
            "post_id": comment.post.id,
            "name": comment.name,
            "email": comment.email,
            "comment": comment.comment,
            "reply": comment.reply,
            "date": comment.date.isoformat()  # Convert datetime to string
        }
        
        return {
            "success": True,
            "data": comment_data
        }
    except ObjectDoesNotExist:
        return {"success": False, "message": "Không tìm thấy bài viết"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.get("/posts/{post_id}/comments")
def list_comments(request, post_id: int):
    try:
        comments = Comment.objects.filter(post_id=post_id).order_by('-date')
        
        # Format comments manually
        formatted_comments = [{
            "id": comment.id,
            "post_id": comment.post.id,
            "name": comment.name,
            "email": comment.email,
            "comment": comment.comment,
            "reply": comment.reply,
            "date": comment.date.isoformat()  # Convert datetime to string
        } for comment in comments]
        
        return {
            "success": True,
            "data": formatted_comments
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# Notification Routes
@api.get("/notifications", auth=AuthBearer())
def list_notifications(request):
    try:
        notifications = Notification.objects.filter(
            user=request.user,
            seen=False
        ).order_by('-date')

        # Format notifications manually
        formatted_notifications = [{
            "id": notif.id,
            "user_id": notif.user.id,
            "post_id": notif.post.id if notif.post else None,
            "type": notif.type,
            "seen": notif.seen,
            "date": notif.date.isoformat()
        } for notif in notifications]
        
        return {
            "success": True,
            "data": formatted_notifications
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@api.post("/notifications/{notification_id}/seen", auth=AuthBearer())
def mark_notification_seen(request, notification_id: int):
    try:
        # Tìm notification của user hiện tại
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        
        # Đánh dấu đã đọc
        notification.seen = True
        notification.save()
        
        # Format response
        formatted_notification = {
            "id": notification.id,
            "user_id": notification.user.id,
            "post_id": notification.post.id if notification.post else None,
            "type": notification.type,
            "seen": notification.seen,
            "date": notification.date.isoformat()
        }
        
        return {
            "success": True,
            "data": formatted_notification,
            "message": "Đã đánh dấu là đã đọc"
        }
    except Notification.DoesNotExist:
        return {
            "success": False, 
            "message": "Không tìm thấy thông báo"
        }
    except Exception as e:
        return {
            "success": False, 
            "message": str(e)
        }

# Dashboard Routes
@api.get("/dashboard/stats", auth=AuthBearer())
def get_dashboard_stats(request):
    try:
        return {
            "success": True,
            "data": {
                "total_posts": Post.objects.filter(user=request.user).count(),
                "total_views": Post.objects.filter(user=request.user).aggregate(Sum('views'))['views__sum'] or 0,
                "total_likes": sum(post.likes.count() for post in Post.objects.filter(user=request.user)),
                "total_comments": Comment.objects.filter(post__user=request.user).count()
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

print("Available routes:", api.urls)  # In ra tất cả routes