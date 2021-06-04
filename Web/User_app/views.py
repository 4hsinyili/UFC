# from django.http import request
from django.shortcuts import redirect, render
from .forms import RegisterForm, LoginForm
from django.contrib import auth
# Create your views here.


def register(request):
    if request.method == 'GET':
        form = RegisterForm()
        context = {'form': form}
        return render(request, 'User_app/register.html', context)
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            return redirect("/dinerlist")


def login(request):
    if request.user.is_authenticated:
        return redirect("/dinerlist")
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(email)
        print(password)
        user = auth.authenticate(email=email, password=password)
        if user:
            auth.login(request, user)
            return redirect("/dinerlist")
        else:
            print('invalid')
            print(form.errors)
            form = LoginForm()
            context = {'form': form}
            return render(request, 'User_app/login.html', context)
    if request.method == 'GET':
        form = LoginForm()
        context = {'form': form}
        return render(request, 'User_app/login.html', context)


def logout(request):
    auth.logout(request)
    return redirect("/dinerlist")
