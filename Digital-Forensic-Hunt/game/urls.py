from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.index,            name='index'),
    path('login/',                    views.login_view,       name='login'),
    path('register/',                 views.register_view,    name='register'),
    path('logout/',                   views.logout_view,      name='logout'),
    path('game/',                     views.game_view,        name='game'),
    path('leaderboard/',              views.leaderboard_view, name='leaderboard'),
    # JSON API
    path('api/mission/<int:n>/',      views.api_mission,      name='api_mission'),
    path('api/submit/',               views.api_submit,       name='api_submit'),
    path('api/hint/',                 views.api_hint,         name='api_hint'),
    path('api/clue/',                 views.api_clue,         name='api_clue'),
    path('api/violation/',            views.api_violation,    name='api_violation'),
    path('api/session/start/',        views.api_session_start,name='api_session_start'),
    path('api/session/end/',          views.api_session_end,  name='api_session_end'),
    path('api/leaderboard/',          views.api_leaderboard,  name='api_leaderboard'),
]
