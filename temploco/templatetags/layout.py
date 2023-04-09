from typing import Any
from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def outlet(context: dict[str, Any]) -> str:
    return format_html(context['__outlet_divider__'])
