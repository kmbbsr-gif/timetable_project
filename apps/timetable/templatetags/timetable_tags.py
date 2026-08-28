from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_item_tuple(dictionary, period, class_id, section_id):
    return dictionary.get((period, class_id, section_id))
@register.filter
def make_key(day, period):
    return f"{day}_{period}"
@register.filter
def neg(value):
    return -value