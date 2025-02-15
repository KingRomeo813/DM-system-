from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (MessageViewset, 
                    ConversationViewset,
                    ConversationSettingsViewset,
                    ConversationUserViewSet,
                    FollowerViewset,
                    MessageForwardViewSet,
                    RequestViewset)

router = DefaultRouter()
router.register("message", MessageViewset, "message")
router.register("message-forward", MessageForwardViewSet, "message-forward")
router.register("conversation", ConversationViewset, "conversation")
router.register("conversation-settings", ConversationSettingsViewset, "conversation-settings")
router.register("follow", FollowerViewset, "follow")
router.register("request", RequestViewset, "request")

urlpatterns = [
    path('', include(router.urls)),
    path("conversation-user/<int:user_id>/", ConversationUserViewSet.as_view(), name="conversation-users")
    # path("message-forward/", ConversationUserViewSet.as_view(), name="conversation-users")

]
