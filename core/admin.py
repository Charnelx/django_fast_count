from django.contrib import admin
from .models import TestProfileModel


class TestProfileAdmin(admin.ModelAdmin):

    list_display = ('first_name', 'last_name', 'id')


admin.site.register(TestProfileModel, TestProfileAdmin)
