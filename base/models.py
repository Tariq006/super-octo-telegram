from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from django.utils import timezone


def message_attachment_path(instance, filename):
    """
    Generate upload path for message attachments
    
    Args:
        instance: The model instance (Message object)
        filename: Original filename of the uploaded file
        
    Returns:
        String path where the file should be stored
    """
    # Get file extension
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    # Create a path like: message_attachments/2025/08/filename.ext
    return os.path.join(
        'message_attachments',
        timezone.now().strftime('%Y'),
        timezone.now().strftime('%m'),
        filename
    )


def room_media_path(instance, filename):
    """
    Generate upload path for room media (banners, thumbnails, etc.)
    
    Args:
        instance: The model instance (Room object)
        filename: Original filename of the uploaded file
        
    Returns:
        String path where the file should be stored
    """
    # Create a path like: room_media/2025/08/filename.ext
    return os.path.join(
        'room_media',
        timezone.now().strftime('%Y'),
        timezone.now().strftime('%m'),
        filename
    )


def user_avatar_path(instance, filename):
    """
    Generate upload path for user avatar images
    
    Args:
        instance: The model instance (User object)
        filename: Original filename of the uploaded file
        
    Returns:
        String path where the file should be stored
    """
    # Create a path like: avatars/2025/08/filename.ext
    return os.path.join(
        'avatars',
        timezone.now().strftime('%Y'),
        timezone.now().strftime('%m'),
        filename
    )


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)
    bio = models.TextField(null=True)

    avatar = models.ImageField(null=True, default="avatar.svg")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Topic(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(
        User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[0:50]