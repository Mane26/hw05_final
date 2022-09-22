from django.core.paginator import Paginator

POST_NUMBER = 10


def get_page(request, post_list):
    """ Паджинация 10 постов на страницу."""
    paginator = Paginator(post_list, POST_NUMBER)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
