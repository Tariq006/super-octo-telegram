from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Prefetch
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm, MessageForm
import logging

logger = logging.getLogger(__name__)


@csrf_protect
def loginPage(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'base/login_register.html', {'page': 'login'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist.')
            return render(request, 'base/login_register.html', {'page': 'login'})

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')

    context = {'page': 'login'}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@csrf_protect
def registerPage(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('home')

    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.username = user.username.lower()
                user.save()
                login(request, user)
                messages.success(request, f'Welcome {user.name or user.username}! Your account has been created.')
                return redirect('home')
            except Exception as e:
                logger.error(f"Registration error: {e}")
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f"Registration error: {error}")
                    else:
                        messages.error(request, f"{field.replace('_', ' ').title()}: {error}")

    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    """Home page with room listings and search"""
    q = request.GET.get('q', '').strip()
    
    # Build query for rooms
    rooms_query = Room.objects.select_related('host', 'topic').prefetch_related('participants')
    
    if q:
        rooms_query = rooms_query.filter(
            Q(topic__name__icontains=q) |
            Q(name__icontains=q) |
            Q(description__icontains=q)
        )

    # Pagination
    paginator = Paginator(rooms_query, 10)  # Show 10 rooms per page
    page_number = request.GET.get('page')
    rooms = paginator.get_page(page_number)

    # Get topics with room counts
    topics = Topic.objects.annotate(room_count=Count('rooms')).order_by('-room_count')[:5]
    
    room_count = rooms_query.count()
    
    # Recent messages
    recent_messages_query = Message.objects.select_related('user', 'room', 'room__topic')
    if q:
        recent_messages_query = recent_messages_query.filter(room__topic__name__icontains=q)
    
    room_messages = recent_messages_query[:3]

    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
        'search_query': q
    }
    return render(request, 'base/home.html', context)


def room(request, pk):
    """Room detail view with messages"""
    room = get_object_or_404(
        Room.objects.select_related('host', 'topic').prefetch_related('participants'),
        id=pk
    )
    
    room_messages = room.messages.select_related('user').order_by('created')
    participants = room.participants.all()

    if request.method == 'POST' and request.user.is_authenticated:
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.user = request.user
            message.room = room
            message.save()
            room.participants.add(request.user)
            messages.success(request, 'Message sent successfully!')
            return redirect('room', pk=room.id)
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = MessageForm()

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
        'form': form
    }
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    """User profile view"""
    user = get_object_or_404(User, id=pk)
    rooms = user.hosted_rooms.select_related('topic').annotate(
        participant_count=Count('participants')
    )
    room_messages = user.messages.select_related('room')[:10]
    topics = Topic.objects.all()
    
    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics
    }
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
@csrf_protect
def createRoom(request):
    """Create a new room"""
    form = RoomForm()
    topics = Topic.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            
            # Handle topic creation/selection
            topic_name = form.cleaned_data['topic']
            topic, created = Topic.objects.get_or_create(name=topic_name)
            room.topic = topic
            
            room.save()
            messages.success(request, f'Room "{room.name}" created successfully!')
            return redirect('room', pk=room.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
@csrf_protect
def updateRoom(request, pk):
    """Update an existing room"""
    room = get_object_or_404(Room, id=pk)
    
    if request.user != room.host:
        return HttpResponseForbidden('You are not allowed to edit this room.')

    form = RoomForm(instance=room)
    topics = Topic.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            room = form.save(commit=False)
            
            # Handle topic creation/selection
            topic_name = form.cleaned_data['topic']
            topic, created = Topic.objects.get_or_create(name=topic_name)
            room.topic = topic
            
            room.save()
            messages.success(request, f'Room "{room.name}" updated successfully!')
            return redirect('room', pk=room.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def deleteRoom(request, pk):
    """Delete a room"""
    room = get_object_or_404(Room, id=pk)

    if request.user != room.host:
        return HttpResponseForbidden('You are not allowed to delete this room.')

    if request.method == 'POST':
        room_name = room.name
        room.delete()
        messages.success(request, f'Room "{room_name}" deleted successfully!')
        return redirect('home')
        
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def deleteMessage(request, pk):
    """Delete a message"""
    message = get_object_or_404(Message, id=pk)

    if request.user != message.user and request.user != message.room.host:
        return HttpResponseForbidden('You are not allowed to delete this message.')

    room_id = message.room.id
    
    if request.method == 'POST':
        message.delete()
        messages.success(request, 'Message deleted successfully!')
        return redirect('room', pk=room_id)
        
    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
@csrf_protect
def updateUser(request):
    """Update user profile"""
    form = UserForm(instance=request.user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user-profile', pk=request.user.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")

    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):
    """Topics listing page"""
    q = request.GET.get('q', '').strip()
    
    topics_query = Topic.objects.annotate(room_count=Count('rooms'))
    
    if q:
        topics_query = topics_query.filter(name__icontains=q)
    
    topics = topics_query.order_by('-room_count', 'name')
    
    context = {'topics': topics, 'search_query': q}
    return render(request, 'base/topics.html', context)


def activityPage(request):
    """Recent activity page"""
    room_messages = Message.objects.select_related('user', 'room', 'room__topic').order_by('-created')[:20]
    
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)


# API-like views for AJAX requests
@login_required
def join_room(request, pk):
    """Join a room via AJAX"""
    if request.method == 'POST':
        room = get_object_or_404(Room, id=pk)
        room.participants.add(request.user)
        return JsonResponse({'status': 'success', 'message': 'Joined room successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


@login_required
def leave_room(request, pk):
    """Leave a room via AJAX"""
    if request.method == 'POST':
        room = get_object_or_404(Room, id=pk)
        room.participants.remove(request.user)
        return JsonResponse({'status': 'success', 'message': 'Left room successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})