from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import DetailView, UpdateView
from django.views.generic.edit import FormView

from projects.models import Project
from users.constants import USERS_PER_PAGE
from users.forms import (
    LoginForm,
    ProfileEditForm,
    RegisterForm,
    UserPasswordChangeForm,
)
from users.models import User
from users.services import paginate_queryset


def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("users:login")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("projects:list")
        form.add_error(None, "Неверный имейл или пароль")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


class UserDetailView(DetailView):
    model = User
    template_name = "users/user-details.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = ctx["profile"]
        ctx["profile_projects"] = (
            Project.objects.filter(Q(owner=profile) | Q(participants=profile))
            .distinct()
            .select_related("owner")
            .order_by("-created_at")
        )
        return ctx


def participants_list(request):
    queryset = User.objects.order_by("-date_joined", "-id")
    page_obj = paginate_queryset(request, queryset, USERS_PER_PAGE)
    return render(
        request,
        "users/participants.html",
        {"participants": page_obj},
    )


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileEditForm
    template_name = "users/edit_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


class ChangePasswordView(LoginRequiredMixin, FormView):
    form_class = UserPasswordChangeForm
    template_name = "users/change_password.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        return redirect("users:detail", pk=self.request.user.pk)
