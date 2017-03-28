import os
import time
import traceback

import django
from django.test import Client
from django.core.urlresolvers import reverse


def get_sent_session():
    from regnskab.models import Session
    qs = Session.objects.exclude(sheet=None).exclude(send_time=None)
    qs = qs.order_by('-id')
    return qs[0]


def get_fresh_session():
    from regnskab.models import Session
    qs = Session.objects.filter(send_time=None).order_by('-id')
    if qs:
        return qs[0]
    return Session.objects.create()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "regnskabsite.settings")
    django.setup()
    from regnskab.models import Profile, EmailTemplate
    c = Client()

    def assert_get(name, data=None, code=200, **kwargs):
        if name.startswith('/'):
            url = name
        else:
            url = reverse('regnskab:%s' % name, kwargs=kwargs)
        print('%-29s ' % url, end='', flush=True)
        t1 = time.time()
        try:
            if data:
                response = c.post(url, data)
            else:
                response = c.get(url)
        except Exception as exn:
            print('%.2f ' % (time.time() - t1), end='', flush=True)
            print('%s: %s' % (exn.__class__.__name__, exn), flush=True)
            traceback.print_exc()
        else:
            print('%.2f ' % (time.time() - t1), end='', flush=True)
            if response.status_code != code:
                print('Wrong response code: Got %s, expected %s' %
                      (response.status_code, code), flush=True)
            else:
                print('OK (%s)' % code, flush=True)

    assert_get('/admin/login/', dict(username='rav', password='hej'), code=302)

    sent_session = get_sent_session()
    sent_sheet = sent_session.sheet_set.all()[0]
    email_template = EmailTemplate.objects.all()[0]
    fresh_session = get_fresh_session()
    fresh_sheet = fresh_session.sheet_set.all()[0]
    profile = Profile.objects.exclude(sheetrow=None)[0]

    assert_get('home')
    assert_get('log')
    assert_get('sheet_create', session=fresh_session.pk)
    assert_get('sheet_detail', pk=sent_sheet.pk)
    assert_get('sheet_update', pk=fresh_sheet.pk)
    assert_get('email_template_list')
    assert_get('email_template_update', pk=email_template.pk)
    assert_get('email_template_create')
    assert_get('session_list')
    assert_get('session_create')
    assert_get('session_update', pk=sent_session.pk)
    assert_get('session_update', pk=fresh_session.pk)
    assert_get('email_list', pk=sent_session.pk)
    assert_get('email_list', pk=fresh_session.pk)
    assert_get('purchase_note_list', pk=fresh_session.pk)
    assert_get('profile_detail', pk=profile.pk)
    assert_get('payment_batch_create', pk=fresh_session.pk)
    assert_get('payment_purchase_list', pk=sent_session.pk)
    assert_get('profile_list')
    assert_get('balance_print', dict(mode='source'), pk=fresh_session.pk)
    assert_get('balance_print', dict(mode='pdf'), pk=sent_session.pk)



if __name__ == '__main__':
    main()
