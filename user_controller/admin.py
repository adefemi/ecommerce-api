from django.contrib import admin
from .models import User, ImageUpload, UserProfile, AddressList


admin.site.register((User, ImageUpload, UserProfile, AddressList,))
