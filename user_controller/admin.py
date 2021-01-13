from django.contrib import admin
from .models import User, ImageUpload, UserProfile, UserAddress


admin.site.register((User, ImageUpload, UserProfile, UserAddress, ))
