from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q, F
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils.crypto import get_random_string
from teams.models import TeamJoinEvent, User, Team, University
from allauth.account.views import SignupView
from allauth.account.forms import SignupForm
from allauth.account.adapter import get_adapter

def _ajax_response(request, response, form=None, data=None):
    adapter = get_adapter()
    if adapter.is_ajax(request):
        if isinstance(response, HttpResponseRedirect) or isinstance(
            response, HttpResponsePermanentRedirect
        ):
            redirect_to = response["Location"]
        else:
            redirect_to = None
        response = adapter.ajax_response(
            request, response, form=form, data=data, redirect_to=redirect_to
        )
    return response


def index(request):
    user_own_university = None
    if request.user.is_authenticated and hasattr(request.user, 'university'):
        user_own_university = request.user.university

    unis_with_count = University.objects.annotate(teams=Count('team', distinct=True), students=Count('user', distinct=True))
    other_university = unis_with_count.filter(short_name='other').get()

    # List all university except the "other" one
    unis = unis_with_count.exclude(short_name='other').order_by('-teams', '-students', 'short_name').all()

    # Put "other" university first if it exists
    if other_university:
        unis = [other_university] + list(unis)

    # If user has university, put that one first
    if user_own_university:
        unis = list(filter(lambda u: u == user_own_university, unis)) + \
            list(filter(lambda u: u != user_own_university, unis))

    team_count = Team.objects.count()
    students_count = User.objects.count()

    return render(request, "teams/index.html", {
        "unis": unis,
        "user_own_university": user_own_university,
        "team_count": team_count,
        "students_count": students_count,
    })

@login_required
def my_profile(request):
    class ProfileForm(forms.ModelForm):
        class Meta:
            model = User
            fields = ['first_name', 'last_name', 'kattis_handle', 'olinfo_handle', 'codeforces_handle', 'github_handle', 'subscribed', 'is_swerc_eligible']

    student = request.user
    university = student.university

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=student)
        if form.is_valid:
            form.save()
            messages.success(request, "Profile successfully updated!")
            return redirect('my-profile')
    else:
        form = ProfileForm(instance=student)

        return render(request, "teams/my_profile.html", {
            "student": student,
            "university": university,
            "form": form,
        })

def university(request, university_short_name):
    university = get_object_or_404(University, short_name=university_short_name)
    user_own_team = None
    if request.user.is_authenticated and request.user.team:
        # if hasattr(request.user, "team"):
            # team = request.user.team
            # if team:
        user_own_team = request.user.team

    teams = Team.objects.filter(university=university).all()
    grouped = []
    for t in teams:
        students = User.objects.filter(team=t).all()
        grouped.append((t, students))

    students_left = User.objects.filter(team=None, university=university).all()

    return render(request, "teams/university.html", {
        "students_left": students_left,
        "grouped": grouped,
        "university": university,
        "user_own_team": user_own_team,
    })

