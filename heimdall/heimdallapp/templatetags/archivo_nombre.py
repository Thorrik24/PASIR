from django import template

register = template.Library()

@register.filter
def archivo(value):
    return str(value).split("/")[1]