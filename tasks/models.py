from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    importance = models.IntegerField(default=5)  # 1-10
    estimated_hours = models.FloatField(default=1.0)
    dependencies = models.JSONField(default=list, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
