from django.shortcuts import render

# Create your views here.


def handle_not_found(request, exception):
    return render(request, 'Helper_app/404.html', {})
