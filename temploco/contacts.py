from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Model, CharField, Q


class Contact(Model):
    first = CharField(max_length=256)
    last = CharField(max_length=256)
    phone = CharField(max_length=256)
    email = CharField(max_length=256)


def contacts(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("q")
    if search is not None:
        contacts = Contact.objects.filter(
            Q(first__icontains=search)
            | Q(last__icontains=search)
        )
    contacts = Contact.objects.all()
    return render(request, "temploco/contacts/index.html", {"contacts": contacts})
