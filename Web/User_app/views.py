from django.shortcuts import redirect, render
from .forms import RegisterForm
# from django.contrib.auth import login, logout
# Create your views here.


def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save()
        return redirect("/dinerlist")
    else:
        form = RegisterForm()

    return render(response, 'User_app/register.html', {"form": form})
