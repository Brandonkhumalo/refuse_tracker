from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Truck, Schedule, LocationUpdate
from .serializers import TruckSerializer, ScheduleSerializer, LocationUpdateSerializer

# -----------------------------
# Trucks
# -----------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def trucks_list_create(request):
    if request.method == 'GET':
        trucks = Truck.objects.all()
        serializer = TruckSerializer(trucks, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TruckSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def truck_detail(request, pk):
    try:
        truck = Truck.objects.get(pk=pk)
    except Truck.DoesNotExist:
        return Response({"error": "Truck not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TruckSerializer(truck)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = TruckSerializer(truck, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        truck.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# -----------------------------
# Schedules
# -----------------------------
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def schedules_list_create(request):
    if request.method == 'GET':
        schedules = Schedule.objects.all()
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def schedule_detail(request, pk):
    try:
        schedule = Schedule.objects.get(pk=pk)
    except Schedule.DoesNotExist:
        return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ScheduleSerializer(schedule, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# -----------------------------
# Location Updates
# -----------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def locations_list_create(request):
    if request.method == 'GET':
        locations = LocationUpdate.objects.all()
        serializer = LocationUpdateSerializer(locations, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = LocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def location_detail(request, pk):
    try:
        location = LocationUpdate.objects.get(pk=pk)
    except LocationUpdate.DoesNotExist:
        return Response({"error": "Location update not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = LocationUpdateSerializer(location)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = LocationUpdateSerializer(location, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        location.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resident_schedules(request):

    user = request.user

    if user.role != 'resident':
        return Response(
            {"error": "Only residents can access schedules"},
            status=status.HTTP_403_FORBIDDEN
        )

    if not user.suburb:
        return Response(
            {"error": "User does not have a suburb assigned"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Filter schedules by user's suburb (case-insensitive)
    user_suburb = user.suburb.strip().lower()
    schedules = Schedule.objects.filter(suburb__iexact=user_suburb)
    serializer = ScheduleSerializer(schedules, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resident_trucks(request):
    if request.user.role != 'resident':
        return Response({"error": "Only residents can access trucks"}, status=status.HTTP_403_FORBIDDEN)

    # Filter trucks assigned to user's route/suburb
    trucks = Truck.objects.filter(route_info__icontains=request.user.suburb)
    serializer = TruckSerializer(trucks, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resident_locations(request):
    if request.user.role != 'resident':
        return Response({"error": "Only residents can access location updates"}, status=status.HTTP_403_FORBIDDEN)

    # Filter location updates for trucks on the resident's route/suburb
    trucks = Truck.objects.filter(route_info__icontains=request.user.suburb)
    locations = LocationUpdate.objects.filter(truck__in=trucks).order_by('-timestamp')
    serializer = LocationUpdateSerializer(locations, many=True)
    return Response(serializer.data)
