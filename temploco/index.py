from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


def index(request: HttpRequest) -> HttpResponse:
    return redirect("temploco:contacts")
