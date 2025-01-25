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
from .models import FoundItem
from django.utils.dateparse import parse_date
from datetime import datetime


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
        try:
            # Handle form-data separately
            if request.content_type.startswith('multipart/form-data'):
                # Parse form-data
                name = request.POST.get('name')
                mobile_number = request.POST.get('mobile_number')
                location = request.POST.get('location')
                lost_item_name = request.POST.get('lost_item_name')
                description = request.POST.get('description')
                date_lost = request.POST.get('date_lost')
                image = request.FILES.get('image')

                # Validate required fields
                if not (name and mobile_number and location and lost_item_name and description and date_lost):
                    return JsonResponse({'error': 'Missing required fields.'}, status=400)

                # Parse and validate date
                try:
                    date_lost = datetime.strptime(date_lost, '%d/%m/%Y').date()
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format. Use dd/mm/yyyy.'}, status=400)

                # Save the lost item
                lost_item = LostItem(
                    name=name,
                    mobile_number=mobile_number,
                    location=location,
                    lost_item_name=lost_item_name,
                    description=description,
                    date_lost=date_lost,
                    image=image
                )
                lost_item.save()

                return JsonResponse({'message': 'Lost item submitted successfully!'}, status=201)

            return JsonResponse({'error': 'Unsupported content type.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
def get_recent_lost_items(request):
    try:
        # Retrieve the most recent 9 lost items ordered by the 'date_lost' field
        recent_lost_items = LostItem.objects.all().order_by('-date_lost')

        # Create a list of dictionaries to hold the lost item data
        lost_items_data = []
        for item in recent_lost_items:
            lost_items_data.append({
                'name': item.name,
                'mobile_number': item.mobile_number,
                'location': item.location,
                'lost_item_name': item.lost_item_name,
                'description': item.description,
                'date_lost': item.date_lost.strftime('%d/%m/%Y'),
                'image': item.image.url if item.image else None,  # Add image URL if available
            })

        return JsonResponse({'recent_lost_items': lost_items_data}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def submit_found_item(request):
    if request.method == 'POST':
        try:
            # Handle form-data separately
            if request.content_type.startswith('multipart/form-data'):
                # Parse form-data
                name = request.POST.get('name')
                mobile_number = request.POST.get('mobile_number')
                location = request.POST.get('location')
                found_item_name = request.POST.get('found_item_name')
                description = request.POST.get('description')
                date_found = request.POST.get('date_found')
                image = request.FILES.get('image')

                # Validate required fields
                if not (name and mobile_number and location and found_item_name and description and date_found):
                    return JsonResponse({'error': 'Missing required fields.'}, status=400)

                # Parse and validate date
                try:
                    date_found = datetime.strptime(date_found, '%d/%m/%Y').date()
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format. Use dd/mm/yyyy.'}, status=400)

                # Save the found item
                found_item = FoundItem(
                    name=name,
                    mobile_number=mobile_number,
                    location=location,
                    found_item_name=found_item_name,
                    description=description,
                    date_found=date_found,
                    image=image
                )
                found_item.save()

                return JsonResponse({'message': 'Found item submitted successfully!'}, status=201)

            return JsonResponse({'error': 'Unsupported content type.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
def get_recent_found_items(request):
    try:
        # Retrieve the most recent 9 found items ordered by the 'date_found' field
        recent_found_items = FoundItem.objects.all().order_by('-date_found')[:9]

        # Create a list of dictionaries to hold the found item data
        found_items_data = []
        for item in recent_found_items:
            found_items_data.append({
                'name': item.name,
                'mobile_number': item.mobile_number,
                'location': item.location,
                'found_item_name': item.found_item_name,
                'description': item.description,
                'date_found': item.date_found.strftime('%d/%m/%Y'),
                'image': item.image.url if item.image else None,  # Add image URL if available
            })

        return JsonResponse({'recent_found_items': found_items_data}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)