from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewset, ConversationViewset

router = DefaultRouter()
router.register("message", MessageViewset, "message")
router.register("conversation", ConversationViewset, "conversation")

urlpatterns = [
    path('', include(router.urls)),
]
