from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify-otp'),
    path('user-details/', views.get_user_details, name='user-details'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('submit-lost-item/', views.submit_lost_item, name='submit_lost_item'),
    path('recent-lost-items/', views.get_recent_lost_items, name='recent_lost_items'),
    path('submit-found-item/', views.submit_found_item, name='submit_found_item'),
    path('recent-found-items/', views.get_recent_found_items, name='recent_found_item'),
]
