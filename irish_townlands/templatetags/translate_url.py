# This Python file uses the following encoding: utf-8

from django import template
from django.core.urlresolvers import reverse
from django.core.urlresolvers import resolve
from django.utils import translation

register = template.Library()

class TranslatedURL(template.Node):
    def __init__(self, language):
        self.language = language
    def render(self, context):
        import pudb ; pudb.set_trace()
        request_language = translation.get_language()
        translation.activate(request_language)
        view = resolve(context['request'].path)
        translation.activate(self.language)
        url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
        translation.activate(request_language)
        return url

@register.tag(name='translate_url')
def do_translate_url(parser, token):
    language = token.split_contents()[1]
    return TranslatedURL(language)
