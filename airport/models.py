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


class Crew(models.Model):
    first_name = models.CharField(max_length=63)
    last_name = models.CharField(max_length=63)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name
