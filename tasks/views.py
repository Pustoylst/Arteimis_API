from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Project, Task, TaskComment
from .permissions import (
	IsProjectCreator,
	IsProjectParticipant,
	TaskCommentPermission,
	TaskObjectPermission,
)
from .serializers import (
	ProjectSerializer,
	TaskCommentSerializer,
	TaskSerializer,
	UserRegistrationSerializer,
)

User = get_user_model()


class TaskFilter(filters.FilterSet):
	"""Фильтры для удобноот фильтрации задач по дате.
	deadline_before и deadline_after утучняют query: deadline__lte и deadline__gte.
	"""
	deadline_before = filters.DateFilter(field_name="deadline", lookup_expr="lte")
	deadline_after = filters.DateFilter(field_name="deadline", lookup_expr="gte")

	class Meta:
		model = Task
		fields = [
			"project",
			"status",
			"priority",
			"assignee",
			"deadline_before",
			"deadline_after",
		]

class UserRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
	queryset = User.objects.all()
	serializer_class = UserRegistrationSerializer
	permission_classes = [AllowAny]

class ProjectViewSet(viewsets.ModelViewSet):
	serializer_class = ProjectSerializer
	queryset = Project.objects.select_related("creator").prefetch_related("participants")
	permission_classes = [IsAuthenticated]
	search_fields = ["name", "description"]
	ordering_fields = ["created_at", "name"]

	def get_queryset(self):
		"""UserProfile видим только те проекты, где он партнёр."""
		return self.queryset.filter(participants=self.request.user)

	def get_permissions(self):
		"""Настраиваем разные правила для разных действий (акшенов)."""
		if self.action in ["update", "partial_update", "destroy"]:
			# Менять или удалять редактируется может только владелец
			return [IsAuthenticated(), IsProjectCreator()]
		if self.action in ["retrieve"]:
			# Просматривать может только участник проекта
			return [IsAuthenticated(), IsProjectParticipant()]
		if self.action in ["add_participant", "remove_participant"]:
			# Управлять участниками может только владелец
			return [IsAuthenticated(), IsProjectCreator()]
		return [permission() for permission in self.permission_classes]

	def perform_create(self, serializer):
		"""При сохранении автоматически устанавливаем creator."""
		serializer.save(creator=self.request.user)

	@action(detail=True, methods=["post"])
	def add_participant(self, request, pk=None):
		"""
		Кастомное действие: add_participant. Генерирует endpoint /api/projects/{id}/add_participant/
		Владелец передает user_id и мы добавляем его в participants.
		"""
		project = self.get_object()
		user_id = request.data.get("user_id")
		if not user_id:
			return Response({"detail": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
		try:
			user = User.objects.get(id=user_id)
		except User.DoesNotExist:
			return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
		project.participants.add(user)
		return Response({"detail": "Participant added"}, status=status.HTTP_200_OK)

	@action(detail=True, methods=["post"])
	def remove_participant(self, request, pk=None):
		"""
		Кастомное действие: remove_participant. Генерирует endpoint /api/projects/{id}/remove_participant/
		Владелец передает user_id и мы удаляем его из participants (кроме самого владельца).
		"""
		project = self.get_object()
		user_id = request.data.get("user_id")
		if not user_id:
			return Response({"detail": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
		# Защита: нельзя удалить самого владельца
		if str(project.creator_id) == str(user_id):
			raise PermissionDenied("Project creator cannot be removed from participants.")
		project.participants.remove(user_id)
		return Response({"detail": "Participant removed"}, status=status.HTTP_200_OK)

class TaskViewSet(viewsets.ModelViewSet):
	serializer_class = TaskSerializer
	queryset = Task.objects.select_related("project", "author", "assignee")
	permission_classes = [IsAuthenticated, TaskObjectPermission]
	filterset_class = TaskFilter
	search_fields = ["title", "description"]
	ordering_fields = ["deadline", "created_at", "updated_at", "priority", "status"]

	def get_queryset(self):
		"""Отфильтровываем задачи, чтобы текущий пользователь видел только свои."""
		return self.queryset.filter(project__participants=self.request.user)

	def perform_create(self, serializer):
		"""При сохранении автоматически устанавливаем author (текущего пользователя)."""
		serializer.save(author=self.request.user)

class TaskCommentViewSet(viewsets.ModelViewSet):
	serializer_class = TaskCommentSerializer
	queryset = TaskComment.objects.select_related("task", "author", "task__project")
	permission_classes = [IsAuthenticated, TaskCommentPermission]
	ordering_fields = ["created_at"]

	def get_queryset(self):
		"""Отфильтровываем комментарии, чтобы текущий пользователь видел только комменты в своих проектах."""
		return self.queryset.filter(task__project__participants=self.request.user)

	def perform_create(self, serializer):
		serializer.save(author=self.request.user)
