# from django.http import request
from django.shortcuts import redirect, render
from .forms import RegisterForm, LoginForm
# Create your views here.


def register(request):
    if request.user.is_authenticated:
        return redirect("/dinerlist")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            login(request)
        return redirect("/user/login")
    else:
        form = RegisterForm()

    return render(request, 'User_app/register.html', {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("/dinerlist")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect("/dinerlist")
    else:
        form = LoginForm()

    return render(request, 'User_app/login.html', {"form": form})


def collection(request):
    if request.user.is_authenticated:
        return render(request, 'User_app/collection.html', {})
    else:
        return redirect('login')


test_users = [
    {
        'name': 'test_1',
        'ematil': 'test_1@gmail.com',
        'password': '8rue9f93jtn2oi3rjo23'
    }
]
