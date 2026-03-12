import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Max, Avg, Count, Sum
from .models import (Mission, MissionFile, MissionLog, PlayerProfile,
                     GameSession, MissionAttempt, ViolationLog, LeaderboardEntry)


# ── Auth ────────────────────────────────────────────────────

def index(request):
    return redirect('game' if request.user.is_authenticated else 'login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('game')
    error = None
    if request.method == 'POST':
        user = authenticate(request,
                            username=request.POST.get('username','').strip(),
                            password=request.POST.get('password',''))
        if user:
            login(request, user); return redirect('game')
        error = 'Invalid credentials — access denied.'
    return render(request, 'game/login.html', {'error': error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('game')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username','').strip()
        password = request.POST.get('password','')
        confirm  = request.POST.get('confirm','')
        op_name  = request.POST.get('operative_name','').strip().upper()
        if not all([username, password, op_name]):
            error = 'All fields required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif User.objects.filter(username=username).exists():
            error = 'Username already taken.'
        elif PlayerProfile.objects.filter(operative_name=op_name).exists():
            error = 'Operative name already in use.'
        else:
            user = User.objects.create_user(username=username, password=password)
            PlayerProfile.objects.create(user=user, operative_name=op_name)
            login(request, user); return redirect('game')
    return render(request, 'game/register.html', {'error': error})


def logout_view(request):
    logout(request); return redirect('login')


# ── Game ────────────────────────────────────────────────────

@login_required
def game_view(request):
    profile = request.user.profile
    total   = Mission.objects.filter(is_active=True).count()
    return render(request, 'game/game.html', {'profile': profile, 'total_missions': total})


# ── Leaderboard ─────────────────────────────────────────────

def leaderboard_view(request):
    entries = LeaderboardEntry.objects.select_related('player','session').order_by('-score','time_taken')[:50]
    stats = {
        'total_players': PlayerProfile.objects.count(),
        'total_games':   GameSession.objects.filter(status='completed').count(),
        'avg_score':     int(LeaderboardEntry.objects.aggregate(a=Avg('score'))['a'] or 0),
        'top_score':     LeaderboardEntry.objects.aggregate(m=Max('score'))['m'] or 0,
    }
    player_entry = None
    if request.user.is_authenticated:
        try:
            player_entry = LeaderboardEntry.objects.filter(
                player=request.user.profile).order_by('-score').first()
        except Exception:
            pass
    return render(request, 'game/leaderboard.html',
                  {'entries': entries, 'stats': stats, 'player_entry': player_entry})


# ── API: Mission data ────────────────────────────────────────

@login_required
def api_mission(request, n):
    mission = get_object_or_404(Mission, order=n, is_active=True)
    files   = MissionFile.objects.filter(mission=mission)
    fs = {}
    for f in files:
        parts = f.path.strip('/').split('/') if f.path.strip('/') else []
        node  = fs
        for part in parts:
            node = node.setdefault(part, {})
        node[f.filename] = {
            'content': f.content,
            'clue': {'tag': f.clue_tag, 'text': f.clue_text} if f.has_clue else None,
        }
    logs = [{'time': l.time_label, 'level': l.level, 'msg': l.message}
            for l in MissionLog.objects.filter(mission=mission)]
    return JsonResponse({
        'id': mission.order, 'code': mission.code, 'title': mission.title,
        'levelGroup': mission.level_group, 'difficulty': mission.difficulty,
        'brief': mission.brief, 'targetHint': mission.target_hint,
        'timeLimit': mission.time_limit, 'hintCost': mission.hint_cost,
        'totalClues': mission.total_clues, 'fileSystem': fs, 'logs': logs,
    })


# ── API: Submit answer ───────────────────────────────────────

@login_required
@require_POST
def api_submit(request):
    d            = json.loads(request.body)
    mission      = get_object_or_404(Mission, order=d.get('missionId'), is_active=True)
    answer       = d.get('answer','').strip().lower()
    time_left    = d.get('timeLeft', 0)
    clues_found  = d.get('cluesFound', 0)
    wrong        = d.get('wrongAttempts', 0)
    session_id   = d.get('sessionId')
    cur_score    = d.get('currentScore', 0)

    if answer == mission.answer.lower():
        earned = max(0, 200 + time_left * 2 + clues_found * 25 - wrong * 30)
        try:
            session = GameSession.objects.get(id=session_id, player=request.user.profile)
            att, _  = MissionAttempt.objects.get_or_create(
                session=session, mission=mission, defaults={'started_at': timezone.now()})
            att.solved = True; att.score_earned = earned
            att.time_taken = mission.time_limit - time_left
            att.wrong_attempts = wrong; att.clues_found = clues_found
            att.completed_at = timezone.now(); att.save()
            session.missions_completed += 1
            session.final_score = cur_score + earned; session.save()
        except Exception:
            pass
        return JsonResponse({'correct': True, 'earned': earned})
    return JsonResponse({'correct': False})


# ── API: Hint ────────────────────────────────────────────────

@login_required
@require_POST
def api_hint(request):
    d       = json.loads(request.body)
    mission = get_object_or_404(Mission, order=d.get('missionId'))
    try:
        session = GameSession.objects.get(id=d.get('sessionId'), player=request.user.profile)
        att, _ = MissionAttempt.objects.get_or_create(
            session=session, mission=mission, defaults={'started_at': timezone.now()})
        att.hint_used = True; att.save()
    except Exception:
        pass
    return JsonResponse({'hint': mission.hint_text, 'cost': mission.hint_cost})


# ── API: Collect clue ────────────────────────────────────────

@login_required
@require_POST
def api_clue(request):
    d = json.loads(request.body)
    try:
        session = GameSession.objects.get(id=d.get('sessionId'), player=request.user.profile)
        mission = Mission.objects.get(order=d.get('missionId'))
        att, _ = MissionAttempt.objects.get_or_create(
            session=session, mission=mission, defaults={'started_at': timezone.now()})
        att.clues_found = d.get('cluesFound', 0); att.save()
    except Exception:
        pass
    return JsonResponse({'ok': True})


# ── API: Log violation ───────────────────────────────────────

@login_required
@require_POST
def api_violation(request):
    d = json.loads(request.body)
    try:
        session = GameSession.objects.get(id=d.get('sessionId'), player=request.user.profile)
        ViolationLog.objects.create(
            session=session, event_type=d.get('eventType',''),
            penalty=d.get('penalty',0), severity=d.get('severity','low'))
        session.violations += 1
        session.integrity = max(0, session.integrity - max(1, d.get('penalty',0)//10))
        session.save()
    except Exception:
        pass
    return JsonResponse({'ok': True})


# ── API: Session start ───────────────────────────────────────

@login_required
@require_POST
def api_session_start(request):
    profile = request.user.profile
    GameSession.objects.filter(player=profile, status='active').update(status='failed')
    session = GameSession.objects.create(player=profile, status='active')
    profile.games_played += 1; profile.save()
    return JsonResponse({'sessionId': session.id})


# ── API: Session end ─────────────────────────────────────────

@login_required
@require_POST
def api_session_end(request):
    d          = json.loads(request.body)
    score      = d.get('finalScore', 0)
    missions   = d.get('missionsCompleted', 0)
    violations = d.get('violations', 0)
    time_taken = d.get('timeTaken', 0)
    status     = d.get('status', 'completed')
    try:
        session = GameSession.objects.get(id=d.get('sessionId'), player=request.user.profile)
        session.final_score = score; session.missions_completed = missions
        session.violations  = violations
        session.integrity   = max(0, 100 - violations * 5)
        session.status      = status; session.ended_at = timezone.now(); session.save()
        profile = request.user.profile
        profile.total_score += score
        profile.missions_completed = max(profile.missions_completed, missions)
        if score > profile.best_score: profile.best_score = score
        profile.save()
        if status == 'completed' and missions > 0:
            LeaderboardEntry.objects.create(
                player=profile, session=session, score=score,
                missions_completed=missions, integrity=session.integrity,
                time_taken=time_taken)
    except Exception:
        pass
    return JsonResponse({'ok': True})


# ── API: Leaderboard ─────────────────────────────────────────

def api_leaderboard(request):
    entries = LeaderboardEntry.objects.select_related('player').order_by('-score','time_taken')[:20]
    data = []
    for i, e in enumerate(entries, 1):
        m, s = divmod(e.time_taken, 60)
        data.append({
            'rank': i, 'operative': e.player.operative_name,
            'score': e.score, 'missions': e.missions_completed,
            'integrity': e.integrity, 'time': f'{m}m {s}s',
            'date': e.achieved_at.strftime('%Y-%m-%d'),
        })
    return JsonResponse({'entries': data})
