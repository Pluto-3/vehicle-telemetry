from django.urls import re_path
from realtime import consumers

websocket_urlpatterns = [
    re_path(r"^ws/vehicle/(?P<vehicle_id>[^/]+)/$", consumers.VehicleConsumer.as_asgi()),
    re_path(r"^ws/fleet/$", consumers.FleetConsumer.as_asgi()),
]
