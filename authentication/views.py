import json
from django.contrib import messages, auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View, generic
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from validate_email import validate_email

from .forms import UserChangeForm
from .utils import account_activation_token
from django.utils.encoding import force_bytes,force_str
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
import threading
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class RegistrationView(View):
    def get(self, request):
        return render(request, 'authentication/register.html')

    def post(self, request):
        # GET USER DATA
        # VALIDATE
        # create a user account

        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        context = {
            'fieldValues': request.POST
        }

        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password) < 6:
                    messages.error(request, 'Password too short')
                    return render(request, 'authentication/register.html', context)

                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                # user.is_active = False
                user.save()
                # current_site = get_current_site(request)
                # email_body = {
                #     'user': user,
                #     'domain': current_site.domain,
                #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                #     'token': account_activation_token.make_token(user),
                # }
                #
                # link = reverse('activate', kwargs={
                #                'uidb64': email_body['uid'], 'token': email_body['token']})
                #
                # email_subject = 'Activate your account'
                #
                # activate_url = 'http://'+current_site.domain+link
                #
                # email = EmailMessage(
                #     email_subject,
                #     'Hi '+user.username + ', Please the link below to activate your account \n'+activate_url,
                #     'noreply@semycolon.com',
                #     [email],
                # )
                # EmailThread(email).start()
                messages.success(request, 'Account successfully created')
                return redirect('login')

        return render(request, 'authentication/register.html')

class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        if not str(username).isalnum():
            return JsonResponse({'username_error': 'username should only contain alphanumeric characters'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'sorry username in use,choose another one '}, status=409)
        return JsonResponse({'username_valid': True})

class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'email_error': 'Email is invalid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'sorry email in use,choose another one '}, status=409)
        return JsonResponse({'email_valid': True})

# class VerificationView(View):
#     def get(self, request, uidb64, token):
#         try:
#             id = force_str(urlsafe_base64_decode(uidb64))
#             user = User.objects.get(pk=id)
#
#             if not account_activation_token.check_token(user, token):
#                 return redirect('login'+'?message='+'User already activated')
#
#             if user.is_active:
#                 return redirect('login')
#             user.is_active = True
#             user.save()
#
#             messages.success(request, 'Account activated successfully')
#             return redirect('login')
#
#         except Exception as ex:
#             pass
#
#         return redirect('login')

class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = auth.authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(request, 'Welcome, ' +
                                     user.username+' you are now logged in')
                    return redirect('expenses')
                # messages.error(
                #     request, 'Account is not active,please check your email')
                # return render(request, 'authentication/login.html')
            messages.error(
                request, 'Invalid credentials,try again')
            return render(request, 'authentication/login.html')

        messages.error(
            request, 'Please fill all fields')
        return render(request, 'authentication/login.html')

class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request, 'You have been logged out')
        return redirect('login')

class RequestPasswordResetEmail(View):
    def get(self, request):
        return render(request, 'authentication/reset-password.html')

    def post(self,request):
        email = request.POST['email']

        if User.objects.filter(email=email):
            # current_site = get_current_site(request)
            # email_body = {
            #     'user': user,
            #     'domain': current_site.domain,
            #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            #     'token': account_activation_token.make_token(user),
            # }
            #
            # link = reverse('activate', kwargs={
            #                'uidb64': email_body['uid'], 'token': email_body['token']})
            #
            # email_subject = 'Activate your account'
            #
            # activate_url = 'http://'+current_site.domain+link
            #
            # email = EmailMessage(
            #     email_subject,
            #     'Hi '+user.username + ', Please the link below to activate your account \n'+activate_url,
            #     'noreply@semycolon.com',
            #     [email],
            # )
            # EmailThread(email).start()

            return render(request, 'authentication/reset-password.html')
        return render(request, 'authentication/reset-password.html')

class CompletePasswordReset(View):
    def get(self, request,uid64,token):
        return render(request, 'authentication/set-newpassword.html')
    def post(self,request,uid64,token):
        # PasswordResetTokenGenerator
        #     try:
        #         user_id = force_str(urlsafe_base64_decode(uid64)
        #         user= User.objects.get(pk=user_id)
        #         user.password = password
        #         user.save()
        #         messages.success(request,'Password reset successful')
        #         return redirect('login')
        #     except Exception as identifier:
        #        messages.error(request,'try again')

        return render(request, 'authentication/set-newpassword.html')

class EmailThread(threading.Thread):
    # speeding up sending email
    def __init__(self,email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
       self.email.send(fail_silently=False)


class UserEditView(LoginRequiredMixin,generic.UpdateView):
    login_url = '/login/'
    redirect_field_name = 'login'
    form_class = UserChangeForm
    template_name = 'authentication/profile.html'
    success_url = reverse_lazy('expenses')

    def get_object(self, queryset=None):
        return self.request.user