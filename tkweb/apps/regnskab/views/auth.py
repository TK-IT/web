from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

regnskab_permission_required = permission_required('regnskab.add_sheetrow')
regnskab_permission_required_method = method_decorator(
    regnskab_permission_required)
