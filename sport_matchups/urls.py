from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import GameViewSet, TeamStatViewSet, Login, Logout, send_email_notifications
from .views import game_list, game_detail

# API router
router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'teams', TeamStatViewSet, basename='team')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/login/', Login.as_view(), name='api-login'),
    path('api/logout/', Logout.as_view(), name='api-logout'),

    # Add your email notification endpoint here
    path('api/send-emails/', send_email_notifications, name='send-email-notifications'),

    # Normal views
    path('', game_list, name="game_list"),  # Home page
    path('game/<str:game_id>/', game_detail, name="game_detail"),
]
