from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (MessageViewset, 
                    ConversationViewset,
                    ConversationSettingsViewset,
                    ConversationUserViewSet,
                    FollowerViewset,
                    MessageForwardViewSet,
                    AttachmentViewSet,
                    MessageReactViewset,
                    CustomRequestViewSet,
                    RequestViewset,
                    HiddenRequestViewSet)

router = DefaultRouter()
router.register("message", MessageViewset, "message")
router.register("message-forward", MessageForwardViewSet, "message-forward")
router.register("conversation", ConversationViewset, "conversation")
router.register("conversation-settings", ConversationSettingsViewset, "conversation-settings")
router.register("follow", FollowerViewset, "follow")
router.register("request", RequestViewset, "request")
router.register(r'upload-attachment', AttachmentViewSet, basename='upload_attachment')
router.register('message-react', MessageReactViewset, basename='message-react')
router.register(r'hidden-request', HiddenRequestViewSet, basename='hidden-request')

urlpatterns = [
    path('', include(router.urls)),
    path("conversation-user/<int:user_id>/", ConversationUserViewSet.as_view(), name="conversation-users"),
    path("requests-to-user/", CustomRequestViewSet.as_view(), name="request-to-user"),
    # path("message-forward/", ConversationUserViewSet.as_view(), name="conversation-users")

]
