from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import get_page


def index(request):
    """Функция index передает данные в шаблон index.html."""
    template = 'posts/index.html'
    post_list = Post.objects.select_related(
        'author',
        'group'
    )
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
    )
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
    following = False
    # Здесь код запроса к модели и создание словаря контекста
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    """Здесь код запроса к модели и создание словаря контекста."""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    # В тело страницы выведен один пост, выбранный по pk
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, template, context)


@login_required
def post_create(request):
    """Добавлена "Новая запись" для авторизованных пользователей."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user)
    context = {
        'form': form,
        'is_edit': False,
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
    page_obj = get_page(request, list_of_posts)
    context = {'page_obj': page_obj}

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    follower.delete()

    return redirect('posts:profile', username=author)
