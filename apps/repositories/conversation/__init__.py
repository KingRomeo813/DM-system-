import uuid
import logging
import datetime
from typing import Dict, List, Optional, Any, Set
from apps.models import Conversation, Profile

log = logging.getLogger(__name__)

class ConversationRepo():
    def __init__(self):
        pass

    def get(self, id):
        return Conversation.objects.get(id=id)