from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from .models import (Mission, MissionFile, MissionLog, PlayerProfile,
                     GameSession, MissionAttempt, ViolationLog, LeaderboardEntry)

# ── Branding ─────────────────────────────────────────────────
admin.site.site_header  = '⌬ SYS://TRACE — NEXUS COMMAND'
admin.site.site_title   = 'NEXUS Admin'
admin.site.index_title  = 'NEXUS Operations Dashboard'


class MissionFileInline(admin.TabularInline):
    model  = MissionFile
    extra  = 1
    fields = ['path', 'filename', 'has_clue', 'clue_tag']
    show_change_link = True


class MissionLogInline(admin.TabularInline):
    model  = MissionLog
    extra  = 1
    fields = ['order', 'time_label', 'level', 'message']


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display  = ['order', 'code', 'title', 'diff_badge', 'level_group',
                     'time_limit', 'hint_cost', 'is_active', 'solve_rate']
    list_filter   = ['difficulty', 'level_group', 'is_active']
    search_fields = ['title', 'code', 'brief']
    list_editable = ['is_active']
    ordering      = ['order']
    inlines       = [MissionFileInline, MissionLogInline]
    fieldsets     = (
        ('Identity',    {'fields': ('order','code','title','level_group','difficulty','is_active')}),
        ('Content',     {'fields': ('brief','target_hint','hint_text')}),
        ('Game Config', {'fields': ('answer','time_limit','hint_cost','total_clues')}),
    )

    def diff_badge(self, obj):
        c = {'ROOKIE':'#00ff88','AGENT':'#00e5ff','SPECIALIST':'#ffcc00','EXPERT':'#ff7700','ELITE':'#ff3355'}
        return format_html('<b style="color:{}">{}</b>', c.get(obj.difficulty,'#888'), obj.difficulty)
    diff_badge.short_description = 'Difficulty'

    def solve_rate(self, obj):
        total  = MissionAttempt.objects.filter(mission=obj).count()
        if not total: return format_html('<span style="color:#555">—</span>')
        solved = MissionAttempt.objects.filter(mission=obj, solved=True).count()
        pct    = int(solved / total * 100)
        c      = '#00ff88' if pct >= 60 else '#ffcc00' if pct >= 30 else '#ff3355'
        return format_html('<span style="color:{}">{}/{} ({}%)</span>', c, solved, total, pct)
    solve_rate.short_description = 'Solve Rate'


@admin.register(MissionFile)
class MissionFileAdmin(admin.ModelAdmin):
    list_display  = ['mission', 'path', 'filename', 'has_clue', 'clue_tag']
    list_filter   = ['mission', 'has_clue', 'clue_tag']
    search_fields = ['path', 'filename', 'content']


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display  = ['operative_name', 'user', 'best_score', 'total_score',
                     'missions_completed', 'games_played', 'rank_badge', 'created_at']
    search_fields = ['operative_name', 'user__username']
    readonly_fields = ['total_score', 'best_score', 'missions_completed',
                       'games_played', 'created_at']

    def rank_badge(self, obj):
        s = obj.best_score
        if s >= 5000: return format_html('<b style="color:#ff3355">★ SOVEREIGN ANALYST</b>')
        if s >= 3000: return format_html('<b style="color:#ff7700">◆ ELITE OPERATIVE</b>')
        if s >= 1500: return format_html('<b style="color:#ffcc00">▲ SPECIALIST</b>')
        if s >= 500:  return format_html('<b style="color:#00e5ff">▸ AGENT</b>')
        return format_html('<span style="color:#00ff88">○ ROOKIE</span>')
    rank_badge.short_description = 'Rank'


class MissionAttemptInline(admin.TabularInline):
    model         = MissionAttempt
    extra         = 0
    readonly_fields = ['mission','started_at','completed_at','solved','score_earned',
                       'time_taken','wrong_attempts','hint_used']
    can_delete    = False


class ViolationLogInline(admin.TabularInline):
    model         = ViolationLog
    extra         = 0
    readonly_fields = ['timestamp','event_type','penalty','severity']
    can_delete    = False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display  = ['player','started_at','status_badge','final_score',
                     'missions_completed','integrity_bar','violations','duration_fmt']
    list_filter   = ['status','started_at']
    search_fields = ['player__operative_name']
    readonly_fields = ['player','started_at','ended_at','final_score',
                       'missions_completed','violations','integrity']
    inlines       = [MissionAttemptInline, ViolationLogInline]

    def status_badge(self, obj):
        c = {'active':'#ffcc00','completed':'#00ff88','failed':'#ff3355'}
        return format_html('<b style="color:{}">{}</b>', c.get(obj.status,'#888'), obj.status.upper())
    status_badge.short_description = 'Status'

    def integrity_bar(self, obj):
        v = obj.integrity
        c = '#00ff88' if v >= 70 else '#ffcc00' if v >= 40 else '#ff3355'
        return format_html(
            '<div style="width:80px;background:#222;border-radius:3px">'
            '<div style="width:{}%;background:{};height:10px;border-radius:3px"></div>'
            '</div> {}%', v, c, v)
    integrity_bar.short_description = 'Integrity'

    def duration_fmt(self, obj):
        if obj.ended_at:
            m, s = divmod(int((obj.ended_at - obj.started_at).total_seconds()), 60)
            return f'{m}m {s}s'
        return '—'
    duration_fmt.short_description = 'Duration'


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display  = ['rank_pos','player','score','missions_completed',
                     'integrity','time_fmt','achieved_at']
    list_filter   = ['achieved_at']
    search_fields = ['player__operative_name']
    readonly_fields = ['player','session','score','missions_completed',
                       'integrity','time_taken','achieved_at']
    ordering      = ['-score','time_taken']

    def rank_pos(self, obj):
        rank = list(LeaderboardEntry.objects.order_by('-score','time_taken')
                    .values_list('id',flat=True)).index(obj.id) + 1
        medals = {1:'🥇',2:'🥈',3:'🥉'}
        return format_html('{} <b>#{}</b>', medals.get(rank,''), rank)
    rank_pos.short_description = '#'

    def time_fmt(self, obj):
        m, s = divmod(obj.time_taken, 60)
        return f'{m}m {s}s'
    time_fmt.short_description = 'Time'


@admin.register(ViolationLog)
class ViolationLogAdmin(admin.ModelAdmin):
    list_display  = ['session','timestamp','event_type','severity','penalty']
    list_filter   = ['severity','timestamp']
    search_fields = ['session__player__operative_name','event_type']
