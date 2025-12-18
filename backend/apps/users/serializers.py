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
    """Serializer for reading addresses with full location details"""
    city = serializers.CharField(source='postal_code.city.city_name', read_only=True)
    state = serializers.CharField(source='postal_code.city.state.state_name', read_only=True)
    country = serializers.CharField(source='postal_code.city.state.country.country_name', read_only=True)
    postal_code_value = serializers.CharField(source='postal_code.postal_code', read_only=True)
    
    class Meta:
        model = Address
        fields = (
            'id', 'address_line1', 'address_line2', 'address_type', 'is_default',
            'city', 'state', 'country', 'postal_code_value', 'created_at'
        )

class AddressCreateSerializer(serializers.Serializer):
    """Serializer for creating addresses from checkout form"""
    address_line_1 = serializers.CharField(max_length=255)
    address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=50)
    state = serializers.CharField(max_length=50)
    postal_code = serializers.CharField(max_length=10)
    country = serializers.CharField(max_length=50, default='India')
    address_type = serializers.ChoiceField(
        choices=Address.ADDRESS_TYPE_CHOICES, 
        default='other'
    )
    is_default = serializers.BooleanField(default=False)
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Get or create country
        country_name = validated_data['country']
        country, _ = Country.objects.get_or_create(
            country_name=country_name,
            defaults={'country_code': 'IN' if country_name == 'India' else 'XX'}
        )
        
        # Get or create state
        state_name = validated_data['state']
        state, _ = State.objects.get_or_create(
            country=country,
            state_name=state_name
        )
        
        # Get or create city
        city_name = validated_data['city']
        city, _ = City.objects.get_or_create(
            state=state,
            city_name=city_name
        )
        
        # Get or create postal code
        postal_code_value = validated_data['postal_code']
        postal_code, _ = PostalCode.objects.get_or_create(
            city=city,
            postal_code=postal_code_value
        )
        
        # Create address
        address = Address.objects.create(
            user=user,
            address_line1=validated_data['address_line_1'],
            address_line2=validated_data.get('address_line_2', ''),
            postal_code=postal_code,
            address_type=validated_data.get('address_type', 'other'),
            is_default=validated_data.get('is_default', False)
        )
        
        # If this is set as default, unset other default addresses
        if address.is_default:
            Address.objects.filter(
                user=user, 
                is_default=True
            ).exclude(id=address.id).update(is_default=False)
        
        return address
