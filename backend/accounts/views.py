from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Open registration -- anyone can create an account, choosing their
    role at signup. In a production system, school_admin/ministry_admin
    roles would likely be provisioned by an existing administrator rather
    than self-selected; kept open here to keep the demo runnable without a
    seeded admin account for every role."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """Returns the authenticated user's own profile, including role -- the
    frontend uses this right after login to decide which portal to route
    into."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class EmailTokenObtainPairView(TokenObtainPairView):
    """Plain username/password JWT login (simplejwt's default). Kept as a
    thin subclass so the URL naming stays consistent with the rest of the
    API and it's easy to customise the token claims later if needed."""

    pass
