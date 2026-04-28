from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProjectCreator(BasePermission):
    """Только владелец проекта может менять/удалять его параметры."""
    def has_object_permission(self, request, view, obj):
        return obj.creator_id == request.user.id


class IsProjectParticipant(BasePermission):
    """Только участники проекта могут его просматривать."""
    def has_object_permission(self, request, view, obj):
        return obj.participants.filter(id=request.user.id).exists()


class TaskObjectPermission(BasePermission):
    """
    Сложные правила для редактирования задач.
    
    Логика:
    - На чтение (GET): только участники проекта
    - На изменение (PUT/PATCH/DELETE):
      * Владелец проекта может менять ВСЮ задачу
      * Исполнитель может менять только свою задачу: status и priority
      * Автор может менять только описание (description) своей задачи
      * На удаление (DELETE): только автор или владелец проекта
    """
    def has_object_permission(self, request, view, obj):
        user = request.user

        # Прочитать задачу может только участник проекта
        if request.method in SAFE_METHODS:
            return obj.project.participants.filter(id=user.id).exists()

        # Владелец проекта может всё
        if obj.project.creator_id == user.id:
            return True

        # Удалить может только автор задачи или владелец проекта
        if request.method == "DELETE":
            return obj.author_id == user.id

        # На изменение (PUT/PATCH): проверяем, какие поля меняются
        if request.method in ("PUT", "PATCH"):
            fields = set(request.data.keys())
            # Исполнитель может менять только status и priority
            if obj.assignee_id == user.id:
                return fields.issubset({"status", "priority"})
            # Автор может менять только description
            if obj.author_id == user.id:
                return fields.issubset({"description"})
            return False

        return False


class TaskCommentPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.task.project.participants.filter(id=request.user.id).exists()
        return obj.author_id == request.user.id or obj.task.project.creator_id == request.user.id
