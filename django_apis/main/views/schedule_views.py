from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models.models import MySchedule
from ..serializers.serializers import MyScheduleSerializer


# get all record, create a record
@api_view(['GET', 'POST'])
def schedule_list(request):
    if request.method == 'GET':
        schedules = MySchedule.objects.all()
        serializers = MyScheduleSerializer(schedules, many=True)
        return Response(serializers.data)

    elif request.method == 'POST':
        serializer = MyScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# handle a single record
@api_view(['GET', 'PUT', 'DELETE'])
def schedule_detail(request, pk):
    try:
        schedule = MySchedule.objects.get(pk=pk)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = MyScheduleSerializer(schedule)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = MyScheduleSerializer(schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

