from allauth.account.adapter import DefaultAccountAdapter

class StudentAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form):
        user = super(StudentAccountAdapter, self).save_user(request, user, form, commit=False)
        user.university = form.university
        user.save()
