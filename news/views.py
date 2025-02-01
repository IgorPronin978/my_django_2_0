from django.http import HttpResponse


def main(request):
    return HttpResponse("Hello, world.") # Вернёт страницу с надписью "Hallo world"


def info(request):
    return HttpResponse("Information page")