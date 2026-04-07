from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProjectCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.creator_id == request.user.id


class IsProjectParticipant(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.participants.filter(id=request.user.id).exists()


class TaskObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return obj.project.participants.filter(id=user.id).exists()

        if obj.project.creator_id == user.id:
            return True

        if request.method == "DELETE":
            return obj.author_id == user.id

        if request.method in ("PUT", "PATCH"):
            fields = set(request.data.keys())
            if obj.assignee_id == user.id:
                return fields.issubset({"status", "priority"})
            if obj.author_id == user.id:
                return fields.issubset({"description"})
            return False

        return False


class TaskCommentPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.task.project.participants.filter(id=request.user.id).exists()
        return obj.author_id == request.user.id or obj.task.project.creator_id == request.user.id
