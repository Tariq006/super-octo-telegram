from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from pathlib import Path


def message_attachment_path(instance, filename):
    """
    Generate upload path for message attachments
    
    Args:
        instance: The model instance (Message object)
        filename: Original filename of the uploaded file
        
    Returns:
        String path where the file should be stored
    """
    # Create a path like: message_attachments/2025/08/filename.ext
    return Path('message_attachments') / timezone.now().strftime('%Y') / timezone.now().strftime('%m') / filename


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
    return Path('room_media') / timezone.now().strftime('%Y') / timezone.now().strftime('%m') / filename


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
    return Path('avatars') / timezone.now().strftime('%Y') / timezone.now().strftime('%m') / filename


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(unique=True, null=True)
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(null=True, blank=True, default="avatar.svg", upload_to=user_avatar_path)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'base_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email or self.username


class Topic(models.Model):
    name = models.CharField(max_length=200, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'base_topic'
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
        ordering = ['name']

    def __str__(self):
        return self.name


class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hosted_rooms')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, related_name='rooms')
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='participated_rooms', blank=True)
    room_image = models.ImageField(null=True, blank=True, upload_to=room_media_path, 
                                  help_text='Room banner or thumbnail image')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'base_room'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.name

    @property
    def participant_count(self):
        return self.participants.count()


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    body = models.TextField()
    image = models.ImageField(null=True, blank=True, upload_to=message_attachment_path, 
                             help_text='Image attachment')
    document = models.FileField(null=True, blank=True, upload_to=message_attachment_path, 
                               help_text='Document attachment (PDF, DOC, etc.)')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'base_message'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[:50] + ('...' if len(self.body) > 50 else '')

    @property
    def has_attachments(self):
        return bool(self.image or self.document)


class Attachment(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=message_attachment_path)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'base_attachment'
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.file_name} ({self.get_file_type_display()})"