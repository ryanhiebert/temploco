from django.urls import path

from .index import index
from . import contacts
from . import nested

app_name = "temploco"
urlpatterns = [
    path("", index, name="index"),
    path("contacts/", contacts.contacts, name="contacts"),
    path("contacts/new", contacts.New.as_view(), name="contacts-new"),
    path("contacts/<int:id>/", contacts.Detail.as_view(), name="contacts-detail"),
    path("contacts/<int:id>/edit", contacts.Edit.as_view(), name="contacts-detail"),
    path("contacts/<int:id>/delete", contacts.Delete.as_view(), name="contacts-detail"),
    *nested.route.urlpatterns(),
]
