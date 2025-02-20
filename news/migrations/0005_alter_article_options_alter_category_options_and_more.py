# Generated by Django 5.1.6 on 2025-02-20 20:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0004_article_is_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'verbose_name': 'Статья', 'verbose_name_plural': 'Статьи'},
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['name'], 'verbose_name': 'Категория', 'verbose_name_plural': 'Категории'},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'verbose_name': 'Тег', 'verbose_name_plural': 'Теги'},
        ),
        migrations.AddField(
            model_name='article',
            name='status',
            field=models.BooleanField(choices=[(False, 'не проверено'), (True, 'проверено')], default=0, verbose_name='Проверено'),
        ),
        migrations.AlterField(
            model_name='article',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='news.category', verbose_name='Категория'),
        ),
        migrations.AlterField(
            model_name='article',
            name='content',
            field=models.TextField(verbose_name='Содержание'),
        ),
        migrations.AlterField(
            model_name='article',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Активна'),
        ),
        migrations.AlterField(
            model_name='article',
            name='publication_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации'),
        ),
        migrations.AlterField(
            model_name='article',
            name='slug',
            field=models.SlugField(blank=True, unique=True, verbose_name='Слаг'),
        ),
        migrations.AlterField(
            model_name='article',
            name='tags',
            field=models.ManyToManyField(related_name='article', to='news.tag', verbose_name='Теги'),
        ),
        migrations.AlterField(
            model_name='article',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Заголовок'),
        ),
        migrations.AlterField(
            model_name='article',
            name='views',
            field=models.IntegerField(default=0, verbose_name='Просмотры'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Категория'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=50, unique=True, verbose_name='Тег'),
        ),
        migrations.AlterModelTable(
            name='article',
            table='Articles',
        ),
        migrations.AlterModelTable(
            name='category',
            table='Categories',
        ),
        migrations.AlterModelTable(
            name='tag',
            table='Tags',
        ),
    ]
