class RegnskabSite(object):
    name = "regnskab"

    def get_urls(self):
        from django.conf import settings
        from django.conf.urls import url, include
        from tkweb.apps.regnskab import views
        from tkweb.apps.regnskab.views import images, email
        from tkweb.apps import krydsliste

        urls = [
            url(r"^$", views.Home.as_view(), name="home"),
            url(r"^log/$", views.Log.as_view(), name="log"),
            url(
                r"^session/(?P<session>\d+)/sheet/new/$",
                views.SheetCreate.as_view(),
                name="sheet_create",
            ),
            url(
                r"^sheet/(?P<pk>\d+)/$",
                views.SheetDetail.as_view(),
                name="sheet_detail",
            ),
            url(
                r"^sheet/(?P<pk>\d+)/edit/$",
                views.SheetRowUpdate.as_view(),
                name="sheet_update",
            ),
            url(
                r"^template/$",
                views.EmailTemplateList.as_view(),
                name="email_template_list",
            ),
            url(
                r"^template/(?P<pk>\d+)/$",
                views.EmailTemplateUpdate.as_view(),
                name="email_template_update",
            ),
            url(
                r"^template/new/$",
                views.EmailTemplateCreate.as_view(),
                name="email_template_create",
            ),
            url(r"^session/$", views.SessionList.as_view(), name="session_list"),
            url(
                r"^session/new/$", views.SessionCreate.as_view(), name="session_create"
            ),
            url(
                r"^session/(?P<pk>\d+)/$",
                views.SessionUpdate.as_view(),
                name="session_update",
            ),
            url(
                r"^session/(?P<pk>\d+)/email/$",
                views.EmailList.as_view(),
                name="email_list",
            ),
            url(
                r"^session/(?P<pk>\d+)/email/send/$",
                views.EmailSend.as_view(),
                name="email_send",
            ),
            url(
                r"^session/(?P<pk>\d+)/email/(?P<profile>\d+)/$",
                views.EmailDetail.as_view(),
                name="email_detail",
            ),
            url(
                r"^session/(?P<pk>\d+)/email/(?P<profile>\d+)/send/$",
                views.EmailSend.as_view(),
                name="email_send",
            ),
            url(
                r"^session/(?P<pk>\d+)/payment/$",
                views.PaymentBatchCreate.as_view(),
                name="payment_batch_create",
            ),
            url(
                r"^session/(?P<pk>\d+)/other/$",
                views.PurchaseNoteList.as_view(),
                name="purchase_note_list",
            ),
            url(
                r"^session/(?P<pk>\d+)/other/add/$",
                views.PurchaseBatchCreate.as_view(),
                name="purchase_batch_create",
            ),
            url(
                r"^session/(?P<pk>\d+)/purchases/$",
                views.PaymentPurchaseList.as_view(),
                name="payment_purchase_list",
            ),
            url(
                r"^session/(?P<pk>\d+)/print/$",
                views.BalancePrint.as_view(),
                name="balance_print",
            ),
            url(r"^profile/$", views.ProfileList.as_view(), name="profile_list"),
            url(
                r"^profile/(?P<pk>\d+)/$",
                views.ProfileDetail.as_view(),
                name="profile_detail",
            ),
            url(
                r"^profile/search/$",
                views.ProfileSearch.as_view(),
                name="profile_search",
            ),
            url(
                r"^sheet/(?P<pk>\d+)/(?P<page>\d+)/orig\.png$",
                images.SheetImageFile.as_view(),
                name="sheet_image_file",
            ),
            url(
                r"^sheet/(?P<pk>\d+)/(?P<page>\d+)/proj\.png$",
                images.SheetImageFile.as_view(),
                name="sheet_image_file_projected",
                kwargs={"projected": True},
            ),
            url(
                r"^sheet/(?P<pk>\d+)/(?P<page>\d+)/parameters/$",
                images.SheetImageParameters.as_view(),
                name="sheet_image_parameters",
            ),
            url(
                r"^sheet/(?P<pk>\d+)/(?P<page>\d+)/crosses/$",
                images.SheetImageCrosses.as_view(),
                name="sheet_image_crosses",
            ),
            url(r"^images/$", images.SheetImageList.as_view(), name="sheet_image_list"),
            url(r"^news/$", email.NewsletterList.as_view(), name="newsletter_list"),
            url(
                r"^news/create/$",
                email.NewsletterCreate.as_view(),
                name="newsletter_create",
            ),
            url(
                r"^news/(?P<pk>\d+)/$",
                email.NewsletterUpdate.as_view(),
                name="newsletter_update",
            ),
            url(
                r"^news/(?P<pk>\d+)/email/$",
                email.NewsletterEmailList.as_view(),
                name="newsletter_email_list",
            ),
            url(
                r"^news/(?P<pk>\d+)/email/(?P<profile>\d+)/$",
                email.NewsletterEmailDetail.as_view(),
                name="newsletter_email_detail",
            ),
            url(
                r"^news/(?P<pk>\d+)/send/$",
                email.NewsletterEmailSend.as_view(),
                name="newsletter_email_send",
            ),
            url(
                r"^news/(?P<pk>\d+)/email/(?P<profile>\d+)/send/$",
                email.NewsletterEmailSend.as_view(),
                name="newsletter_email_send",
            ),
            url(r"^krydsliste/", include(krydsliste.site.urls)),
        ]
        if settings.DEBUG:
            urls += [
                url(r"^svm/$", images.Svm.as_view()),
                url(r"^naive/$", images.NaiveParam.as_view()),
            ]
        return urls

    @property
    def urls(self):
        return self.get_urls(), "regnskab", self.name


site = RegnskabSite()
