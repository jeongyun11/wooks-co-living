# Generated by Django 3.2.18 on 2023-06-02 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0003_alter_post_views'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='category',
            field=models.CharField(blank=True, max_length=40),
        ),
    ]
