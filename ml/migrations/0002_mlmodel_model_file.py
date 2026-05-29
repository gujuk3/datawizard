from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ml', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mlmodel',
            name='model_file',
            field=models.FileField(blank=True, null=True, upload_to='ml_models/'),
        ),
    ]
