from django.contrib import admin
from airport.models import (
    Airplane,
    Airport,
    Crew,
    Route,
    AirplaneType,
    Flight,
    Order,
    Ticket)

admin.site.register(Airplane)
admin.site.register(Airport)
admin.site.register(Crew)
admin.site.register(Route)
admin.site.register(AirplaneType)
admin.site.register(Flight)
admin.site.register(Order)
admin.site.register(Ticket)
