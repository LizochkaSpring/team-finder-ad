import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from projects.forms import ProjectForm
from projects.models import Project, Skill


def root_redirect(request):
    return redirect("projects:list")


def project_list(request):
    qs = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .order_by("-created_at")
    )
    active_skill = (request.GET.get("skill") or "").strip()
    if active_skill:
        qs = qs.filter(skills__name=active_skill).distinct()
    all_skills = Skill.objects.all().order_by("name")
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
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
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})


class OwnerOrStaffMixin(UserPassesTestMixin):
    def test_func(self):
        project = self.get_object()
        return self.request.user.is_staff or project.owner_id == self.request.user.id


class ProjectUpdateView(LoginRequiredMixin, OwnerOrStaffMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        return ctx

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"pk": self.object.pk})


@login_required
def complete_project(request, pk):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=405)
    project = get_object_or_404(Project, pk=pk)
    allowed = (
        request.user.is_staff or project.owner_id == request.user.id
    ) and project.status == Project.STATUS_OPEN
    if not allowed:
        return JsonResponse({"status": "error"}, status=403)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})


@login_required
def toggle_participate(request, pk):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=405)
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id == request.user.id:
        return JsonResponse({"status": "error"}, status=400)
    user = request.user
    if project.participants.filter(pk=user.pk).exists():
        project.participants.remove(user)
        participant = False
    else:
        project.participants.add(user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


def skills_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    qs = Skill.objects.all()
    if q:
        qs = qs.filter(name__istartswith=q)
    qs = qs.order_by("name")[:10]
    data = [{"id": s.pk, "name": s.name} for s in qs]
    return JsonResponse(data, safe=False)


@method_decorator(login_required, name="dispatch")
class ProjectSkillAddView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if not (request.user.is_staff or project.owner_id == request.user.id):
            return JsonResponse({"error": "forbidden"}, status=403)

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
                        status=400,
                    )
            elif name:
                skill = Skill.objects.filter(name__iexact=name).first()
                if skill is None:
                    skill = Skill.objects.create(name=name)
                    created = True
            else:
                return JsonResponse(
                    {"skill_id": None, "created": False, "added": False},
                    status=400,
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
            return JsonResponse({"error": "forbidden"}, status=403)
        skill = Skill.objects.filter(pk=skill_id).first()
        if skill is None:
            return JsonResponse({"status": "error"}, status=404)
        if not project.skills.filter(pk=skill.pk).exists():
            return JsonResponse({"status": "error"}, status=400)
        project.skills.remove(skill)
        return JsonResponse({"status": "ok"})
