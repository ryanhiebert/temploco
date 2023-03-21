from __future__ import annotations

from typing import Callable, Optional, Any
from django.http import HttpRequest, HttpResponse
from django.urls.resolvers import URLPattern, URLResolver
from django.urls import path, re_path, include


class Content:
    """What a page layout should return.

    Needs to have headers too.
    Status code?
    How much of a response should it emulate?
    Should it just be a response itself,
    and the content gets put together?
    Or perhaps should it be a special response subclass?
    """

    def __init__(self, text: str = "", /):
        self.__text = text

    def __str__(self, /):
        return self.__text


class Layout:
    """What a layout route should return.

    Should a layout route be allowed to just return content directly? i think so. it seems like a useful way to give more power.
      update: I no longer think this. Instead, I think to have two
              types of layout, one that can be filled, and one that
              throws away any content that would fill it.
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
        self.__pre = pre
        self.__post = post

    def __str__(self, /):
        return self.__pre + self.__post

    def compose(self, content: Layout, /) -> Layout:
        return Layout(self.__pre + content.__pre, content.__post + self.__post)

    def fill(self, content: Content, /) -> Content:
        return Content(self.__pre + str(content) + self.__post)


class Route:
    def __init__(
        self,
        *,
        path: str = "",
        layout: Optional[Callable[..., Layout]] = None,
        children: Optional[list[Route]] = None,
        view: Optional[Callable[..., Content]] = None,
        name: Optional[str] = None,
    ):
        self.__path = path
        self.__layout = layout or (lambda *a, **kw: Layout())
        self.__children = children or []
        self.__view = view or (lambda *a, **kw: Content())
        self.__name = name

    def __resolver(
        self,
        /,
        *,
        full_path: str,
        resolve_parent: Callable[..., Layout],
    ) -> Callable[..., Layout]:
        urlpattern = re_path(r".*", lambda *a, **kw: HttpResponse())
        urlresolver = re_path(r"^/", include([path(full_path, include([urlpattern]))]))

        def resolve(request: HttpRequest, **kwargs: Any) -> Layout:
            parent = resolve_parent(request, **kwargs)
            resolver_match = urlresolver.resolve(request.path)
            resolved = self.__layout(request, **resolver_match.kwargs)
            return parent.compose(resolved)

        return resolve

    def __create_view(
        self, resolve_parent: Callable[..., Layout], /
    ) -> Callable[..., HttpResponse]:
        def routeview(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            content = self.__view(request, **kwargs)
            parent = resolve_parent(request, **kwargs)
            return HttpResponse(str(parent.fill(content)))

        return routeview

    def path(
        self,
        /,
        *,
        parent_path: str = "",
        resolve_parent: Optional[Callable[..., Layout]] = None,
    ) -> URLPattern | URLResolver:
        """Construct the path to include in the URLConf."""
        full_path = parent_path + self.__path
        resolve_parent = resolve_parent or (lambda *a, **kw: Layout())
        resolve = self.__resolver(full_path=full_path, resolve_parent=resolve_parent)
        if self.__children:
            return path(
                self.__path,
                include(
                    [
                        child.path(parent_path=full_path, resolve_parent=resolve)
                        for child in self.__children
                    ]
                ),
            )
        if not self.__name:
            # Routes with children don't need to be reversed, but routes
            # without children might need to be. Since we construct an
            # internal view, there's no view function to reverse with.
            raise Exception("name required for routes without children.")
        return path(self.__path, self.__create_view(resolve), name=self.__name)


############
## IDEAS ###
############

# Immediately show an item as deleted even though there's a delay
# between insert and read, such as replicating to elasticsearch.

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
