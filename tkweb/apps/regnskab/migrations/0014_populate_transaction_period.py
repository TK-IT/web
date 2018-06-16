from django.db import migrations, models


def populate_transaction_period(apps, schema_editor):
    Transaction = apps.get_model('regnskab', 'Transaction')
    Sheet = apps.get_model('regnskab', 'Sheet')
    date_to_period = dict(Sheet.objects.all().values_list(
        'end_date', 'period'))
    qs = Transaction.objects.filter(period=0)
    qs = qs.values_list('id', 'time', 'session__period')
    for id, time, session_period in qs:
        time_period = date_to_period.get(time.date())
        print('%r\t%r\t%r' % (id, time_period, session_period))
        if time_period is None and session_period is None:
            raise Exception('No period for id=%s time=%r' %
                            (id, time))
        if time_period is not None and session_period is not None:
            if time_period != session_period:
                raise Exception("Time (%r) disagrees with session (%r)" %
                                (time_period, session_period))
        Transaction.objects.filter(id=id).update(
            period=time_period or session_period)


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0013_transaction_period'),
    ]

    operations = [
        migrations.RunPython(populate_transaction_period),
    ]
