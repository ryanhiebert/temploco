from __future__ import annotations

from typing import Callable, Optional, Any
from django.http import HttpRequest, HttpResponse
from django.urls.resolvers import URLPattern, URLResolver
from django.urls import path, include


class Content:
    """What a page layout should return.

    Needs to have headers too.
    Status code?
    How much of a response should it emulate?
    Should it just be a response itself,
    and the content gets put together?
    Or perhaps should it be a special response subclass?
    """

    def __init__(self, text: str = ""):
        self.text = text

    def __str__(self):
        return self.text


class Layout:
    """What a layout route should return.

    Should a layout route be allowed to just return content directly? i think so. it seems like a useful way to give more power.
    How much of a response can a layout emulate?
    Can a layout include headers?
    Can the layout be a standard response and we find and replace a token?
    Or perhaps we have a special `LayoutResponse` response subclass?

    I don't think that the layout needs to be able to add any response
    parameters or anything. Seems like the child may be able to handle
    all of that by itself. So layouts may not need to be a response at
    all, while content might just be a response, or might be a signal
    subclass of response.
    """

    def __init__(self, pre: str = "", post: str = "", /):
        self.pre = pre
        self.post = post


class Route:
    def __init__(
        self,
        *,
        path: str = "",
        view: Optional[Callable[..., Layout | Content]] = None,
        children: Optional[list[Route]] = None,
    ):
        def noop_view(request: HttpRequest, /, **kwargs: Any) -> Layout:
            return Layout()

        self.__path = path
        self.__view = view or noop_view
        self.__children = children or []

    def __resolver(
        self, resolve_parent: Optional[Callable[..., Layout | Content]] = None, /
    ) -> Callable[..., Layout | Content]:
        def resolve(request: HttpRequest, **kwargs: Any) -> Layout | Content:
            parent = resolve_parent(request, **kwargs) if resolve_parent else Layout()
            if isinstance(parent, Content):
                return parent
            resolved = self.__view(request, **kwargs)
            if isinstance(resolved, Layout):
                return Layout(parent.pre + resolved.pre, parent.post + resolved.post)
            return Content("".join([parent.pre, resolved.text, parent.post]))

        return resolve

    @staticmethod
    def __create_view(
        resolve: Callable[..., Layout | Content]
    ) -> Callable[..., HttpResponse]:
        def routeview(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            resolved = resolve(request, **kwargs)
            if isinstance(resolved, Layout):
                resolved = Content("".join([resolved.pre, "", resolved.post]))
            return HttpResponse(resolved.text)

        return routeview

    def path(
        self, *, resolve_parent: Optional[Callable[..., Layout | Content]] = None
    ) -> URLPattern | URLResolver:
        """Construct the path to include in the URLConf."""
        resolve = self.__resolver(resolve_parent)
        if self.__children:
            return path(
                self.__path,
                include(
                    [child.path(resolve_parent=resolve) for child in self.__children]
                ),
            )
        return path(self.__path, self.__create_view(resolve))


route = Route(
    view=lambda r: Layout("&lt;root&gt;", "&lt;/root&gt;"),
    children=[
        Route(path="x/", view=lambda r: Content("x")),
        Route(path="y/", view=lambda r: Content("y")),
    ],
)


############
## IDEAS ###
############

# Immediately show a item as deleted even though there's a delay between
# insert and read, such as replicating to elasticsearch.

# Lazy load sub-routes.

# Infinite scroll.

# Routes that are _only_ ever used for partial, lazy templates.
# They seem like they should be gathered under the related parent,
# but will not make sense to load as their own page.
#
# If they did load as the initial, it would load as the parent page
# with any other segments being loaded lazily. But in that case it
# should redirect to the "real" parent route, and may as well do that
# immediately rather than even running the views at all.

# Form submissions with alternative methods, like PUT, PATCH, DELETE.
