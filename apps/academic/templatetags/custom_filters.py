from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key) if dictionary else None
@register.filter
def as_list(value):
    """Safely convert int/None to list for template iteration."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return value
    return [value]

@register.filter
def day_name(value):
    """Convert day number to short name. Handles int or string."""
    names = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    try:
        return names.get(int(value), str(value))
    except (ValueError, TypeError):
        return str(value)
    
from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """Split a string by the given delimiter."""
    if value:
        return [s.strip() for s in str(value).split(arg)]
    return []