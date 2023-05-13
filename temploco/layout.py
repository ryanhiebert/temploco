from __future__ import annotations

from typing import Callable, Optional, Any, Self, Dict
from functools import wraps
from dataclasses import dataclass
from django.http import HttpRequest, HttpResponse
from django.template import loader
import django.urls.resolvers
import django.urls


class LayoutResponse:
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

    __DIVIDER = "<django-layout></django-layout>"

    def __init__(self, content: Optional[str] = None):
        self.__content = content or self.__DIVIDER

    def compose(self, parent: LayoutResponse, /) -> Self:
        return LayoutResponse(parent.fill(self.__content))

    def fill(self, content: str, /) -> str:
        return self.__content.replace(self.__DIVIDER, content)

    @classmethod
    def render(
        cls,
        request: Optional[HttpRequest],
        template_name: list[str] | str,
        context: Optional[dict[str, Any]] = None,
        using: Optional[str] = None,
    ):
        context = context or {}
        context.setdefault("__outlet_divider__", cls.__DIVIDER)
        content = loader.render_to_string(template_name, context, request, using=using)
        return cls(content)


@dataclass
class PartialResponse:
    """A partial response ready to add combine with layouts."""

    content: str = ""
    content_type: Optional[str] = None
    status: Optional[int] = None
    charset: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    layout: Optional[LayoutResponse] = None

    @classmethod
    def render(
        cls,
        request: Optional[HttpRequest],
        template_name: list[str] | str,
        context: Optional[dict[str, Any]] = None,
        content_type: Optional[str] = None,
        status: Optional[int] = None,
        using: Optional[str] = None,
        *,
        charset: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        layout: Optional[LayoutResponse] = None,
    ):
        """Render a template to a PartialResponse."""
        content = loader.render_to_string(template_name, context, request, using=using)
        return cls(
            content,
            content_type,
            status,
            charset=charset,
            headers=headers,
            layout=layout,
        )


