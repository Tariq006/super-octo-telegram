from rest_framework import serializers
from base.models import Room, Topic, Message, User, Attachment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'email', 'bio', 'avatar', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class TopicSerializer(serializers.ModelSerializer):
    room_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'created', 'room_count']
        read_only_fields = ['id', 'created']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_type', 'file_name', 'file_size', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    has_attachments = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'user', 'body', 'image', 'document', 
            'attachments', 'has_attachments', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class RoomSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'host', 'topic', 'name', 'description', 'room_image',
            'participants', 'participant_count', 'messages', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class RoomListSerializer(serializers.ModelSerializer):
    """Simplified serializer for room listings"""
    host = serializers.StringRelatedField()
    topic = serializers.StringRelatedField()
    participant_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'host', 'topic', 'name', 'description', 'room_image',
            'participant_count', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']