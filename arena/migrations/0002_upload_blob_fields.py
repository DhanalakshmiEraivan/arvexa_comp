from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arena", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
        
            model_name="upload",
            name="blob_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="upload",
            name="blob_path",
            field=models.CharField(max_length=1000, blank=True),
        ),
        migrations.AddField(
            model_name="upload",
            name="original_name",
            field=models.CharField(max_length=500, blank=True),
        ),
        migrations.AddField(
            model_name="upload",
            name="content_type",
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name="upload",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="submissions/%Y/%m/",
            ),
        ),
    ]
