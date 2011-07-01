from django import template

register = template.Library()

@register.filter
def escape_dot(s):
	return s.replace('"', '\"')
