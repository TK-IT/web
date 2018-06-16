from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0021_remove_group_relativ'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gradgroupmembership',
            name='group',
        ),
        migrations.RemoveField(
            model_name='gradgroupmembership',
            name='profile',
        ),
        migrations.DeleteModel(
            name='GradGroupMembership',
        ),
    ]
