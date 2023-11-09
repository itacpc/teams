from django.contrib import admin

from .models import Team, TeamJoinEvent, University, User

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'students')

    @admin.display(description="Number of students")
    def students(self, obj):
        return User.objects.filter(university=obj).count()

    search_fields = ('name', 'short_name')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'university', 'team')

    list_filter = ('university',)

    search_fields = (
        'codeforces_handle', 'email', 'first_name', 'github_handle',
        'kattis_handle', 'last_name', 'olinfo_handle', 'team__name',
        'university__name',
    )


@admin.register(Team)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'university', 'students')

    list_filter = ('university',)

    search_fields = ('user__first_name', 'user__last_name')

    @admin.display(description="Number of students")
    def students(self, obj):
        return User.objects.filter(team=obj).count()


admin.site.register(TeamJoinEvent)
