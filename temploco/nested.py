from __future__ import annotations

from typing import Callable, Optional
from django.http import HttpResponse
from django.urls.resolvers import URLPattern
from django.urls import path


class Content:
    """What a page layout should return.

    Needs to have headers too.
    Status code?
    How much of a response should it emulate?
    Should it just be a response itself,
    and the content gets put together?
    Or perhaps should it be a special response subclass?
    """

    def __init__(self, text: str):
        self.__text = text

    def __str__(self):
        return self.__text


class Layout:
    """What a layout route should return.

    Should a layout route be allowed to just return content directly? i think so. it seems like a useful way to give more power.
    How much of a response can a layout emulate?
    Can a layout include headers?
    Can the layout be a standard response and we find and replace a token?
    Or perhaps we have a special `LayoutResponse` response subclass?

    """

    def __init__(self, prelude: str, postlude: str):
        self.__prelude = prelude
        self.__postlude = postlude

    def fill(self, content: Content) -> Content:
        return Content(''.join([self.__prelude, str(content), self.__postlude]))


class Route:
    def __init__(
            self,
            *,
            path: str = "",
            view: Optional[Callable[..., Layout | Content]] = None,
            children: Optional[list[Route]] = None
        ):
        self.path = path
        self.view = view
        self.children = children or []

    def __route_chains(self: Route) -> list[list[Route]]:
        """Get the full and complete chain of routes."""
        if self.children:
            return [
                [self] + routes
                for child in self.children
                for routes in child.__route_chains()
            ]
        return [[self]]


    def urlpatterns(self) -> list[URLPattern]:
        """Construct url patterns to include in the URLConf."""
        def create_view(routes: list[Route]) -> Callable[..., HttpResponse]:
            def routeview() -> HttpResponse:
                raise NotImplementedError
            return routeview

        def create_path(routes: list[Route]) -> str:
            return ''.join(route.path for route in routes)

        return [
            path(create_path(routes), create_view(routes))
            for routes in self.__route_chains()
        ]


route = Route(
    path='',
    view=lambda: Layout('<root>', '</root>'),
    children=[
        Route(path='<int:x>', view=lambda: Content('x')),
        Route(path='<int:y>', view=lambda: Content('y')),
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
