from django.contrib import admin

from .models import Team, TeamJoinEvent, University, User

admin.site.register(University)
admin.site.register(Team)
admin.site.register(User)
admin.site.register(TeamJoinEvent)
