# определение моделей Django с возможностью публикации постов, комментариев и их категоризации.

from django.contrib.auth import get_user_model
from django.db import models

# Получаем текущую модель пользователя из настроек проекта
User = get_user_model()


# Абстрактная модель для добавления полей "Опубликовано" и "Дата создания"
class PublishedCreated(models.Model):
    is_published = models.BooleanField(
        default=True, verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'  # Подсказка для админки
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено'  # Автоматически добавляется при создании
    )

    class Meta:
        abstract = True  # Указывает, что это абстрактная модель


# Модель "Категория", наследует поля из PublishedCreated
class Category(PublishedCreated):
    title = models.CharField(max_length=256, verbose_name='Заголовок')  # Название категории
    description = models.TextField(verbose_name='Описание')  # Описание категории
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=('Идентификатор страницы для URL; разрешены '
                   'символы латиницы, цифры, дефис и подчёркивание.')  # Подсказка для админки
    )

    class Meta:
        verbose_name = 'категория'  # Отображаемое имя в админке
        verbose_name_plural = 'Категории'  # Множественное число для админки

    def __str__(self):
        # Возвращает строковое представление объекта
        return (
            f'{self.title[:30]} - {self.description[:30]} - {self.slug}'
        )


# Модель "Местоположение", наследует поля из PublishedCreated
class Location(PublishedCreated):
    name = models.CharField(
        max_length=256, verbose_name='Название места', default='Планета Земля'  # Поле с названием места
    )

    class Meta:
        verbose_name = 'местоположение'  # Отображаемое имя в админке
        verbose_name_plural = 'Местоположения'  # Множественное число для админки

    def __str__(self):
        # Возвращает строковое представление объекта
        return self.name[:30]


# Модель "Публикация", наследует поля из PublishedCreated
class Post(PublishedCreated):
    title = models.CharField(max_length=256, verbose_name='Название')  # Название публикации
    text = models.TextField(verbose_name='Текст')  # Содержимое публикации
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'  # Подсказка для админки
        )
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор публикации',
        related_name='posts'  # Связь с пользователем (автор)
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL,
        null=True, verbose_name='Местоположение',
        related_name='posts'  # Связь с местоположением
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, verbose_name='Категория',
        related_name='posts'  # Связь с категорией
    )
    image = models.ImageField(
        'Изображение', upload_to='post_images', blank=True  # Поле для загрузки изображения
    )

    class Meta:
        verbose_name = 'публикация'  # Отображаемое имя в админке
        verbose_name_plural = 'Публикации'  # Множественное число для админки
        ordering = ('-pub_date',)  # Сортировка по убыванию даты публикации

    def __str__(self):
        # Возвращает строковое представление объекта
        return (
            f'{(self.author.get_username())[:30]} - {self.title[:30]} '
            f'{self.text[:50]} - {self.pub_date} '
            f'{self.location.name[:30]} - {self.category.title[:30]}'
        )


# Модель "Комментарий"
class Comment(models.Model):
    text = models.TextField('Текст')  # Содержимое комментария
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено'  # Автоматически добавляется при создании
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='comments'  # Связь с пользователем (автор)
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        verbose_name='Публикация',
        related_name='comments'  # Связь с публикацией
    )

    class Meta:
        verbose_name = 'коментарий'  # Отображаемое имя в админке
        verbose_name_plural = 'коментарии'  # Множественное число для админки
        ordering = ('created_at',)  # Сортировка по дате создания (по возрастанию)
