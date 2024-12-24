# Generated by Django 3.2.16 on 2023-08-07 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_alter_comments_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='post_images', verbose_name='Изображение'),
        ),
        migrations.AlterField(
            model_name='comments',
            name='text',
            field=models.TextField(verbose_name='Текст Коментария'),
        ),
    ]
