from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from airport.models import Airport, Route, Flight, Ticket, Order, Airplane, AirplaneType

User = get_user_model()
URL = reverse("airport:order-list")

class OrderApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="testpass123"
        )
        self.client.force_authenticate(self.user)

        # создаём аэропорты
        self.airport1 = Airport.objects.create(
            name="Boryspil Airport", closest_big_city="Kyiv"
        )
        self.airport2 = Airport.objects.create(
            name="Berlin Tegel", closest_big_city="Berlin"
        )

        # создаём маршрут
        self.route = Route.objects.create(
            source=self.airport1,
            destination=self.airport2,
            distance=1200,
        )

        self.airplane_type = AirplaneType.objects.create(
            name="Boryspil Airplane",
        )

        self.airplane = Airplane.objects.create(
            name="Boeing 737",
            rows=20,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )
        # создаём рейс
        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time="2025-09-24T12:00:00Z",
            arrival_time="2025-09-24T14:00:00Z",
        )

    def test_create_order_with_ticket(self):
        payload = {
            "tickets": [
                {"row": 1, "seat": 2, "flight": self.flight.id},
                {"row": 1, "seat": 3, "flight": self.flight.id},
            ]
        }
        res = self.client.post(URL, payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.tickets.count(), 2)
        self.assertEqual(order.user, self.user)

    def test_order_list_only_user_orders(self):
        order = Order.objects.create(user=self.other_user)
        Ticket.objects.create(order=order, flight=self.flight, row=2, seat=4)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0)  # чужие заказы не видны

    def test_user_sees_their_orders(self):
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(order=order, flight=self.flight, row=5, seat=6)

        res = self.client.get(URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], order.id)