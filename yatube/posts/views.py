from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import CommentForm, PostForm
from .utils import get_page_obj


def index(request):
    """Главная страница."""
    post_list = Post.objects.select_related('group', 'author').all()
    page_obj = get_page_obj(request, post_list)
    return render(
        request,
        'posts/index.html',
        {'page_obj': page_obj}
    )


def group_posts(request, slug):
    """Посты отфильтрованные по группам."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group', 'author').all()
    page_obj = get_page_obj(request, post_list)
    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': page_obj}
    )


def profile(request, username):
    """Профиль пользовталеля."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group', 'author').all()
    page_obj = get_page_obj(request, post_list)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(
                user=request.user,
                author=author
        ).exists():
            following = True
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': page_obj,
            'following': following
        }
    )


def post_detail(request, post_id):
    """Страница поста."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = reversed(post.comments.all())
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'form': form,
            'comments': comments
        }
    )


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    form = CommentForm(request.POST or None)
    if form.is_valid():
        print('kk')
        post = get_object_or_404(Post, pk=post_id)
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    """
    Создание нового поста.
    После успешного заполнения переход на страницу пользователя.
    """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """
    Редактирование поста.
    Доступно только автору поста.
    После успешного заполнения переход на страницу поста.
    """
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        if form.is_valid():
            post.save()
            return redirect('posts:post_detail', post_id)

    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
            'is_edit': True,
            'post': post
        }
    )


@login_required
def follow_index(request):
    """
    Посты авторов, на которых подписан текущий пользователь.
    """
    user = get_object_or_404(User, username=request.user)
    post_list = Post.objects.filter(
        author__following__user=user
    ).select_related('author', 'group')
    page_obj = get_page_obj(request, post_list)
    return render(
        request,
        'posts/follow.html',
        {'page_obj': page_obj}
    )


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author and (not Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()):
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author and (Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()):
        Follow.objects.get(
            user=request.user,
            author=author
        ).delete()
    return redirect('posts:profile', username)
