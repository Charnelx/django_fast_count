from django.db import models

from .managers import TestProfileManager

class TestProfileModel(models.Model):

    first_name = models.CharField(max_length=128, default='Joe')
    last_name = models.CharField(max_length=128, default='Doe')

    objects = TestProfileManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name}'