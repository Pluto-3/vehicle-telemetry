from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from strawberry.django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from api.schema import schema

def authenticated_graphql_view(request):
    """Wrap GraphQL with API key check."""
    if not settings.DEBUG:  # Skip auth in debug mode for easier testing
        api_key = request.headers.get("X-API-Key", "")
        from ingestion.auth import validate_api_key
        if not validate_api_key(api_key):
            return JsonResponse({"error": "Invalid or missing API key"}, status=401)
    return csrf_exempt(GraphQLView.as_view(schema=schema))(request)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql/", authenticated_graphql_view),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
