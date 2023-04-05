from django.http import HttpRequest
from .nested import (
    Route,
    LayoutResponse,
    PartialResponse,
)

from .index import index
from . import contacts


def spam(request: HttpRequest, spam_id: int):
    return LayoutResponse.render(
        request,
        "temploco/nested/spam.html",
        {"spam_id": spam_id},
    )


def eggs_x(request: HttpRequest, spam_id: int, eggs_id: int):
    return PartialResponse.render(
        request,
        "temploco/nested/x.html",
        {"spam_id": spam_id, "eggs_id": eggs_id},
    )


def eggs_y(request: HttpRequest, spam_id: int, eggs_id: int):
    return PartialResponse.render(
        request,
        "temploco/nested/y.html",
        {"spam_id": spam_id, "eggs_id": eggs_id},
    )


app_name = "temploco"
urlpatterns = [
    Route(
        path="",
        children=[
            Route(path="", view=index, name="index"),
            Route(path="contacts", view=contacts.contacts, name="contacts"),
            Route(
                path="contacts/new", view=contacts.New.as_view(), name="contacts-new"
            ),
            Route(
                path="contacts/<int:id>/",
                view=contacts.Detail.as_view(),
                name="contacts-detail",
            ),
            Route(
                path="contacts/<int:id>/edit",
                view=contacts.Edit.as_view(),
                name="contacts-edit",
            ),
            Route(
                path="contacts/<int:id>/delete",
                view=contacts.Delete.as_view(),
                name="contacts-delete",
            ),
            Route(
                path="spam/<int:spam_id>/",
                layout=spam,
                children=[
                    Route(path="x/<int:eggs_id>/", view=eggs_x, name="spam-x"),
                    Route(path="y/<int:eggs_id>/", view=eggs_y, name="spam-y"),
                ],
            ),
        ],
    ).path()
]
