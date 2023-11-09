from typing import Any
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.shortcuts import resolve_url
from django.templatetags.static import static
from allauth.account.signals import email_confirmed
from django.dispatch import receiver


@receiver(email_confirmed)
def verify_user_when_email_confirmed(request, email_address, **kwargs):
    user = email_address.user
    user.is_verified = True
    user.save()


class University(models.Model):
    short_name = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=200)
    kattis_subdivision = models.CharField(max_length=200, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name}"

    @property
    def flag_300(self):
        return static(f"flags/300/{self.short_name}.png")


class Team(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=200, unique=True)
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True)
    secret = models.CharField(max_length=200)
    creation_date = models.DateTimeField(auto_now_add=True)
    credentials = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    @property
    def invitation_link(self):
        url = resolve_url('join-team', secret=self.secret)
        return f"https://teams.itacpc.it{url}"

    @property
    def students(self):
        return User.objects.filter(team=self).all()



class UserManager(BaseUserManager):
    def create_superuser(self, email, password, **kwargs):
        user = self.model(email=email, is_staff=True, is_superuser=True, **kwargs)
        user.set_password(password)
        user.save()
        return user


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    username = None
    email = models.EmailField(unique=True, null=False, blank=False)
    is_swerc_eligible = models.BooleanField(null=False, default=False, blank=True, verbose_name="I am eligible for SWERC", help_text="""
        Not mandatory. See <a href="https://icpc.global/regionals/rules"
        target="_blank">eligibility criteria</a> and <a href="https://swerc.eu/"
        target="_blank">information about SWERC</a> and check this box if you
        would be interested in participating to SWERC.""")
    is_verified = models.BooleanField(null=False, default=False)
    university = models.ForeignKey(University, on_delete=models.CASCADE, null=False, blank=False)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    subscribed = models.BooleanField(default=True, verbose_name="Subscribe to email updates", help_text="Needed to receive contest access credentials.")
    codeforces_handle = models.CharField(max_length=200, null=True, blank=True)
    kattis_handle = models.CharField(max_length=200, null=True, blank=True)
    olinfo_handle = models.CharField(max_length=200, null=True, blank=True)
    github_handle = models.CharField(max_length=200, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'university_id']  # for manage.py createsuperuser

    objects = UserManager()

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class TeamJoinEvent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    joining = models.BooleanField()

    def __str__(self) -> str:
        return f"{self.user} {'joined' if self.joining else 'left'} team {self.team} on {self.created_at}"
