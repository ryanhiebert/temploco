from __future__ import annotations

from typing import Union, Callable, Any, Self
from http import HTTPStatus
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
)
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import resolve_url, redirect
from django.db.models import Model, CharField, Q
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from .layout import LayoutResponse, PartialResponse


class HttpResponseSeeOtherRedirect(HttpResponseRedirectBase):
    status_code = HTTPStatus.SEE_OTHER


def redirect(
    to: Union[Callable[..., Any], str, Model],
    *args: Any,
    permanent: bool = False,
    see_other: bool = False,
    **kwargs: Any,
) -> Union[
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
    HttpResponseSeeOtherRedirect,
]:
    """
    Return an HttpResponseRedirect to the appropriate URL for the arguments
    passed.

    The arguments could be:

        * A model: the model's `get_absolute_url()` function will be called.

        * A view name, possibly with arguments: `urls.reverse()` will be used
          to reverse-resolve the name.

        * A URL, which will be used as-is for the redirect location.

    Issues a temporary redirect by default; pass permanent=True to issue a
    permanent redirect, or pass see_other=True to issue a see other redirect.
    """
    redirect_class = (
        HttpResponsePermanentRedirect
        if permanent
        else HttpResponseSeeOtherRedirect
        if see_other
        else HttpResponseRedirect
    )
    return redirect_class(resolve_url(to, *args, **kwargs))


def hx_redirect(
    request: HttpRequest,
    to: Union[Callable[..., Any], str, Model],
    *args: Any,
    permanent: bool = False,
    see_other: bool = False,
    **kwargs: Any,
) -> Union[
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
    HttpResponseSeeOtherRedirect,
    HttpResponse,
]:
    """
    Return an HttpResponseRedirect or an HttpResponse with the HX-Redirect
    header set to the appropriate URL for the arguments passed.

    The arguments could be:

        * A model: the model's `get_absolute_url()` function will be called.

        * A view name, possibly with arguments: `urls.reverse()` will be used
          to reverse-resolve the name.

        * A URL, which will be used as-is for the redirect location.

    Issues a temporary redirect by default; pass permanent=True to issue a
    permanent redirect, or pass see_other=True to issue a see other redirect.
    """
    if request.headers.get("HX-Request") == "true":
        # Future: Get response from the redirected URL if local and
        #         return that inline to avoid additional requests.
        return HttpResponse(headers={"HX-Redirect": resolve_url(to, *args, **kwargs)})
    return redirect(to, *args, permanent=permanent, see_other=see_other, **kwargs)


class Contact(Model):
    first = CharField(max_length=256)
    last = CharField(max_length=256)
    phone = CharField(max_length=256)
    email = CharField(max_length=256)


class TerminalLayoutResponse(LayoutResponse):
    """A layout response that will not compose with parents."""

    def compose(self, parent: LayoutResponse, /) -> Self:
        return self


def layout(request: HttpRequest) -> LayoutResponse:
    if request.headers.get("hx-target") == "layout":
        return TerminalLayoutResponse("")
    return LayoutResponse.render(request, "temploco/layout.html")


@require_GET
def contacts(request: HttpRequest) -> PartialResponse:
    search = request.GET.get("q")
    contacts = Contact.objects.all()
    if search is not None:
        contacts = contacts.filter(
            Q(first__icontains=search) | Q(last__icontains=search)
        )
    response = PartialResponse.render(
        request, "temploco/contacts/index.html", {"contacts": contacts}
    )
    return response


@require_http_methods(["GET", "POST"])
def new(request: HttpRequest) -> PartialResponse | HttpResponse:
    if request.method == "POST":
        Contact.objects.create(
            first=request.POST["first_name"],
            last=request.POST["last_name"],
            phone=request.POST["phone"],
            email=request.POST["email"],
        )
        return hx_redirect(request, "/contacts/", see_other=True)
    return PartialResponse.render(
        request, "temploco/contacts/new.html", {"contact": Contact()}
    )


@require_http_methods(["GET", "DELETE"])
def detail(request: HttpRequest, *, id: int) -> PartialResponse | HttpResponse:
    if request.method == "DELETE":
        Contact.objects.filter(id=id).delete()
        return hx_redirect(request, "/contacts/", see_other=True)
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
        return hx_redirect(request, f"/contacts/{contact.pk}/", see_other=True)
    contact = Contact.objects.get(id=id)
    return PartialResponse.render(
        request, "temploco/contacts/edit.html", {"contact": contact}
    )


@require_POST
def delete(request: HttpRequest, *, id: int) -> HttpResponse:
    contact = Contact.objects.get(id=id)
    contact.delete()
    return hx_redirect(request, "/contacts", see_other=True)
