import uuid
from django.db import models
from django.core.exceptions import ValidationError
from . import BaseModel



class Attachments(BaseModel):
    message = models.ForeignKey("apps.Message", on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to='uploads/')  # Default upload directory

    def upload_to_dynamic(self, field_name, filename):
        """Generate a dynamic upload path using the specified field name."""
        unique_filename = f"{uuid.uuid4()}_{filename}" 
        return f"{field_name}/{unique_filename}"

    def save(self, *args, **kwargs):
        if self.file:
            field_name = kwargs.pop('field_name', 'attachments')  # Default to 'attachments'
            self.file.name = self.upload_to_dynamic(field_name, self.file.name)  # Set the file name dynamically
        super().save(*args, **kwargs)
