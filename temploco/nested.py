from __future__ import annotations

from typing import Callable, Optional, Any
from django.http import HttpRequest, HttpResponse
from django.urls.resolvers import URLPattern, URLResolver
from django.urls import path, re_path, include


class LayoutNotRenderedError(Exception):
    """The layout needs to be rendered before this action."""


class PartialResponse(HttpResponse):
    """A response to nest in layouts."""

    # This is modeled heavily after TemplateResponse, because Django
    # automatically runs the render method on to handle it, and we
    # are going to want to make sure we can do the same in a custom
    # TemplateResponse subclass.

    def __init__(
        self,
        content: str = "",
        content_type: Any = None,
        status: Any = None,
        charset: Any = None,
        headers: Any = None,
    ):
        # content will be replaced with rendered content, so we always
        # pass an empty string here so the base initializer can use our
        # content set method without errors.
        super().__init__("", content_type, status, charset=charset, headers=headers)
        self.__content: str = content
        self.__rendered: bool = False

    @property
    def layout(self) -> Layout:
        """The layout to use for this response."""
        return self.__layout  # Raises if not yet set

    @layout.setter
    def layout(self, value: Layout):
        """Set the layout for this response.

        This cannot be done at construction time, because the purpose
        is to decouple layouts from views. The content cannot be set
        immediately, because some ``HttpReponse`` subclassses, like
        ``TemplateResponse``, do not render their template until the
        render() method is called automatically by Django.
        """
        self.__layout: Layout = value

    def render(self) -> HttpResponse:
        """Render (thereby finalizing) the content of the response.

        If the content has already been rendered, this is a no-op.

        Return the baked response instance.
        """
        self.content = self.layout.fill(self.__content)
        self.__rendered = True
        return self

    def __iter__(self):
        if not self.__rendered:
            raise LayoutNotRenderedError(
                "The response content must be rendered before it can be iterated over."
            )
        return super().__iter__()

    @property
    def content(self):
        if not self.__rendered:
            raise LayoutNotRenderedError(
                "The response content must be rendered before it can be accessed."
            )
        return super().content

    @content.setter
    def content(self, value: Any):
        HttpResponse.content.fset(self, value)


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

    I do think that layouts will probably need to be involved in
    determining things like cache headers. I'm not sure how that
    should work yet, but a cache header needs to take into account
    the longevity of the info in the view as well as the longevity
    of any info in the layout.
    """

    def __init__(self, pre: str = "", post: str = "", /):
        self.__pre = pre
        self.__post = post

    def compose(self, content: Layout, /) -> Layout:
        return Layout(self.__pre + content.__pre, content.__post + self.__post)

    def fill(self, content: str, /) -> str:
        return self.__pre + content + self.__post


class Route:
    def __init__(
        self,
        *,
        path: str = "",
        layout: Optional[Callable[..., Layout]] = None,
        children: Optional[list[Route]] = None,
        view: Optional[Callable[..., HttpResponse]] = None,
        name: Optional[str] = None,
    ):
        self.__path = path
        self.__layout = layout or (lambda *a, **kw: Layout())
        self.__children = children or []
        self.__view = view
        self.__name = name

    def __resolver(
        self,
        /,
        *,
        full_path: str,
        resolve_layout: Callable[..., Layout],
    ) -> Callable[..., Layout]:
        urlpattern = re_path(r".*", lambda *a, **kw: HttpResponse())
        urlresolver = re_path(r"^/", include([path(full_path, include([urlpattern]))]))

        def resolve(request: HttpRequest, **kwargs: Any) -> Layout:
            layout = resolve_layout(request, **kwargs)
            resolver_match = urlresolver.resolve(request.path)
            resolved = self.__layout(request, **resolver_match.kwargs)
            return layout.compose(resolved)

        return resolve

    def __create_view(
        self, resolve_layout: Callable[..., Layout], /
    ) -> Callable[..., HttpResponse]:
        view = self.__view
        if not view:
            raise Exception("No view given for this path.")

        def routeview(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            response = view(request, **kwargs)
            if isinstance(response, PartialResponse):
                response.layout = resolve_layout(request, **kwargs)
            return response

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
        resolve = self.__resolver(full_path=full_path, resolve_layout=resolve_parent)
        if self.__children:
            child_paths = [
                child.path(parent_path=full_path, resolve_parent=resolve)
                for child in self.__children
            ]
            return path(self.__path, include(child_paths))
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

# Caching: if the layout has expired client-side, then it should
# automatically fill in from a higher parent route. I don't know
# yet whether that could be determined effectively server-side,
# or whether that would require client-side cooperation.
