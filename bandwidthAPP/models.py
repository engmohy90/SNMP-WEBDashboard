from __future__ import unicode_literals

from django.db import models

# Create your models here.
class RouterData(models.Model):
    ip =  models.CharField(max_length=200)
    interface = models.CharField(max_length=200,null=True)
    input = models.IntegerField(null=True)
    output = models.IntegerField(null=True)