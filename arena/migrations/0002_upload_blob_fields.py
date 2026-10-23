from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arena", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="upload",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="submissions/%Y/%m/",
            ),
        ),
        migrations.AddField(
            model_name="upload",
            name="blob_path",
            field=models.CharField(
                blank=True,
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name="upload",
            name="blob_url",
            field=models.URLField(
                blank=True,
                max_length=2000,
            ),
        ),
        migrations.AddField(
            model_name="upload",
            name="original_name",
            field=models.CharField(
                blank=True,
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="upload",
            name="content_type",
            field=models.CharField(
                blank=True,
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="upload",
            name="file_size",
            field=models.BigIntegerField(
                default=0,
            ),
        ),
    ]
    
