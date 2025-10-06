from rest_framework import serializers
from .models import User, Truck, Schedule, LocationUpdate

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id','email','password','phone','role','lat','lng','suburb',]

    def create(self, validated_data):
        # Use create_user to ensure password hashing
        print(validated_data)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data['phone'],
            role=validated_data['role'],
            lat=validated_data.get('lat'),
            lng=validated_data.get('lng'),
            suburb=validated_data.get('suburb'),
        )
        return user

class LoginSerializer(serializers.Serializer):  
    email = serializers.EmailField() 
    password = serializers.CharField(max_length=100, write_only=True)

    def validate(self, attrs):

        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required")

        user = User.objects.filter(email=email).first()

        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'role', 'lat', 'lng', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            phone=validated_data.get('phone'),
            role=validated_data.get('role', 'resident'),
            lat=validated_data.get('lat'),
            lng=validated_data.get('lng')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = ['id', 'name', 'gps_device_id', 'route_info']

class ScheduleSerializer(serializers.ModelSerializer):
    truck_name = serializers.CharField(source="truck.name", read_only=True)  # ✅ add truck name

    class Meta:
        model = Schedule
        fields = ['id', 'truck', 'truck_name', 'suburb', 'route', 'collection_date']

class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationUpdate
        fields = '__all__'
