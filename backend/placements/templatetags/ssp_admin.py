from django import template

register = template.Library()


@register.simple_tag
def ssp_admin_summary():
    from placements.admin import admin_summary

    return admin_summary()
