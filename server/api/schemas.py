from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Schema cho việc tạo tài khoản mới
class UserCreateSchema(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    password2: str

    class Config:
        from_attributes = True

    def validate(self):
        if self.password != self.password2:
            raise ValueError("Password fields didn't match.")
        return self

class UserOutSchema(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileSchema(BaseModel):
    user_id: int
    image: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    about: Optional[str] = None
    author: bool = False
    country: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    date: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            user_id=obj.user.id,
            image=obj.image.url if obj.image else None,
            full_name=obj.full_name,
            bio=obj.bio,
            about=obj.about,
            author=obj.author,
            country=obj.country,
            facebook=obj.facebook,
            twitter=obj.twitter,
            date=obj.date.isoformat()
        )

class CategorySchema(BaseModel):
    id: int
    title: str
    image: Optional[str] = None
    slug: Optional[str] = None
    post_count: int

    class Config:
        from_attributes = True
        
class PostSchema(BaseModel):
    id: int
    user_id: int
    title: str
    image: Optional[str] = None
    description: Optional[str] = None
    tags: str
    category_id: Optional[int] = None
    status: str
    views: int = 0
    likes: list[int] = []
    slug: Optional[str] = None
    date: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            user_id=obj.user.id,
            title=obj.title,
            image=obj.image.url if obj.image else None,
            description=obj.description,
            tags=obj.tags,
            category_id=obj.category_id,
            status=obj.status,
            views=obj.views,
            likes=[user.id for user in obj.likes.all()],
            slug=obj.slug,
            date=obj.date.isoformat()
        )

class CommentSchema(BaseModel):
    id: int
    post_id: int
    name: str
    email: str
    comment: str
    reply: Optional[str] = None
    date: str

    class Config:
        from_attributes = True

class BookmarkSchema(BaseModel):
    id: int
    user_id: int
    post_id: int
    date: str

    class Config:
        from_attributes = True

class NotificationSchema(BaseModel):
    id: int
    user_id: int
    post_id: int
    type: str
    seen: bool
    date: str

    class Config:
        from_attributes = True
