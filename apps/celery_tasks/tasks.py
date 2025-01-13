import time
import logging
# from apps.models import Profile
# from apps.repositories import ProfileRepo, ConversationRepo
from services import UserService
from celery import shared_task

log = logging.getLogger(__file__)

@shared_task
def sync_all_profiles(data):
    repo = ProfileRepo()
    repo.update_or_create(data)
