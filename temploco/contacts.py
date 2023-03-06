from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Model, CharField, Q
from django.views import View


class Contact(Model):
    first = CharField(max_length=256)
    last = CharField(max_length=256)
    phone = CharField(max_length=256)
    email = CharField(max_length=256)


def contacts(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("q")
    contacts = Contact.objects.all()
    if search is not None:
        contacts = contacts.filter(
            Q(first__icontains=search) | Q(last__icontains=search)
        )
    return render(request, "temploco/contacts/index.html", {"contacts": contacts})


class New(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "temploco/contacts/new.html", {"contact": Contact()})

    def post(self, request: HttpRequest) -> HttpResponse:
        Contact.objects.create(
            first=request.POST["first_name"],
            last=request.POST["last_name"],
            phone=request.POST["phone"],
            email=request.POST["email"],
        )
        return redirect("/contacts/")


class Detail(View):
    def get(self, request: HttpRequest, *, id: int) -> HttpResponse:
        contact = Contact.objects.get(id=id)
        return render(request, "temploco/contacts/show.html", {"contact": contact})


class Edit(View):
    def get(self, request: HttpRequest, *, id: int) -> HttpResponse:
        contact = Contact.objects.get(id=id)
        return render(request, "temploco/contacts/edit.html", {"contact": contact})

    def post(self, request: HttpRequest, *, id: int) -> HttpResponse:
        contact = Contact.objects.get(id=id)
        contact.first = request.POST["first_name"]
        contact.last = request.POST["last_name"]
        contact.phone = request.POST["phone"]
        contact.email = request.POST["email"]
        contact.save()
        return redirect(f"/contacts/{contact.pk}/")


class Delete(View):
    def post(self, request: HttpRequest, *, id: int) -> HttpResponse:
        contact = Contact.objects.get(id=id)
        contact.delete()
        return redirect("/contacts")
