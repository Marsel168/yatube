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
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
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
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'form': form,
            
        }
    )


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    form = CommentForm(request.POST or None)
    if form.is_valid():
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
    if not request.method == 'POST' or not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


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
    if not request.method == 'POST' or  not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {
                'form': form,
                'is_edit': True,
                'post': post
            }
        )
    post.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    """
    Посты авторов, на которых подписан текущий пользователь.
    """
    post_list = Post.objects.filter(
        author__following__user=request.user
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
    follow_qs = Follow.objects.filter(
        user=request.user,
        author=author
    )
    if request.user != author and follow_qs.exists():
        follow_qs.delete()
    return redirect('posts:profile', username)
