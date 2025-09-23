import os
import uuid

from django.db import models
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from airport_api_service import settings


class Airport(models.Model):
    name = models.CharField(max_length=255)
    closest_big_city = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Route(models.Model):
    source = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="routes_as_source")
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="routes_as_destination")
    distance = models.IntegerField()

    def __str__(self):
        return f"Source: {self.source_id} -> Destination: {self.destination_id} ({self.distance} km)"

    class Meta:
        ordering = ("distance",)

class AirplaneType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

def airplane_image_file_path(instance, filename):
    _, ext = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}{uuid.uuid4()}{ext}"

    return os.path.join("uploads/airplanes/", filename)

class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.CASCADE, related_name="airplane_types")
    image = models.ImageField(null=True, blank=True, upload_to=airplane_image_file_path)

    def __str__(self):
        return self.name

    @property
    def capacity(self):
        return self.rows * self.seats_in_row

    def clean(self):
        if not (1 <= self.rows <= 50):
            raise ValidationError("Row count must be between 1 and 50")

        if not (1 <= self.seats_in_row <= 10):
            raise ValidationError("Seat count must be between 1 and 10")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Airplane, self).save(*args, **kwargs)


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="flights")
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crews = models.ManyToManyField(Crew, related_name="crews")

    def __str__(self):
        return f"{self.airplane.name}: {self.route.source.name} -> {self.route.destination.name}"

    class Meta:
        ordering = ("departure_time",)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.created_at

    class Meta:
        ordering = ['-created_at']

class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")

    def __str__(self):
        return f"{self.row}: {self.seat}"

    @staticmethod
    def validate_ticket(row, seat, errors_in_raise):
        if not (seat > 0 and row > 0):
            raise errors_in_raise(
                "Ticket seat must be greater than 0 and row must be greater than 0"
            )

    def clean(self):
        Ticket.validate_ticket(self.row, self.seat, ValidationError)

    def save(self, *args, **kwargs):
        self.full_clean()

        return super(Ticket, self).save(
            **args, **kwargs
        )


    class Meta:
        unique_together = ("row", "seat", "flight")
        ordering = ["row", "seat"]
