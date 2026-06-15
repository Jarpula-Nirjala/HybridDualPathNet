from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def about(request):
    return render(request, "core/about.html")


def how_to_use(request):
    return render(request, "core/how_to_use.html")
