from django.db import models
from django.conf import settings


class SafetyPlace(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    comment = models.CharField(max_length=255)

    def __str__(self):
        return self.comment
