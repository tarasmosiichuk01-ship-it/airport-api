from django.db import models


class Airport(models.Model):
    name = models.CharField(max_length=63, unique=True)
    closest_big_city = models.CharField(max_length=63, blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class AirplaneType(models.Model):
    name = models.CharField(max_length=63, unique=True)

    def __str__(self) -> str:
        return self.name