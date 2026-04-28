from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Project, Task, TaskComment

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        # Конвертируем очистенные данные в нового пользователя.
        # create_user автоматически хэширует пароль.
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Отображаем основную информацию о пользователе в других сериализаторах."""
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ProjectSerializer(serializers.ModelSerializer):
    """Сериализатор проекта.
    creator притворяють в read_only (автоматически поставляется текущий пользователь).
    """
    creator = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "creator",
            "participants",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор задачи.
    author наставляется автоматически.
    Он также выполняет глубокие проверки исполнителя на уровне бизнес-логики.
    """
    author = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "description",
            "priority",
            "status",
            "deadline",
            "author",
            "assignee",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        """Не стандартная валидация: проверяем бизнес-правила."""
        request = self.context["request"]
        instance = getattr(self, "instance", None)
        project = attrs.get("project") or (instance.project if instance else None)
        assignee = attrs.get("assignee") or (instance.assignee if instance else None)

        if project is None:
            raise serializers.ValidationError("Project is required.")
        if assignee is None:
            raise serializers.ValidationError("Assignee is required.")

        # Проверяем, что сотрудник — партнёр проекта
        if not project.participants.filter(id=request.user.id).exists():
            raise serializers.ValidationError(
                "Only project participants can create or update tasks."
            )

        # От задачи: определяем кто исполнитель — тот же проект
        if not project.participants.filter(id=assignee.id).exists():
            raise serializers.ValidationError(
                "Assignee must be a project participant."
            )

        return attrs


class TaskCommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментария.
    author наставляется автоматически из request.user.
    """
    author = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "task", "author", "text", "created_at"]
        read_only_fields = ["created_at"]

    def validate_task(self, task):
        """Проверяем, что комментатор — участник проекта."""
        request = self.context["request"]
        if not task.project.participants.filter(id=request.user.id).exists():
            raise serializers.ValidationError(
                "Only project participants can work with comments."
            )
        return task
