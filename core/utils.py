from django.core.mail import send_mail

def send_otp_email(user):
    subject = 'Your OTP for Signup'
    message = f'Your OTP is {user.otp.otp_code}. It is valid for 10 minutes.'
    send_mail(subject, message, 'your-email@example.com', [user.email])
