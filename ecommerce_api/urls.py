
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from graphene_file_upload.django import FileUploadGraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphview/', csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True)))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
