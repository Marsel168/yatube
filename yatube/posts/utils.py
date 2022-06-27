from django.conf import settings
from django.core.paginator import Paginator


def get_page_obj(request, post_list):
    """
    Возвращает набор записей для страницы с запрошенным номером.
    """
    paginator = Paginator(post_list, settings.LIMIT_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
