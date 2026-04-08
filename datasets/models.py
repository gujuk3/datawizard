from django.db import models
from django.conf import settings


class Dataset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/')
    file_size = models.BigIntegerField(default=0)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='uploaded')

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class DataColumn(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=50)
    missing_count = models.IntegerField(default=0)
    unique_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.dataset.name} - {self.name}"