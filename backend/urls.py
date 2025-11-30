from django.contrib import admin
from django.urls import path
from tasks.views import TaskAnalysisView, TaskSuggestionView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/tasks/analyze/', TaskAnalysisView.as_view()),
    path('api/tasks/suggest/', TaskSuggestionView.as_view()),
]
