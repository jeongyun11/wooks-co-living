# Generated by Django 3.2.18 on 2023-06-08 02:59

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('communities', '0007_alter_post_views'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='scrape_users',
            field=models.ManyToManyField(related_name='scrape_communities_posts', to=settings.AUTH_USER_MODEL),
        ),
    ]
