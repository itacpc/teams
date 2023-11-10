"""
URL configuration for itacpc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.http import HttpResponseNotFound
from django.views.defaults import page_not_found
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.urls import include, path

from allauth.account.views import EmailView

class NoChangePrimaryEmailView(EmailView):
    def post(self, request, *args, **kwargs):
        if "action_primary" in request.POST:
            raise PermissionDenied()

        return super().post(request, *args, **kwargs)

urlpatterns = [
    # Override allauth default signup
    path('signup/', page_not_found, {"exception": HttpResponseNotFound}),
    # Override allouth email management page (restricts changing primary email)
    path('email/', NoChangePrimaryEmailView.as_view()),

    path("", include("allauth.urls")),
    path("", include("teams.urls")),
    path("admin/", admin.site.urls),
]
