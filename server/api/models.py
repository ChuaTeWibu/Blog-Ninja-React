from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
import shortuuid

# **Custom User Model**
class User(AbstractUser):
    email = models.EmailField(unique=True)  # Email là trường bắt buộc và duy nhất
    full_name = models.CharField(max_length=100, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Chỉ giữ lại username làm trường bổ sung

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        email_username = self.email.split("@")[0]
        if not self.full_name:
            self.full_name = email_username
        if not self.username:
            self.username = email_username
        super().save(*args, **kwargs)


# **Profile Model**
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    image = models.FileField(
        upload_to="images/profiles", 
        default="default/default-user.jpg", 
        null=True, 
        blank=True
    )
    full_name = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    author = models.BooleanField(default=False)
    country = models.CharField(max_length=100, null=True, blank=True)
    facebook = models.URLField(max_length=200, null=True, blank=True)
    twitter = models.URLField(max_length=200, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or self.user.full_name

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.user.full_name
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# **Category Model**
class Category(models.Model):
    title = models.CharField(max_length=100, unique=True)
    image = models.FileField(upload_to="images/categories", null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = slugify(self.title) + "-" + shortuuid.uuid()[:6]
        super().save(*args, **kwargs)


# **Post Model**
class Post(models.Model):
    STATUS = (
        ("Active", "Active"),
        ("Draft", "Draft"),
        ("Disabled", "Disabled"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="images/posts", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    tags = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    status = models.CharField(max_length=10, choices=STATUS, default="Active")
    views = models.IntegerField(default=0)
    likes = models.ManyToManyField(User, blank=True, related_name="liked_posts")
    slug = models.SlugField(unique=True, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{shortuuid.uuid()[:6]}"
        super().save(*args, **kwargs)

    def increment_view_count(self):
        self.views += 1
        self.save()


# **Comment Model**
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    comment = models.TextField()
    reply = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"{self.post.title} - {self.name}"


# **Bookmark Model**
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarked_by")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Bookmarks"
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_bookmark')
        ]

    def __str__(self):
        return f"{self.post.title} - {self.user.username}"


# **Notification Model**
class Notification(models.Model):
    NOTI_TYPE = (
        ("Like", "Like"),
        ("Comment", "Comment"),
        ("Bookmark", "Bookmark"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    type = models.CharField(max_length=10, choices=NOTI_TYPE)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.type} - {self.post.title if self.post else 'General'}"
