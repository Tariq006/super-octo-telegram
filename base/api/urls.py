from django.urls import path
from . import views

urlpatterns = [
    # API overview
    path('', views.getRoutes, name='api-routes'),
    
    # Rooms
    path('rooms/', views.getRooms, name='api-rooms'),
    path('rooms/<str:pk>/', views.getRoom, name='api-room'),
    path('rooms/create/', views.createRoom, name='api-create-room'),
    
    # Topics
    path('topics/', views.getTopics, name='api-topics'),
    
    # Messages
    path('messages/', views.getMessages, name='api-messages'),
    path('rooms/<str:room_pk>/messages/create/', views.createMessage, name='api-create-message'),
    
    # Users
    path('users/', views.getUsers, name='api-users'),
    path('users/<str:pk>/', views.getUser, name='api-user'),
]