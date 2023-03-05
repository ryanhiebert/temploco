from django.urls import path

from .index import index
from .contacts import contacts

app_name = "temploco"
urlpatterns = [
    path("", index, name="index"),
    path("contacts/", contacts, name="contacts"),
]
