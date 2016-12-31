class RegnskabSite(object):
    name = 'regnskab'

    def get_urls(self):
        from django.conf.urls import url
        from regnskab import views
        from regnskab.views import images

        return [
            url(r'^$', views.Home.as_view(), name='home'),
            url(r'^log/$', views.Log.as_view(), name='log'),
            url(r'^session/(?P<session>\d+)/sheet/new/$',
                views.SheetCreate.as_view(), name='sheet_create'),
            url(r'^sheet/(?P<pk>\d+)/$', views.SheetDetail.as_view(),
                name='sheet_detail'),
            url(r'^sheet/(?P<pk>\d+)/edit/$', views.SheetRowUpdate.as_view(),
                name='sheet_update'),
            url(r'^template/$', views.EmailTemplateList.as_view(),
                name='email_template_list'),
            url(r'^template/(?P<pk>\d+)/$',
                views.EmailTemplateUpdate.as_view(),
                name='email_template_update'),
            url(r'^template/new/$', views.EmailTemplateCreate.as_view(),
                name='email_template_create'),
            url(r'^session/$', views.SessionList.as_view(),
                name='session_list'),
            url(r'^session/new/$', views.SessionCreate.as_view(),
                name='session_create'),
            url(r'^session/(?P<pk>\d+)/$', views.SessionUpdate.as_view(),
                name='session_update'),
            url(r'^session/(?P<pk>\d+)/email/$', views.EmailList.as_view(),
                name='email_list'),
            url(r'^session/(?P<pk>\d+)/email/send/$',
                views.EmailSend.as_view(), name='email_send'),
            url(r'^session/(?P<pk>\d+)/email/(?P<profile>\d+)/$',
                views.EmailDetail.as_view(), name='email_detail'),
            url(r'^session/(?P<pk>\d+)/email/(?P<profile>\d+)/send/$',
                views.EmailSend.as_view(), name='email_send'),
            url(r'^session/(?P<pk>\d+)/payment/$',
                views.PaymentBatchCreate.as_view(),
                name='payment_batch_create'),
            url(r'^session/(?P<pk>\d+)/other/$',
                views.PurchaseNoteList.as_view(), name='purchase_note_list'),
            url(r'^session/(?P<pk>\d+)/other/add/$',
                views.PurchaseBatchCreate.as_view(),
                name='purchase_batch_create'),
            url(r'^session/(?P<pk>\d+)/purchases/$',
                views.PaymentPurchaseList.as_view(),
                name='payment_purchase_list'),
            url(r'^session/(?P<pk>\d+)/print/$', views.BalancePrint.as_view(),
                name='balance_print'),
            url(r'^profile/$', views.ProfileList.as_view(),
                name='profile_list'),
            url(r'^profile/(?P<pk>\d+)/$', views.ProfileDetail.as_view(),
                name='profile_detail'),
            url(r'^profile/search/$', views.ProfileSearch.as_view(),
                name='profile_search'),
            # url(r'^images/sheet/(?P<pk>\d+)\.png$',
            #     images.SheetImageFile.as_view(),
            #     name='sheet_image_file'),
            # url(r'^images/sheet/(?P<pk>\d+)/$',
            #     images.SheetImageUpdate.as_view(),
            #     name='sheet_image_update'),
            url(r'^images/$', images.Svm.as_view()),
        ]

    @property
    def urls(self):
        return self.get_urls(), 'regnskab', self.name


site = RegnskabSite()
