from django.urls import path
from django.http import HttpRequest
from .nested import Route, Layout, Content

from .index import index
from . import contacts


def spam_layout(request: HttpRequest, spam_id: int):
    return Layout(f"<p>HEADER {spam_id=}</p>", "<p>FOOTER</p>")


def eggs_x(request: HttpRequest, spam_id: int, eggs_id: int):
    return Content(f"<p>x {spam_id=} {eggs_id=}</p>")


def eggs_y(request: HttpRequest, spam_id: int, eggs_id: int):
    return Content(f"<p>y {spam_id=} {eggs_id=}</p>")


app_name = "temploco"
urlpatterns = [
    path("", index, name="index"),
    path("contacts/", contacts.contacts, name="contacts"),
    path("contacts/new", contacts.New.as_view(), name="contacts-new"),
    path("contacts/<int:id>/", contacts.Detail.as_view(), name="contacts-detail"),
    path("contacts/<int:id>/edit", contacts.Edit.as_view(), name="contacts-detail"),
    path("contacts/<int:id>/delete", contacts.Delete.as_view(), name="contacts-detail"),
    Route(
        path="spam/<int:spam_id>/",
        view=spam_layout,
        children=[
            Route(path="x/<int:eggs_id>/", view=eggs_x),
            Route(path="y/<int:eggs_id>/", view=eggs_y),
        ],
    ).path(),
]
