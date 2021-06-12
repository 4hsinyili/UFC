from django.shortcuts import render

# Create your views here.


def handle_not_found(request, exception):
    return render(request, 'Helper_app/404.html', {})


def handle_server_error(request):
    return render(request, 'Helper_app/500.html', {})
