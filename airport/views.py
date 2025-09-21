from rest_framework import viewsets

from airport.models import Airport, Route, Airplane, Flight, Order, Ticket, AirplaneType
from airport.serializers import AirportSerializer, RouteSerializer, AirplaneSerializer, FlightSerializer, \
    OrderSerializer, AirplaneTypeSerializer, RouteListSerializer, AirplaneListSerializer, FlightListSerializer


class AirportViewSet(viewsets.ModelViewSet):  #Dont need list
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        return AirplaneSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):  #Dont need list
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        return FlightSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
