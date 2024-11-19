from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Test, UserAccount, UserRole
from .serializers import TestSerializer, UserAccountSerializer, UserRoleSerializer

class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer

class UserAccountViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer

class TestPDFView(APIView):
    def get(self, request, id, format=None):
        try:
            test = Test.objects.get(id=id)
        except Test.DoesNotExist:
            return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="test_{test.id}.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        p.drawString(100, 750, f"ID: {test.id}")
        p.drawString(100, 730, f"Name: {test.name}")
        p.drawString(100, 710, f"Age: {test.age}")

        p.showPage()
        p.save()

        return response