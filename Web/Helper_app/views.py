from django.shortcuts import render

# Create your views here.


def handle_not_found(request, exception):
    return render(request, 'Helper_app/404.html', {'current_page': '404'})


def handle_server_error(request):
    return render(request, 'Helper_app/500.html', {'current_page': '500'})


def handle_rate_limited(request, exception):
    return render(request, 'Helper_app/rate_limited.html', {'current_page': 'Rate Limited'})
