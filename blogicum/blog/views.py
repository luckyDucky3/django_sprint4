from datetime import datetime 

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    DetailView, CreateView, ListView, UpdateView, DeleteView
)

from .models import Category, Comment, Post, User
from .forms import CommentForm, PostForm, UserForm

# Параметры для пагинации страниц
PAGINATOR_POST = 10
PAGINATOR_CATEGORY = 10
PAGINATOR_PROFILE = 10

# Фильтрация публикаций: только опубликованные, с категориями, которые тоже опубликованы
def filtered_post(posts, is_count_comments=True):
    posts_query = posts.filter(
        pub_date__lte=datetime.today(),
        is_published=True,             
        category__is_published=True
    ).order_by(
        '-pub_date'  # Сортировка по дате публикации (новые сверху)
    )
    # Аннотация количества комментариев (если включена)
    return posts_query.annotate(
        comment_count=Count('comments')
    ).order_by("-pub_date") if is_count_comments else posts_query


# Представление для отображения списка публикаций
class PostListView(ListView):
    paginate_by = PAGINATOR_POST
    template_name = 'blog/index.html'

    def get_queryset(self):
        return filtered_post(Post.objects.all())


# Представление для детального отображения поста
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        # Добавление формы комментария и списка комментариев в контекст
        return dict(
            **super().get_context_data(**kwargs),
            form=CommentForm(),
            comments=self.object.comments.select_related('author')
        )

    def get_object(self):
        # Получение объекта поста, если пользователь авторизован - показываем и свои неопубликованные посты
        posts = Post.objects
        return get_object_or_404(
            posts.filter(
                is_published=True
            ) or posts.filter(
                author=self.request.user
            )
            if self.request.user and self.request.user.is_authenticated
            else filtered_post(Post.objects, is_count_comments=False),
            pk=self.kwargs["post_id"],
        )


# Представление для отображения постов определенной категории
class PostCategoryView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = PAGINATOR_CATEGORY  # Количество постов на страницу

    def get_queryset(self):
        # Получение категории по slug и фильтрация постов
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return filtered_post(self.category.posts.all())

    def get_context_data(self, **kwargs):
        # Добавление категории в контекст
        return dict(
            **super().get_context_data(**kwargs),
            category=self.category
        )


# Представление для создания нового поста
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        # Автоматическое назначение автором текущего пользователя
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # Переадресация на профиль пользователя после успешного создания поста
        return reverse(
            'blog:profile', args=[self.request.user.username]
        )


# Миксин для обновления и удаления поста (проверка на авторство)
class PostMixin(LoginRequiredMixin):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        # Проверка, является ли пользователь автором поста
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post.author != self.request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


# Представление для обновления поста
class PostUpdateView(PostMixin, UpdateView):
    def get_success_url(self):
        # Переадресация на детальный просмотр поста
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])


# Представление для удаления поста
class PostDeleteView(PostMixin, DeleteView):
    def get_success_url(self):
        # Переадресация на профиль пользователя после удаления
        return reverse('blog:profile', args=[self.request.user.username])


# Представление для редактирования профиля пользователя
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        # Редактирование только текущего пользователя
        return self.request.user

    def get_success_url(self):
        # Переадресация на профиль пользователя после успешного редактирования
        return reverse('blog:profile', args=[self.request.user.username])


# Представление для отображения профиля пользователя
class ProfileListView(ListView):
    paginate_by = PAGINATOR_PROFILE  # Количество постов на страницу
    template_name = 'blog/profile.html'
    model = Post

    def get_object(self):
        # Получение пользователя по имени
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        # Получение всех постов пользователя
        return self.get_object().posts.all()

    def get_context_data(self, **kwargs):
        # Добавление профиля в контекст
        return dict(
            **super().get_context_data(**kwargs),
            profile=self.get_object()
        )

class CommentCreateView(LoginRequiredMixin, CreateView):
    # Представление для создания нового комментария
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm 

    def get_context_data(self, **kwargs):
        # Добавляем форму в контекст для передачи в шаблон
        return dict(**super().get_context_data(**kwargs), form=CommentForm())

    def form_valid(self, form):
        # Настраиваем форму перед сохранением
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form) 

    def get_success_url(self):
        # Перенаправление после успешного создания комментария
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])


class CommentMixin(LoginRequiredMixin):
    # Миксин для редактирования и удаления комментария

    model = Comment  # Указываем модель комментария
    template_name = 'blog/comment.html'  # Шаблон для отображения
    pk_url_kwarg = 'comment_id'  # Имя ключа для идентификации комментария

    def get_success_url(self):
        # Перенаправление после успешного выполнения действия
        return reverse('blog:post_detail', args=[self.kwargs['comment_id']])

    def dispatch(self, request, *args, **kwargs):
        # Проверка прав доступа (текущий пользователь должен быть автором комментария)
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        if comment.author != self.request.user:
            return redirect(
                'blog:post_detail',
                post_id=comment.post.id
            )
        return super().dispatch(request, *args, **kwargs)


class CommentUpdateView(CommentMixin, UpdateView):
    # Представление для редактирования комментария
    form_class = CommentForm 


class CommentDeleteView(CommentMixin, DeleteView):
    #Представление для удаления комментария
    ...
