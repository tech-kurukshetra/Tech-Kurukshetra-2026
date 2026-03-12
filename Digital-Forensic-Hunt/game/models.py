from django.db import models
from django.contrib.auth.models import User


class Mission(models.Model):
    DIFF = [('ROOKIE','Rookie'),('AGENT','Agent'),('SPECIALIST','Specialist'),('EXPERT','Expert'),('ELITE','Elite')]
    order        = models.PositiveIntegerField(unique=True)
    code         = models.CharField(max_length=10)
    title        = models.CharField(max_length=200)
    level_group  = models.CharField(max_length=100)
    difficulty   = models.CharField(max_length=20, choices=DIFF)
    brief        = models.TextField()
    target_hint  = models.CharField(max_length=300)
    answer       = models.CharField(max_length=200)   # stored lowercase
    time_limit   = models.PositiveIntegerField(default=300)
    hint_text    = models.TextField()
    hint_cost    = models.PositiveIntegerField(default=150)
    total_clues  = models.PositiveIntegerField(default=4)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.code} — {self.title}"


class MissionFile(models.Model):
    mission   = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='files')
    path      = models.CharField(max_length=500)
    filename  = models.CharField(max_length=200)
    content   = models.TextField()
    has_clue  = models.BooleanField(default=False)
    clue_tag  = models.CharField(max_length=30, blank=True)
    clue_text = models.TextField(blank=True)

    class Meta:
        ordering = ['path', 'filename']

    def __str__(self):
        return f"{self.mission.code} | {self.path}/{self.filename}"


class MissionLog(models.Model):
    LEVELS = [('INFO','INFO'),('WARN','WARN'),('ERR','ERR'),('CRIT','CRIT')]
    mission    = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='logs')
    order      = models.PositiveIntegerField(default=0)
    time_label = models.CharField(max_length=20)
    level      = models.CharField(max_length=10, choices=LEVELS)
    message    = models.CharField(max_length=500)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.mission.code} | {self.level} | {self.message[:50]}"


class PlayerProfile(models.Model):
    user               = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    operative_name     = models.CharField(max_length=50, unique=True)
    total_score        = models.IntegerField(default=0)
    best_score         = models.IntegerField(default=0)
    missions_completed = models.PositiveIntegerField(default=0)
    games_played       = models.PositiveIntegerField(default=0)
    created_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.operative_name} ({self.user.username})"

    @property
    def rank(self):
        s = self.best_score
        if s >= 5000: return 'SOVEREIGN ANALYST'
        if s >= 3000: return 'ELITE OPERATIVE'
        if s >= 1500: return 'SPECIALIST'
        if s >= 500:  return 'AGENT'
        return 'ROOKIE'


class GameSession(models.Model):
    STATUS = [('active','Active'),('completed','Completed'),('failed','Failed')]
    player             = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='sessions')
    started_at         = models.DateTimeField(auto_now_add=True)
    ended_at           = models.DateTimeField(null=True, blank=True)
    final_score        = models.IntegerField(default=0)
    missions_completed = models.PositiveIntegerField(default=0)
    status             = models.CharField(max_length=20, choices=STATUS, default='active')
    violations         = models.PositiveIntegerField(default=0)
    integrity          = models.PositiveIntegerField(default=100)

    def __str__(self):
        return f"{self.player.operative_name} | {self.started_at.date()} | {self.final_score}pts"

    @property
    def duration_seconds(self):
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return 0


class MissionAttempt(models.Model):
    session         = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='attempts')
    mission         = models.ForeignKey(Mission, on_delete=models.CASCADE)
    started_at      = models.DateTimeField(auto_now_add=True)
    completed_at    = models.DateTimeField(null=True, blank=True)
    solved          = models.BooleanField(default=False)
    score_earned    = models.IntegerField(default=0)
    time_taken      = models.PositiveIntegerField(default=0)
    wrong_attempts  = models.PositiveIntegerField(default=0)
    hint_used       = models.BooleanField(default=False)
    clues_found     = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.session.player.operative_name} | {self.mission.code} | {'✓' if self.solved else '✗'}"


class ViolationLog(models.Model):
    session    = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='violation_logs')
    timestamp  = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=100)
    penalty    = models.PositiveIntegerField(default=0)
    severity   = models.CharField(max_length=10, default='low')

    def __str__(self):
        return f"{self.session.player.operative_name} | {self.event_type}"


class LeaderboardEntry(models.Model):
    player             = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='lb_entries')
    session            = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    score              = models.IntegerField()
    missions_completed = models.PositiveIntegerField()
    integrity          = models.PositiveIntegerField()
    time_taken         = models.PositiveIntegerField(default=0)
    achieved_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'time_taken']

    def __str__(self):
        return f"{self.player.operative_name} | {self.score}pts"
