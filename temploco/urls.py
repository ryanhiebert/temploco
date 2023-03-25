from django.http import HttpRequest
from .nested import Route, Layout, PartialResponse

from .index import index
from . import contacts


def spam_layout(request: HttpRequest, spam_id: int):
    return Layout(f"<p>HEADER {spam_id=}</p>", "<p>FOOTER</p>")


def eggs_x(request: HttpRequest, spam_id: int, eggs_id: int):
    return PartialResponse(f"<p>x {spam_id=} {eggs_id=}</p>")


def eggs_y(request: HttpRequest, spam_id: int, eggs_id: int):
    return PartialResponse(f"<p>y {spam_id=} {eggs_id=}</p>")


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
                layout=spam_layout,
                children=[
                    Route(path="x/<int:eggs_id>/", view=eggs_x, name="spam-x"),
                    Route(path="y/<int:eggs_id>/", view=eggs_y, name="spam-y"),
                ],
            ),
        ],
    ).path()
]
