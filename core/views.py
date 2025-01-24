from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import User, OTP
from .utils import send_otp_email
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework_simplejwt.tokens import RefreshToken
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import LostItem
from django.utils.dateparse import parse_date

# @csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            name = data.get('name')
            mobile_number = data.get('mobile_number')

            # Validate required fields
            if not all([email, password, name, mobile_number]):
                return JsonResponse({'error': 'All fields are required.'}, status=400)

            # Create the user
            user = User.objects.create_user(
                email=email,
                password=password,
                name=name,
                mobile_number=mobile_number
            )
            user.save()
            return JsonResponse({'message': 'User created successfully!', 'error': None}, status=201)


            # return JsonResponse({'message': 'User created successfully.'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

# @csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return JsonResponse({'error': 'Email and password are required.'}, status=400)

            user = authenticate(request, username=email, password=password)

            if user is not None:
                # Create JWT token for the user
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return JsonResponse({
                    'message': 'Login successful.',
                    'access_token': access_token,
                    'user': {
                        'name': user.name,
                          'email': user.email,
                          'mobile_number': user.mobile_number}
                }, status=200)
            else:
                return JsonResponse({'error': 'Invalid email or password.'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)


def verify_otp(request):
    if request.method == 'POST':
        email = request.POST['email']
        otp_code = request.POST['otp_code']

        try:
            user = User.objects.get(email=email)
            if user.otp.otp_code == otp_code:
                user.is_active = True
                user.save()
                return JsonResponse({'message': 'OTP verified. Account activated.'})
            else:
                return JsonResponse({'error': 'Invalid OTP'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        

@csrf_exempt
def get_user_details(request):
    if request.method == 'GET':
        # Get email from query params or headers
        email = request.GET.get('email')  # Example: /api/get-user-details?email=user@example.com
        if not email:
            return JsonResponse({'error': 'Email parameter is missing.'}, status=400)

        try:
            # Fetch user by email
            user = User.objects.get(email=email)  # Adjust if using a custom user model

            # Return user details
            return JsonResponse({
                'name': user.name,  # Adjust to your user model fields
                'email': user.email,
                'mobile_number': getattr(user, 'mobile_number', None),  # Add custom field check
                'profile_picture': user.profile_picture.url if hasattr(user, 'profile_picture') and user.profile_picture else None,
            })

        except User.DoesNotExist:
            return JsonResponse({'error': 'User with this email does not exist.'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
    
@csrf_exempt
def update_profile(request):
    if request.method == 'PATCH':
        email = request.GET.get('email')  # Get email from query params
        if not email:
            return JsonResponse({'error': 'Email parameter is missing.'}, status=400)

        try:
            user = User.objects.get(email=email)
            # Handle the form data
            if request.FILES:
                user.profile_image = request.FILES.get('profile_picture')

            if 'name' in request.POST:
                user.name = request.POST['name']

            if 'mobile_number' in request.POST:
                user.mobile_number = request.POST['mobile_number']

            if 'password' in request.POST:
                user.password = make_password(request.POST['password'])

            user.save()

            return JsonResponse({
                'message': 'Profile updated successfully.',
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'mobile_number': user.mobile_number,
                    'profile_picture': user.profile_image.url if user.profile_image else None,
                }
            }, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
    

@csrf_exempt
def submit_lost_item(request):
    if request.method == 'POST':
        # Get data from request body (assuming JSON)
        data = json.loads(request.body)

        # Fetch details from the request (name and mobile should be fetched from localStorage)
        name = data.get('name')  # Name from localStorage
        mobile_number = data.get('mobile_number')  # Mobile number from localStorage
        location = data.get('location')
        lost_item_name = data.get('lost_item_name')
        description = data.get('description')
        date_lost = data.get('date_lost')  # Date when the item was lost (should be in 'dd/mm/yyyy' format)
        image = data.get('image')  # Image file (if any)

        if not (name and mobile_number and location and lost_item_name and description and date_lost):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        try:
            # Convert date format from dd/mm/yyyy to yyyy-mm-dd
            date_lost = parse_date(date_lost)

            # Create a new LostItem object
            lost_item = LostItem(
                name=name,
                mobile_number=mobile_number,
                location=location,
                lost_item_name=lost_item_name,
                description=description,
                date_lost=date_lost
            )

            if image:
                lost_item.image = image  # Assign the image if provided

            lost_item.save()  # Save the object to the database

            return JsonResponse({'message': 'Lost item submitted successfully!'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)