from django.conf import settings
from django.db import models


class Project(models.Model):
	"""Проект — это контейнер для задач и участников.
	
	Один проект = один набор участников + набор задач.
	Владелец (creator) создает проект и может управлять участниками.
	Участники (participants) могут видеть и работать с задачами в проекте.
	"""
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	creator = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="created_projects",
	)
	participants = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		related_name="projects",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def save(self, *args, **kwargs):
		"""При создании проекта автоматически добавляем его создателя в список участников."""
		is_new = self.pk is None
		super().save(*args, **kwargs)
		if is_new:
			self.participants.add(self.creator)

	def __str__(self):
		return self.name



class Task(models.Model):
	"""Задача — это единица работы внутри проекта. Важные роли: author (создатель), assignee (исполнитель), project."""
	
	class Priority(models.TextChoices):
		LOW = "LOW", "Low"
		MEDIUM = "MEDIUM", "Medium"
		HIGH = "HIGH", "High"
		CRITICAL = "CRITICAL", "Critical"

	class Status(models.TextChoices):
		TODO = "TODO", "To Do"
		IN_PROGRESS = "IN_PROGRESS", "In Progress"
		REVIEW = "REVIEW", "Review"
		DONE = "DONE", "Done"
		BLOCKED = "BLOCKED", "Blocked"

	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	priority = models.CharField(
		max_length=16,
		choices=Priority.choices,
		default=Priority.MEDIUM,
	)
	status = models.CharField(
		max_length=16,
		choices=Status.choices,
		default=Status.TODO,
	)
	deadline = models.DateField(null=True, blank=True)
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="authored_tasks",
	)
	assignee = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="assigned_tasks",
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return self.title


class TaskComment(models.Model):
	"""Комментарий к задаче для обсуждения. Видны только участникам проекта."""
	
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="task_comments",
	)
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at"]

	def __str__(self):
		return f"Comment #{self.pk}"
