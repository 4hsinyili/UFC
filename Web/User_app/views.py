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


# def custom_login(request):
#     if request.user.is_authenticated:
#         return redirect('/dinerlist')
#     else:
#         return login(request, request.user)


# def custom_logout(request):
#     if request.user.is_authenticated:
#         return logout(request)
#     else:
#         return redirect('/dinerlist')

# def login(response):
#     if response.method == "POST":
#         form = LoginForm(response.POST)
#         if form.is_valid():
#             form.save()
#         return redirect("/dinerlist")
#     else:
#         form = RegisterForm()

#     return render(response, 'User_app/login.html', {"form": form})


def collection(response):
    if response.user.is_authenticated:
        return render(response, 'User_app/collection.html', {})
    else:
        return redirect('login')


test_users = [
    {
        'name': 'test_1',
        'ematil': 'test_1@gmail.com',
        'password': '8rue9f93jtn2oi3rjo23'
    }
]
