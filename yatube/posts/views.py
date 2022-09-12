from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POST_NUMBER = 10


def get_page(request, post_list):
    # Паджинация 10 постов на страницу
    paginator = Paginator(post_list, POST_NUMBER)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    """Функция index передает данные в шаблон index.html."""
    template = 'posts/index.html'
    post_list = Post.objects.all().select_related(
        'author',
        'group'
    ).order_by('-pub_date')
    page_obj = get_page(request, post_list)
    # Здесь код запроса к модели и создание словаря контекста
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Функция group_posts передает данные в шаблон group_list.html."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related(
        'author'
    ).order_by('-pub_date')
    page_obj = get_page(request, post_list)
    # Здесь код запроса к модели и создание словаря контекста
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    """Здесь код запроса к модели и создание словаря контекста."""
    template = 'posts/profile.html'
    # В тело страницы выведен список постов
    author = get_object_or_404(
        User.objects.all().prefetch_related(
            'posts',
            'posts__group'
        ), username=username)
    posts_list = author.posts.all()
    page_obj = get_page(request, posts_list)
    # Здесь код запроса к модели и создание словаря контекста
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    profile = author

    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'profile': profile,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    """Здесь код запроса к модели и создание словаря контекста."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    # В тело страницы выведен один пост, выбранный по pk
    context = {
        'post': post,
        'form': form,

    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Добавлена "Новая запись" для авторизованных пользователей."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user)
    group_list = Group.objects.all()
    context = {
        'form': form,
        'group_list': group_list,
        'is_edit': False,
        'button_name': 'Добавить',
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Добавлена страница редактирования записи."""
    # Права на редактирование должны быть только у автора этого поста
    # Остальные пользователи должны перенаправляться
    # На страницу просмотра поста
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
        'button_name': 'Сохранить'
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'form': form,
    }

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_detail.html', context)


@login_required
def follow_index(request):
    list_of_posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(list_of_posts, POST_NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
