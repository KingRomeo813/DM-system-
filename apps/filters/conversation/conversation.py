import logging
import django_filters
from django_filters import rest_framework as filters
from apps.models import Conversation, Request
from django.db.models import Q

log = logging.getLogger(__file__)
class ConversationFilter(django_filters.FilterSet):
    request_status = filters.CharFilter(method='filter_request_status')

    def filter_request_status(self, queryset, name, value):
        user = self.request.user
        statuses = value.split('|') if value else []

        requests = Request.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status__in=statuses
        )
        
        sender_profiles = requests.values_list('sender', flat=True)
        receiver_profiles = requests.values_list('receiver', flat=True)

        related_profiles = sender_profiles.union(receiver_profiles)
        conversations = queryset.filter(profiles__in=related_profiles)
        return conversations.distinct()

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'profiles', 'message_limit', 'created_at', 'room_type']