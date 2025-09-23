from datetime import datetime

from django.db.models import F, Value, Count
from django.db.models.functions import Concat
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from airport.models import Airport, Route, Airplane, Flight, Order, AirplaneType
from airport.serializers import AirportSerializer, RouteSerializer, AirplaneSerializer, FlightSerializer, \
    OrderSerializer, AirplaneTypeSerializer, AirplaneListSerializer, FlightListSerializer, \
    RouteDetailSerializer, AirplaneDetailSerializer, FlightDetailSerializer, OrderListSerializer, RouteListSerializer, \
    AirplaneImageSerializer


class AirportViewSet(viewsets.ModelViewSet):  #Dont need list
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_queryset(self):
        name = self.request.query_params.get("name")
        city = self.request.query_params.get("city")
        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)

        if city:
            queryset = queryset.filter(closest_big_city__icontains=city)

        return queryset.distinct()


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related('source', 'destination')
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteDetailSerializer



    def get_queryset(self):
        queryset = self.queryset
        if self.action == "retrieve":
            queryset = queryset.annotate(
                airport_computed=Concat(
                    F('source__name'),
                    Value(' -> '),
                    F('destination__name'),
                ),
                trips_computed=Concat(
                    F('source__closest_big_city'),
                    Value(' -> '),
                    F('destination__closest_big_city'),
                )
            )
        return queryset.distinct()


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all().select_related("airplane_type")
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action == "upload-image":
            return AirplaneImageSerializer
        return AirplaneSerializer


    def get_queryset(self):
        name = self.request.query_params.get("name")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[IsAdminUser],
        url_path='upload-image'
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class AirplaneTypeViewSet(viewsets.ModelViewSet):  #Dont need list
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer

class FlightPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size'


class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight.objects.all()
        .select_related('airplane', 'airplane__airplane_type', 'route', 'route__source', 'route__destination')
        .prefetch_related('crews')
        .annotate(
            tickets_available=(
                    F('airplane__rows') * F('airplane__seats_in_row')
                    - Count("tickets")
            ),
        )
        )
    pagination_class = FlightPagination
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        return FlightDetailSerializer

    @staticmethod
    def _params_to_ints(queryset):
        return [int(str_id) for str_id in queryset.split(',')]

    def get_queryset(self):
        crews = self.request.query_params.get('crews')
        date = self.request.query_params.get('date')

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, '%Y-%m-%d').date()
            queryset = queryset.filter(departure_time__date=date)

        if crews:
            crews_ids = self._params_to_ints(crews)
            queryset = queryset.filter(crews__id__in=crews_ids)

        return queryset.distinct()

class OrderViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
):
    queryset = Order.objects.all().select_related("tickets__flight__travel")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

