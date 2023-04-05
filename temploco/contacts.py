from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.db.models import Model, CharField, Q
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from .nested import LayoutResponse, PartialResponse


class Contact(Model):
    first = CharField(max_length=256)
    last = CharField(max_length=256)
    phone = CharField(max_length=256)
    email = CharField(max_length=256)


def layout(request: HttpRequest) -> LayoutResponse:
    return LayoutResponse.render(request, "temploco/layout.html")


@require_GET
def contacts(request: HttpRequest) -> PartialResponse:
    search = request.GET.get("q")
    contacts = Contact.objects.all()
    if search is not None:
        contacts = contacts.filter(
            Q(first__icontains=search) | Q(last__icontains=search)
        )
    return PartialResponse.render(
        request, "temploco/contacts/index.html", {"contacts": contacts}
    )


@require_http_methods(["GET", "POST"])
def new(request: HttpRequest) -> PartialResponse | HttpResponse:
    if request.method == "POST":
        Contact.objects.create(
            first=request.POST["first_name"],
            last=request.POST["last_name"],
            phone=request.POST["phone"],
            email=request.POST["email"],
        )
        return redirect("/contacts/")
    return PartialResponse.render(
        request, "temploco/contacts/new.html", {"contact": Contact()}
    )


@require_GET
def detail(request: HttpRequest, *, id: int) -> PartialResponse:
    contact = Contact.objects.get(id=id)
    return PartialResponse.render(
        request, "temploco/contacts/show.html", {"contact": contact}
    )


@require_http_methods(["GET", "POST"])
def edit(request: HttpRequest, *, id: int) -> PartialResponse | HttpResponse:
    if request.method == "POST":
        contact = Contact.objects.get(id=id)
        contact.first = request.POST["first_name"]
        contact.last = request.POST["last_name"]
        contact.phone = request.POST["phone"]
        contact.email = request.POST["email"]
        contact.save()
        return redirect(f"/contacts/{contact.pk}/")
    contact = Contact.objects.get(id=id)
    return PartialResponse.render(
        request, "temploco/contacts/edit.html", {"contact": contact}
    )


@require_POST
def delete(request: HttpRequest, *, id: int) -> HttpResponse:
    contact = Contact.objects.get(id=id)
    contact.delete()
    return redirect("/contacts")
