from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("my-profile", views.my_profile, name="my-profile"),
    path("leave-team", views.leave_team, name="leave-team"),
    path("join/<secret>", views.join_team, name="join-team"),
    path("<university_short_name>", views.university, name="university"),
    path("<university_short_name>/new-student", views.create_student, name="create-student"),
    path("<university_short_name>/new-team", views.create_team, name="create-team"),
]
