from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Room, Topic, Message, User, Attachment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'username', 'name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('name', 'bio', 'avatar')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('name', 'email', 'bio', 'avatar')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_count', 'created']
    search_fields = ['name']
    ordering = ['name']
    readonly_fields = ['created']
    
    def room_count(self, obj):
        return obj.rooms.count()
    room_count.short_description = 'Number of Rooms'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('rooms')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['created', 'updated']
    fields = ['user', 'body', 'image', 'document', 'created']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'topic', 'participant_count', 'message_count', 'created']
    list_filter = ['topic', 'created', 'updated']
    search_fields = ['name', 'description', 'host__username', 'host__email']
    readonly_fields = ['created', 'updated', 'participant_count', 'message_count']
    filter_horizontal = ['participants']
    inlines = [MessageInline]
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'host', 'topic', 'description']
        }),
        ('Media', {
            'fields': ['room_image'],
            'classes': ['collapse']
        }),
        ('Participants', {
            'fields': ['participants'],
            'classes': ['collapse']
        }),
        ('Statistics', {
            'fields': ['participant_count', 'message_count', 'created', 'updated'],
            'classes': ['collapse']
        })
    ]
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('host', 'topic').prefetch_related('participants')


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['uploaded_at', 'file_size']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['truncated_body', 'user', 'room', 'has_attachments', 'created']
    list_filter = ['created', 'updated', 'room__topic']
    search_fields = ['body', 'user__username', 'user__email', 'room__name']
    readonly_fields = ['created', 'updated', 'has_attachments']
    inlines = [AttachmentInline]
    
    fieldsets = [
        ('Message Content', {
            'fields': ['user', 'room', 'body']
        }),
        ('Attachments', {
            'fields': ['image', 'document', 'has_attachments'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created', 'updated'],
            'classes': ['collapse']
        })
    ]
    
    def truncated_body(self, obj):
        return obj.body[:50] + ('...' if len(obj.body) > 50 else '')
    truncated_body.short_description = 'Message'
    
    def has_attachments(self, obj):
        return obj.has_attachments
    has_attachments.boolean = True
    has_attachments.short_description = 'Has Attachments'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'room', 'room__topic')


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_type', 'message_user', 'message_room', 'file_size_display', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_name', 'message__user__username', 'message__room__name']
    readonly_fields = ['uploaded_at', 'file_size']
    
    def message_user(self, obj):
        return obj.message.user.username
    message_user.short_description = 'User'
    
    def message_room(self, obj):
        return obj.message.room.name
    message_room.short_description = 'Room'
    
    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'File Size'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message__user', 'message__room')


# Customize admin site
admin.site.site_header = "StudyBud Administration"
admin.site.site_title = "StudyBud Admin"
admin.site.index_title = "Welcome to StudyBud Administration"