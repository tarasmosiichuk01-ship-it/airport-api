from django.contrib import admin

from airport.models import (
    Airport,
    AirplaneType,
    Crew,
    Route,
    Airplane,
    Flight,
    Order,
    Ticket,
)

class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 2


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInline, )

admin.site.register(Airport)
admin.site.register(AirplaneType)
admin.site.register(Crew)
admin.site.register(Route)
admin.site.register(Airplane)
admin.site.register(Flight)
admin.site.register(Ticket)
