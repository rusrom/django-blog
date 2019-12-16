from django.shortcuts import render, get_object_or_404
from .models import Post, Comment

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView

from django.core.mail import send_mail
from .forms import EmailPostForm, CommentForm, SearchForm

from taggit.models import Tag

from django.db.models import Count

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity


# Post LIst FBV
# def post_list(request):
#     object_list = Post.published.all()

#     paginator = Paginator(object_list, 3)  # По 3 статьи на каждой странице.
#     page = request.GET.get('page')

#     # Variant 1: aginator.page(number)
#     # Returns a Page object with the given 1-based index. Raises InvalidPage if the given page number doesn’t exist.
#     # https://docs.djangoproject.com/en/2.2/topics/pagination/#django.core.paginator.Paginator.page

#     # try:
#     #     posts = paginator.page(page)
#     # except PageNotAnInteger:
#     #     # Если страница не является целым числом, возвращаем первую страницу
#     #     posts = paginator.page(1)
#     # except EmptyPage:
#     #     # Если номер страницы больше, чем общее количество страниц, возвращаем последнюю
#     #     posts = paginator.page(paginator.num_pages)
#     # return render(request, 'blog/post/list.html', {'page': page, 'posts': posts})

#     # Variant 2: Paginator.get_page(number)
#     # Returns a Page object with the given 1-based index, while also handling out of range and invalid page numbers.
#     # https://docs.djangoproject.com/en/2.2/topics/pagination/#django.core.paginator.Paginator.get_page

#     posts = paginator.get_page(page)
#     return render(request, 'blog/post/list.html', {'posts': posts})


# Post LIst FBV
def post_list(request, tag_slug=None):
    object_list = Post.published.all()

    # Default for post list
    tag = None

    # For post list by tag
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__name__in=[tag])

    paginator = Paginator(object_list, 5)  # По 3 статьи на каждой странице.
    page = request.GET.get('page')

    # Variant 1: aginator.page(number)
    # Returns a Page object with the given 1-based index. Raises InvalidPage if the given page number doesn’t exist.
    # https://docs.djangoproject.com/en/2.2/topics/pagination/#django.core.paginator.Paginator.page

    # try:
    #     posts = paginator.page(page)
    # except PageNotAnInteger:
    #     # Если страница не является целым числом, возвращаем первую страницу
    #     posts = paginator.page(1)
    # except EmptyPage:
    #     # Если номер страницы больше, чем общее количество страниц, возвращаем последнюю
    #     posts = paginator.page(paginator.num_pages)
    # return render(request, 'blog/post/list.html', {'page': page, 'posts': posts})

    # Variant 2: Paginator.get_page(number)
    # Returns a Page object with the given 1-based index, while also handling out of range and invalid page numbers.
    # https://docs.djangoproject.com/en/2.2/topics/pagination/#django.core.paginator.Paginator.get_page
    posts = paginator.get_page(page)

    return render(request, 'blog/post/list.html', {'posts': posts, 'tag': tag})


# Post List CBV
class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status='published',
        publish__year=year,
        publish__month=month,
        publish__day=day,
        slug=post,
    )

    # List of active comments for this post
    comments = post.comments.filter(active=True)

    new_comment = None
    # Check was new comment posted
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid:
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # # Save the comment to the database
            new_comment.save()
    else:
        comment_form = CommentForm()

    # ФОРМИРОВАНИЕ СПИСКА ПОХОЖИХ СТАТЕЙ.

    # Получить все теги для текущей статьи
    # https://docs.djangoproject.com/en/2.2/ref/models/querysets/#values-list
    post_tag_ids = post.tags.values_list('id', flat=True)

    # Получить все статьи, которые связаны хотя бы с одним тегом
    # Исключить текущую статью из списка похожих
    similar_posts = Post.published.filter(tags__in=post_tag_ids)\
        .exclude(id=post.id)

    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
        .order_by('-same_tags', '-publish')[:4]

    context = {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'similar_posts': similar_posts,
    }

    return render(request, 'blog/post/detail.html', context)


def post_share(request, post_id):
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # All form fields passed validation
            cd = form.cleaned_data
            # Send email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{post_title} | Recommended by {name} ({email})'.format(
                name=cd['name'],
                email=cd['email'],
                post_title=post.title,
            )
            message = 'Recommended post: "{post_title}"\nDirect link to post: {post_url}\n\n{sender}\'s comment:\n{comment}'.format(
                post_title=post.title,
                post_url=post_url,
                sender=cd['name'],
                comment=cd['comments'],
            )
            recipients = [cd['to']]
            send_mail(subject, message, 'sale@doman-cards.com.ua', recipients)
            sent = True
    else:
        form = EmailPostForm()

    context = {
        'post': post,
        'form': form,
        'sent': sent,
    }
    return render(request, 'blog/post/share.html', context)


def post_search(request):
    form = SearchForm()
    query = None
    results = None

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            # 1 Easy search: Searching against multiple fields
            # results = Post.objects.annotate(search=SearchVector('title', 'body')).filter(search=query)

            # 2 Improved search: Stemming and ranking results
            # search_vector = SearchVector('title', 'body')
            # search_query = SearchQuery(query)
            # results = Post.objects.annotate(
            #     search=search_vector,
            #     rank=SearchRank(search_vector, search_query)
            # ).filter(search=search_query).order_by('-rank')

            # 3 Weighting queries search:
            # more relevance to posts that are matched by title rather than by content
            # search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            # search_query = SearchQuery(query)
            # results = Post.objects.annotate(
            #     rank=SearchRank(search_vector, search_query)
            # ).filter(rank__gte=0.3).order_by('-rank')

            # 4 trigram similarity search
            results = Post.objects.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.3).order_by('-similarity')

    return render(
        request,
        'blog/post/search.html',
        {
            'form': form,
            'query': query,
            'results': results
        }
    )
