from .nested import Route
from .index import index
from . import contacts


app_name = "temploco"
urlpatterns = [
    Route(
        path="",
        layout=contacts.layout,
        children=[
            Route(path="", view=index, name="index"),
            Route(path="contacts/", view=contacts.contacts, name="contacts"),
            Route(path="contacts/new", view=contacts.new, name="contacts-new"),
            Route(
                path="contacts/<int:id>/",
                view=contacts.detail,
                name="contacts-detail",
            ),
            Route(
                path="contacts/<int:id>/edit",
                view=contacts.edit,
                name="contacts-edit",
            ),
            Route(
                path="contacts/<int:id>/delete",
                view=contacts.delete,
                name="contacts-delete",
            ),
        ],
    ).path(),
]
