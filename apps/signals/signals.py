import logging
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from apps.models import Message

logs = logging.getLogger(__file__)
@receiver(pre_save, sender=Message)
def message_send(sender, **kwargs):
    from apps.celery_tasks import send_messages

    try:
        instance: Message = kwargs.get('instance', None)
        if instance and not instance._state.adding:
            old_instance = Message.objects.get(pk=instance.pk)
            old_receiver = set(old_instance.forward_receiver())
            new_receiver = set(instance.forward_receiver())
            unique_receiver = new_receiver - old_receiver

            if unique_receiver:
                for profile in unique_receiver:
                    send_messages.apply_async(args=[instance.id, profile.id])
        else: 
            forward = set(instance.forward_receiver())
            forward.add(instance.receiver())
            for profile in forward:
                send_messages.apply_async(args=[instance.id, profile.id])
    except Exception as e:
            logs.error(str(e))