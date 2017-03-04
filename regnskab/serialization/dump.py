import sys
import json
import operator

from .base import django_setup, Data
from .codegen import field_dumper, field_loader


if __name__ == "__main__":
    django_setup()


def base(model):
    '''
    Create a subclass of Data with the following model specific methods:

    - get_queryset() (returns model.objects.all())
    - new_instance() (returns model())
    - dump_<field>(instance: model) (returns the field attr of instance)
    - load_<field>(data: dict, instance: model) (sets the field attr)
    '''

    if isinstance(model, str):
        import regnskab.models
        model = operator.attrgetter(model)(regnskab.models)

    members = {}
    for field in model._meta.fields:
        members['dump_' + field.name] = field_dumper(field)
        members['load_' + field.name] = field_loader(field)
    members['get_queryset'] = lambda self: model.objects.all()
    members['new_instance'] = lambda self: model()
    return type(model.__name__, (Data,), members)


class TitleData(base('Title')):
    parent_field = 'profile'
    fields = ('root', 'period', 'kind')


class AliasData(base('Alias')):
    parent_field = 'profile'
    fields = ('root', 'period', 'is_title',
              'start_time', 'end_time',
              'created_time')


class SheetStatusData(base('SheetStatus')):
    parent_field = 'profile'
    fields = ('start_time', 'end_time',
              'created_time')


class ProfileData(base('Profile')):
    fields = ('id', 'name', 'email')
    children = {
        'titles': TitleData,
        'aliases': AliasData,
        'statuses': SheetStatusData,
    }


class EmailData(base('Email')):
    parent_field = 'session'
    fields = ('profile', 'subject', 'body',
              'recipient_name', 'recipient_email')


class EmailTemplateData(base('EmailTemplate')):
    fields = ('id', 'name', 'subject', 'body', 'format', 'created_time')


class PurchaseKindData(base('PurchaseKind')):
    fields = ('id', 'position', 'name', 'unit_price')


class SheetKindRelationData(base('PurchaseKind.sheets.through')):
    parent_field = 'sheet'
    fields = ('purchasekind',)
    bulk = True


class PurchaseData(base('Purchase')):
    parent_field = 'row'
    fields = ('kind', 'count')
    bulk = True


class SheetRowData(base('SheetRow')):
    parent_field = 'sheet'
    fields = ('position', 'name', 'profile')
    exclude = ('image_start', 'image_stop')
    children = {
        'purchases': PurchaseData,
    }


class SheetData(base('Sheet')):
    parent_field = 'session'
    fields = ('name', 'start_date', 'end_date', 'period', 'created_time')
    children = {
        'rows': SheetRowData,
        'kinds': SheetKindRelationData,
    }

    def get_queryset(self):
        return super().get_queryset().exclude(session=None)


class TransactionData(base('Transaction')):
    parent_field = 'session'
    fields = ('kind', 'profile', 'time', 'period', 'amount', 'note',
              'created_time')
    bulk = True

    def get_queryset(self):
        return super().get_queryset().exclude(session=None)


class SessionData(base('Session')):
    fields = ('email_template', 'period', 'send_time', 'created_time')
    children = {
        'emails': EmailData,
        'sheets': SheetData,
        'transactions': TransactionData,
    }


class LegacySheetRowData(base('SheetRow')):
    parent_field = 'sheet'
    fields = ('profile',)
    exclude = ('name', 'position', 'image_start', 'image_stop')
    children = {
        'purchases': PurchaseData,
    }

    def load_children(self, parent, child_data):
        children = super().load_children(parent, child_data)
        for i, c in enumerate(children):
            c.position = i + 1
        return children


class LegacySheetData(base('Sheet')):
    fields = ('name', 'start_date', 'end_date', 'period', 'created_time')
    children = {
        'rows': LegacySheetRowData,
        'kinds': SheetKindRelationData,
    }

    def get_queryset(self):
        return super().get_queryset().filter(session=None)


class LegacyTransactionData(base('Transaction')):
    fields = ('kind', 'profile', 'time', 'period', 'amount', 'note',
              'created_time')
    bulk = True

    def get_queryset(self):
        return super().get_queryset().filter(session=None)


class RegnskabData:
    # EmailTemplateData, PurchaseKindData and ProfileData must come before
    # SessionData, LegacySheetData and LegacyTransactionData, since the
    # sessions, sheets and transactions refer by pk to EmailTemplate,
    # PurchaseKind and Profile objects. When loading, the objects referred to
    # by pk must exist, or InnoDB throws an error.
    attributes = [
        ('templates', EmailTemplateData),
        ('kinds', PurchaseKindData),
        ('profiles', ProfileData),
        ('sessions', SessionData),
        ('old_sheets', LegacySheetData),
        ('old_transactions', LegacyTransactionData),
    ]

    def dump(self):
        return {k: v().dump() for k, v in self.attributes}

    def load(self, data):
        callbacks = []
        for k, v in self.attributes:
            callbacks.extend(v().load([data[k]], [None]))
        return callbacks


def debug_json_dump(data, path='data'):
    '''
    In case json.dump raises a TypeError, this function will track down the
    paths to the unserializable objects.
    '''
    if isinstance(data, list):
        for i, o in enumerate(data):
            debug_json_dump(o, path='%s[%s]' % (path, i))
    elif isinstance(data, dict):
        for k, o in data.items():
            debug_json_dump(o, path='%s[%r]' % (path, k))
    else:
        try:
            json.dumps(data)
        except TypeError as exn:
            print('%s: %r' % (path, exn), file=sys.stderr)


def main():
    data = RegnskabData().dump()
    try:
        json.dump(data, sys.stdout, indent=2)
    except TypeError:
        debug_json_dump(data)
        raise


if __name__ == '__main__':
    main()
