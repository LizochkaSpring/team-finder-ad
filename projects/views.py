import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from projects.constants import SKILL_AUTOCOMPLETE_LIMIT, PROJECTS_PER_PAGE
from projects.forms import ProjectForm
from projects.mixins import OwnerOrStaffMixin
from projects.models import Project, Skill
from users.services import paginate_queryset


def root_redirect(request):
    return redirect("projects:list")


def project_list(request):
    queryset = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .order_by("-created_at")
    )
    active_skill = (request.GET.get("skill") or "").strip()
    if active_skill:
        queryset = queryset.filter(skills__name=active_skill).distinct()
    all_skills = Skill.objects.all().order_by("name")
    page_obj = paginate_queryset(request, queryset, PROJECTS_PER_PAGE)
    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj,
            "all_skills": all_skills,
            "active_skill": active_skill,
        },
    )


class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/project-details.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.select_related("owner").prefetch_related(
            "participants", "skills"
        )


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        return ctx

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        self.object.participants.add(self.request.user)
        return response

    def get_success_url(self):
        return reverse("projects:detail", kwargs={"pk": self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, OwnerOrStaffMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        return ctx

    def get_success_url(self):
        return reverse("projects:detail", kwargs={"pk": self.object.pk})


@login_required
def complete_project(request, pk):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=HTTPStatus.METHOD_NOT_ALLOWED)
    project = get_object_or_404(Project, pk=pk)
    allowed = (
        request.user.is_staff or project.owner_id == request.user.id
    ) and project.status == Project.STATUS_OPEN
    if not allowed:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})


@login_required
def toggle_participate(request, pk):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=HTTPStatus.METHOD_NOT_ALLOWED)
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id == request.user.id:
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
    user = request.user
    if project.participants.filter(pk=user.pk).exists():
        project.participants.remove(user)
        participant = False
    else:
        project.participants.add(user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


def skills_autocomplete(request):
    query = (request.GET.get("q") or "").strip()
    queryset = Skill.objects.all()
    if query:
        queryset = queryset.filter(name__istartswith=query)
    queryset = queryset.order_by("name")[:SKILL_AUTOCOMPLETE_LIMIT]
    data = [{"id": skill.pk, "name": skill.name} for skill in queryset]
    return JsonResponse(data, safe=False)


@method_decorator(login_required, name="dispatch")
class ProjectSkillAddView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if not (request.user.is_staff or project.owner_id == request.user.id):
            return JsonResponse({"error": "forbidden"}, status=HTTPStatus.FORBIDDEN)

        payload = {}
        if request.body:
            try:
                payload = json.loads(request.body.decode())
            except json.JSONDecodeError:
                payload = {}
        skill_id = payload.get("skill_id") or request.POST.get("skill_id")
        if skill_id is not None:
            skill_id = str(skill_id).strip()
            try:
                skill_id = int(skill_id)
            except (TypeError, ValueError):
                skill_id = None
        name = (payload.get("name") or request.POST.get("name") or "").strip()

        created = False
        added = False
        skill = None

        with transaction.atomic():
            if skill_id:
                skill = Skill.objects.filter(pk=skill_id).first()
                if skill is None:
                    return JsonResponse(
                        {"skill_id": None, "created": False, "added": False},
                        status=HTTPStatus.BAD_REQUEST,
                    )
            elif name:
                skill = Skill.objects.filter(name__iexact=name).first()
                if skill is None:
                    skill = Skill.objects.create(name=name)
                    created = True
            else:
                return JsonResponse(
                    {"skill_id": None, "created": False, "added": False},
                    status=HTTPStatus.BAD_REQUEST,
                )

            if skill and project.skills.filter(pk=skill.pk).exists():
                return JsonResponse(
                    {
                        "skill_id": skill.pk,
                        "name": skill.name,
                        "created": created,
                        "added": False,
                    }
                )

            if skill:
                project.skills.add(skill)
                added = True

        return JsonResponse(
            {
                "skill_id": skill.pk,
                "name": skill.name,
                "created": created,
                "added": added,
            }
        )


@method_decorator(login_required, name="dispatch")
class ProjectSkillRemoveView(View):
    def post(self, request, pk, skill_id):
        project = get_object_or_404(Project, pk=pk)
        if not (request.user.is_staff or project.owner_id == request.user.id):
            return JsonResponse({"error": "forbidden"}, status=HTTPStatus.FORBIDDEN)
        skill = Skill.objects.filter(pk=skill_id).first()
        if skill is None:
            return JsonResponse({"status": "error"}, status=HTTPStatus.NOT_FOUND)
        if not project.skills.filter(pk=skill.pk).exists():
            return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
        project.skills.remove(skill)
        return JsonResponse({"status": "ok"})
