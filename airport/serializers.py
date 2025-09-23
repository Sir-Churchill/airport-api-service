from django.db import transaction
from rest_framework import serializers

from airport.models import Airport, Route, Airplane, AirplaneType, Flight, Order, Ticket, Crew


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = AirportSerializer(read_only=True, many=False)
    destination = AirportSerializer(read_only=True, many=False)


class RouteDetailSerializer(serializers.ModelSerializer):
    airports = serializers.CharField(source="airport_computed", read_only=True)
    trips = serializers.CharField(source="trips_computed", read_only=True)
    class Meta:
        model = Route
        fields = ("id", "airports", "trips", "distance")


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type")


class AirplaneListSerializer(serializers.ModelSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True, many=False)
    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type", "image")


class AirplaneDetailSerializer(serializers.ModelSerializer):
    airplane_type = serializers.CharField(read_only=True, source="airplane_type.name")
    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "capacity", "airplane_type", "image")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class CrewListSerializer(CrewSerializer):
    class Meta:
        model = Crew
        fields = ("first_name", "last_name", "full_name")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "departure_time", "arrival_time", "crews")


class FlightListSerializer(FlightSerializer):
    route = RouteListSerializer(read_only=True, many=False)
    airplane = AirplaneListSerializer(read_only=True, many=False)
    crews = CrewSerializer(read_only=True, many=True)
    tickets = serializers.IntegerField(source="tickets_available", read_only=True)

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "departure_time", "arrival_time", "tickets","crews")


class FlightDetailSerializer(FlightSerializer):
    final_place = serializers.CharField(read_only=True, source="route.destination.closest_big_city")
    airplane = serializers.CharField(read_only=True, source="airplane.name")
    crews = CrewListSerializer(read_only=True, many=True)
    class Meta:
        model = Flight
        fields = ("id", "final_place", "airplane", "departure_time", "arrival_time", "crews")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            serializers.ValidationError,
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = FlightDetailSerializer(read_only=True, many=False)
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(read_only=False, many=True, allow_empty=False)
    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket in tickets:
                Ticket.objects.create(order=order, **ticket)

            return order

class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(read_only=True, many=True)
