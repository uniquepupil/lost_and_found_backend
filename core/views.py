from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import User, OTP
from .utils import send_otp_email
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
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

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return JsonResponse({'error': 'Email and password are required.'}, status=400)
            user = authenticate(request, username=email, password=password)
            if user is not None:
                return JsonResponse({'message': 'Login successful.', 'user': {'name': user.name, 'email': user.email}}, status=200)
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

