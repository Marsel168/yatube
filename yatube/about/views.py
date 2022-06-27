from django.views.generic import TemplateView


class AboutAuthorView(TemplateView):
    """Об авторе."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Технологии."""
    template_name = 'about/tech.html'