class StudentSignUpView(SignupView):
    class UserForm(SignupForm):
        first_name = forms.CharField()
        last_name = forms.CharField()
        is_swerc_eligible = forms.BooleanField(
            required=False,
            label="I am eligible for SWERC",
            help_text="""
                Not mandatory. See <a href="https://icpc.global/regionals/rules"
                target="_blank">eligibility criteria</a> and <a href="https://swerc.eu/"
                target="_blank">information about SWERC</a> and check this box if you
                would be interested in participating to SWERC.""")
        university = None

        field_order = ('first_name', 'last_name', 'email', 'password1', 'password2', 'is_swerc_eligible')

        def __init__(self, university_short_name, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.university = get_object_or_404(University, short_name=university_short_name)

        def clean_email(self):
            ok = super().clean_email()

            email = self.cleaned_data["email"]

            if self.university.domain == '*':
                return ok

            for dom in self.university.domain.split(","):
                if email.endswith('@' + dom) or email.endswith('.' + dom):
                    return ok

            raise forms.ValidationError('Use your institutional email address')
        
        def save(self, request):
            user = super().save(request)
            user.university = self.university
            user.save()
            return user


    template_name = "teams/university_create_student.html"
    form_class = UserForm
    redirect_field_name = 'next'
    view_name = "create_student"
    success_url = None

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            response = self.form_valid(form)
        else:
            response = self.form_invalid(form, **kwargs)
        return _ajax_response(
            self.request, response, form=form, data=self._get_ajax_data_if()
        )

    def get(self, request, university_short_name, **kwargs):
        kwargs['university_short_name'] = university_short_name
        return self.render_to_response(self.get_context_data(**kwargs))
    
    def form_invalid(self, form, **kwargs):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form, **kwargs))

    def get_context_data(self, **kwargs):
        ret = super().get_context_data(**kwargs)
        university = get_object_or_404(University, short_name=kwargs['university_short_name'])
        ret['university'] = university
        if university.domain != "*":
            ret['uni_domain'] = ret['university'].domain.split(',')
        return ret

    def get_form_kwargs(self):
        kwargs = super(StudentSignUpView, self).get_form_kwargs()
        # update the kwargs for the form init method with yours
        kwargs.update(self.kwargs)  # self.kwargs contains all url conf params
        return kwargs

create_student = StudentSignUpView.as_view()

@login_required
def create_team(request, university_short_name):
    class TeamForm(forms.ModelForm):
        class Meta:
            model = Team
            fields = ["name"]

    university = get_object_or_404(University, short_name=university_short_name)
    if university != request.user.university:
        messages.error(request, 'You can only create teams in your own university!')
        return redirect('create-team', university_short_name=request.user.university.short_name)

    if request.user.team:
        messages.error(request, 'You are already in a team, to create a new team you should first leave your current one.')
        return redirect('my-profile')

    if request.method == "POST":
        form = TeamForm(request.POST)

        if form.is_valid():
            team = form.save()
            team.university = university
            team.secret = get_random_string(length=16)
            team.save()

            request.user.team = team
            request.user.save()

            event = TeamJoinEvent(user=request.user, team=team, joining=True)
            event.save()

            return render(request, "teams/university_team_created.html", {
                "team": team,
                "university": university,
            })
    else:
        form = TeamForm()

        return render(request, "teams/university_create_team.html", {
            "university": university,
            "form": form,
        })

@login_required
def join_team(request, secret):
    MAX_MEMBERS = 3

    team = get_object_or_404(Team, secret=secret)

    if team.university != request.user.university:
        messages.error(request, 'You can only join teams from your university!')
        return redirect('my-profile')

    if request.user.team == team:
        messages.info(request, 'You already joined the team.')
        return redirect('my-profile')
    
    if request.user.team:
        messages.info(request, 'You can\'t join a new team, you should first leave your current team.')
        return redirect('my-profile')

    if request.method == "POST":
        # Run in a transaction to avoid race condition (e.g. someone joins the
        # same team right after we verified that the team is not already full)
        with transaction.atomic():
            num_members = User.objects.filter(team=team).count()
            if num_members >= MAX_MEMBERS:
                messages.error(request, 'This team has reached the maximum number of members')
                return redirect('my-profile')
            
            request.user.team = team
            request.user.save()

            event = TeamJoinEvent(user=request.user, team=team, joining=True)
            event.save()

            messages.error(request, 'You successfully joined the team!')
            return redirect('my-profile')

    return render(request, "teams/university_team_join.html", {
        "team": team,
    })

@login_required
def leave_team(request):
    if request.method == "POST":
        # Run in a transaction to prevent race conditions (e.g. someone else
        # joins the team right before we check if the team is empty)
        with transaction.atomic():
            old_team = request.user.team

            event = TeamJoinEvent(user=request.user, team=old_team, joining=False)
            event.save()

            request.user.team = None
            request.user.save()

            num_members_left = User.objects.filter(team=old_team).count()
            if num_members_left == 0:
                old_team.delete()
            else:
                # Update secret for extra security
                old_team.secret = get_random_string(length=16)
                old_team.save()

        return redirect('my-profile')

    return render(request, "teams/leave_team.html")
