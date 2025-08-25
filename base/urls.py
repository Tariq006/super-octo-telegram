from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    # Main pages
    path('', views.home, name="home"),
    path('room/<str:pk>/', views.room, name="room"),
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),

    # Room management
    path('create-room/', views.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views.deleteRoom, name="delete-room"),
    
    # Message management
    path('delete-message/<str:pk>/', views.deleteMessage, name="delete-message"),

    # User management
    path('update-user/', views.updateUser, name="update-user"),

    # Browse pages
    path('topics/', views.topicsPage, name="topics"),
    path('activity/', views.activityPage, name="activity"),

    # AJAX endpoints
    path('join-room/<str:pk>/', views.join_room, name="join-room"),
    path('leave-room/<str:pk>/', views.leave_room, name="leave-room"),
]