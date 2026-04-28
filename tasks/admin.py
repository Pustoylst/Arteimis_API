from django.contrib import admin
from .models import Project, Task, TaskComment


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	"""Вывод основных полей проекта в таблице."""
	list_display = ("id", "name", "creator", "created_at")
	search_fields = ("name", "description", "creator__username")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	"""Отображаем задачи с выраженными полями и быстродействующими фильтрами."""
	list_display = ("id", "title", "project", "priority", "status", "assignee", "deadline")
	list_filter = ("priority", "status", "project")
	search_fields = ("title", "description", "author__username", "assignee__username")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
	"""Отображаем комментарии с автором, какое задаче принадлежит, и временем создания."""
	list_display = ("id", "task", "author", "created_at")
	search_fields = ("text", "author__username", "task__title")
