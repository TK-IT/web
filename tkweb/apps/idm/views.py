from constance import config
from django.contrib.auth.decorators import permission_required
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from tkweb.apps.idm.forms import GfyearBestForm
from tkweb.apps.idm.models import Title, Profile


class GfyearBestUpdate(FormView):
    form_class = GfyearBestForm
    template_name = 'idm/gfyear_best_update.html'

    # TODO: Use a proper permission. Currently, only superusers are allowed.
    @method_decorator(permission_required('gfyear_best_update', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        eight = 'FORM CERM INKA KASS NF PR SEKR VC'.split()
        kwargs['profiles'] = Profile.objects.all().order_by('name')
        kwargs['roots'] = eight
        return kwargs

    def get_initial(self):
        period = timezone.now().year
        best = Title.objects.filter(kind=Title.BEST, period=period)
        initial = {'period': period}
        for title in best:
            initial[title.root] = title.profile_id
        return initial

    def form_valid(self, form):
        period = form.cleaned_data['period']
        config.GFYEAR = period
        Title.objects.filter(kind=Title.BEST, period=period).delete()
        for root in form.roots:
            profile_id = form.cleaned_data[root]
            if profile_id:
                profile = form.profiles[int(profile_id)]
                Title.objects.create(
                    kind=Title.BEST, period=period, root=root, profile=profile
                )
        return self.render_to_response(self.get_context_data(form=form, success=True))
