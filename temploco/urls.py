from django.urls import path
from nested import Route, Layout, Content

from .index import index
from . import contacts


app_name = "temploco"
urlpatterns = [
    path("", index, name="index"),
    path("contacts/", contacts.contacts, name="contacts"),
    path("contacts/new", contacts.New.as_view(), name="contacts-new"),
    path("contacts/<int:id>/", contacts.Detail.as_view(), name="contacts-detail"),
    path("contacts/<int:id>/edit", contacts.Edit.as_view(), name="contacts-detail"),
    path("contacts/<int:id>/delete", contacts.Delete.as_view(), name="contacts-detail"),
    Route(
        view=lambda r: Layout("&lt;root&gt;", "&lt;/root&gt;"),
        children=[
            Route(path="x/", view=lambda r: Content("x")),
            Route(path="y/", view=lambda r: Content("y")),
        ],
    ).path(),
]
