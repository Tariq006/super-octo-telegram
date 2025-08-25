from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from base.models import Room, Topic, Message, User
from .serializers import (
    RoomSerializer, RoomListSerializer, TopicSerializer, 
    MessageSerializer, UserSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def getRoutes(request):
    """API routes overview"""
    routes = [
        'GET /api/',
        'GET /api/rooms/',
        'GET /api/rooms/:id/',
        'GET /api/topics/',
        'GET /api/messages/',
        'GET /api/users/',
        'GET /api/users/:id/',
    ]
    return Response(routes)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def getRooms(request):
    """Get all rooms with optional search and pagination"""
    search_query = request.GET.get('q', '')
    
    rooms_queryset = Room.objects.select_related('host', 'topic').prefetch_related('participants')
    
    if search_query:
        rooms_queryset = rooms_queryset.filter(
            Q(topic__name__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Add participant count annotation
    rooms_queryset = rooms_queryset.annotate(participant_count=Count('participants'))
    rooms_queryset = rooms_queryset.order_by('-updated')
    
    # Pagination
    paginator = StandardResultsSetPagination()
    paginated_rooms = paginator.paginate_queryset(rooms_queryset, request)
    
    serializer = RoomListSerializer(paginated_rooms, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def getRoom(request, pk):
    """Get a specific room with all details"""
    try:
        room = Room.objects.select_related('host', 'topic').prefetch_related(
            'participants', 'messages__user'
        ).annotate(participant_count=Count('participants')).get(id=pk)
    except Room.DoesNotExist:
        return Response(
            {'error': 'Room not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = RoomSerializer(room)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def getTopics(request):
    """Get all topics with room counts"""
    search_query = request.GET.get('q', '')
    
    topics_queryset = Topic.objects.annotate(room_count=Count('rooms'))
    
    if search_query:
        topics_queryset = topics_queryset.filter(name__icontains=search_query)
    
    topics_queryset = topics_queryset.order_by('-room_count', 'name')
    
    serializer = TopicSerializer(topics_queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def getMessages(request):
    """Get recent messages with optional filtering"""
    room_id = request.GET.get('room')
    
    messages_queryset = Message.objects.select_related('user', 'room', 'room__topic')
    
    if room_id:
        messages_queryset = messages_queryset.filter(room_id=room_id)
    
    messages_queryset = messages_queryset.order_by('-created')
    
    # Pagination
    paginator = StandardResultsSetPagination()
    paginated_messages = paginator.paginate_queryset(messages_queryset, request)
    
    serializer = MessageSerializer(paginated_messages, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def getUsers(request):
    """Get all users"""
    search_query = request.GET.get('q', '')
    
    users_queryset = User.objects.all()
    
    if search_query:
        users_queryset = users_queryset.filter(
            Q(username__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    users_queryset = users_queryset.order_by('-date_joined')
    
    # Pagination
    paginator = StandardResultsSetPagination()
    paginated_users = paginator.paginate_queryset(users_queryset, request)
    
    serializer = UserSerializer(paginated_users, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def getUser(request, pk):
    """Get a specific user"""
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createRoom(request):
    """Create a new room"""
    serializer = RoomSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(host=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createMessage(request, room_pk):
    """Create a new message in a room"""
    try:
        room = Room.objects.get(id=room_pk)
    except Room.DoesNotExist:
        return Response(
            {'error': 'Room not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        message = serializer.save(user=request.user, room=room)
        room.participants.add(request.user)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)