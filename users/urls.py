from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("list/", views.participants_list, name="participants"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="detail"),
    path("edit-profile/", views.EditProfileView.as_view(), name="edit_profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
]
