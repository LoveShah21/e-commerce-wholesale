from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Address, Country, State, City, PostalCode

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phone', 'user_type', 'account_status', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'user_type')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('email', 'full_name', 'phone', 'password')
        
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'], # Username is email
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone'),
            password=validated_data['password'],
            user_type='customer'  # Default to customer role
        )
        return user

class AddressSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='postal_code.city.city_name', read_only=True)
    
    class Meta:
        model = Address
        fields = '__all__'
