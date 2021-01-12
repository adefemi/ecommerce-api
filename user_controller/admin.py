from django.contrib import admin
from .models import User, ImageUpload


admin.site.register((User, ImageUpload,))