class LayoutURLResolver(django.urls.resolvers.URLResolver):
    """Automatically combine partial and layout responses."""

    layout = Optional[Callable[..., LayoutResponse]]

    def __init__(
        self,
        pattern: Any,
        urlconf_name: Optional[str],
        default_kwargs: Optional[Dict[str, Any]] = None,
        app_name: Optional[str] = None,
        namespace: Optional[str] = None,
        *,
        layout: Optional[Callable[..., LayoutResponse]] = None,
    ) -> None:
        super().__init__(pattern, urlconf_name, default_kwargs, app_name, namespace)
        self.layout = layout

    def __layout_func(self, func: Callable[..., Any]) -> Callable[..., Any]:
        if not self.layout:
            return func

        @wraps(func)
        def layout_func(*args: Any, **kwargs: Any):
            response = func(*args, **kwargs)
            if isinstance(response, PartialResponse):
                layout_response = response.layout
                if not layout_response and self.layout:
                    # TODO: Call with partial args
                    layout_response = self.layout(*args, **kwargs)
                respo
                if layout:
                    layout_response = layout(*args, **kwargs)
                response = HttpResponse(
                    content=layout_response.fill(response.content),
                )

        return layout_func

    def __create_view(
        self, layout: Callable[..., LayoutResponse], /
    ) -> Callable[..., HttpResponse]:
        view = self.__view
        if not view:
            raise Exception("No view given for this path.")

        def routeview(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            response = view(request, **kwargs)
            if isinstance(response, PartialResponse):
                layout_response = response.layout or layout(request, **kwargs)
                response = HttpResponse(
                    content=layout_response.fill(response.content),
                    content_type=response.content_type,
                    status=response.status,
                    charset=response.charset,
                    headers=response.headers,
                )
            return response

        return routeview

    def resolve(self, path: str) -> django.urls.resolvers.ResolverMatch:
        resolved = super().resolve(path)
        resolved.func = self.__layout_func(resolved.func)
        return resolved


class Route:
    def __init__(
        self,
        *,
        path: str = "",
        layout: Optional[Callable[..., LayoutResponse]] = None,
        children: Optional[list[Route]] = None,
        view: Optional[Callable[..., HttpResponse | PartialResponse]] = None,
        name: Optional[str] = None,
    ):
        self.__path = path
        self.__layout = layout or (lambda *a, **kw: LayoutResponse())
        self.__children = children or []
        self.__view = view
        self.__name = name

    def __resolver(
        self,
        /,
        *,
        full_path: str,
        resolve_layout: Callable[..., LayoutResponse],
    ) -> Callable[..., LayoutResponse]:
        urlpattern = django.urls.re_path(r".*", lambda *a, **kw: HttpResponse())
        urlresolver = django.urls.re_path(
            r"^/",
            django.urls.include(
                [django.urls.path(full_path, django.urls.include([urlpattern]))]
            ),
        )

        def resolve(request: HttpRequest, **kwargs: Any) -> LayoutResponse:
            layout = resolve_layout(request, **kwargs)
            resolver_match = urlresolver.resolve(request.path)
            resolved = self.__layout(request, **resolver_match.kwargs)
            return resolved.compose(layout)

        return resolve

    def __create_view(
        self, layout: Callable[..., LayoutResponse], /
    ) -> Callable[..., HttpResponse]:
        view = self.__view
        if not view:
            raise Exception("No view given for this path.")

        def routeview(request: HttpRequest, **kwargs: Any) -> HttpResponse:
            response = view(request, **kwargs)
            if isinstance(response, PartialResponse):
                layout_response = response.layout or layout(request, **kwargs)
                response = HttpResponse(
                    content=layout_response.fill(response.content),
                    content_type=response.content_type,
                    status=response.status,
                    charset=response.charset,
                    headers=response.headers,
                )
            return response

        return routeview

    def path(
        self,
        /,
        *,
        parent_path: str = "",
        resolve_parent: Optional[Callable[..., LayoutResponse]] = None,
    ) -> django.urls.resolvers.URLPattern | django.urls.resolvers.URLResolver:
        """Construct the path to include in the URLConf."""
        full_path = parent_path + self.__path
        resolve_parent = resolve_parent or (lambda *a, **kw: LayoutResponse())
        resolve = self.__resolver(full_path=full_path, resolve_layout=resolve_parent)
        if self.__children:
            child_paths = [
                child.path(parent_path=full_path, resolve_parent=resolve)
                for child in self.__children
            ]
            return django.urls.path(self.__path, django.urls.include(child_paths))
        if not self.__name:
            # Routes with children don't need to be reversed, but routes
            # without children might need to be. Since we construct an
            # internal view, there's no view function to reverse with.
            raise Exception("name required for routes without children.")
        return django.urls.path(
            self.__path, self.__create_view(resolve), name=self.__name
        )


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

# Partial, non-primary-route templates might also be non-lazy.
# For example, a layout route may need a partial template in order
# to have a form, with handling, in its template. This doesn't
# properly belong in the layout, where it doesn't really have its
# own URL, but we'd still want it to be server-rendered. We also
# want to make sure that the form action handler could be handled
# in the same function that generates the form, and that's what a
# view is for.

# It would be great for partials to (all?) declare their own caching
# parameters. It could make pages load very quickly.

# Prefetching links would be amazing.

# Error boundaries. Is that defined by the layout as a child
# alternative, or by the child? Or perhaps both approaches have
# merit, for different purposes.

# Non-default branch layouts open an interesting avenue of exploration.
# There should be able to be layouts. Even layouts that may not ever
# contribute anything to any part of a path. That take children,
# and still have the full power of logic-filled view and not merely
# a template. Even if all forms are required to be URL addressable.

# Maybe child routes _should_ be fully in charge of their own layouts.
# But typically can delegate them to the routing layer in order to
# enable the parallel magic. But maybe even that has to be explicitly
# chosen by some easy idomatic and largely transparent selection, such
# as a view decorator that implements a typical class prototype that
# could be overridden? How would that interact with typical Django CBVs?
