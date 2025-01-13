from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (MessageViewset, 
                    ConversationViewset,
                    ConversationSettingsViewset,
                    FollowerViewset,
                    RequestViewset)

router = DefaultRouter()
router.register("message", MessageViewset, "message")
router.register("conversation", ConversationViewset, "conversation")
router.register("conversation-settings", ConversationSettingsViewset, "conversation-settings")
router.register("follow", FollowerViewset, "follow")
router.register("request", RequestViewset, "request")

urlpatterns = [
    path('', include(router.urls)),
]
