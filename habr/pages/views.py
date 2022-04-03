from django.shortcuts import render, get_object_or_404

from pages.models import Pages


def detail(request, slug):
    page = get_object_or_404(Pages, slug=slug)
    content = {
        'title': page.seo_title,
        'content': page,

    }
    print(page.page_type.type_of_page)
    print(f'pages/figma_page/{page.content}')
    if page.page_type.type_of_page == 'figma':
        return render(request, f'pages/figma_pages/{page.content}', content)
    return render(request, 'pages/page.html', content)
