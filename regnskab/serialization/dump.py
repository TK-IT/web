import os
import sys
import json
import decimal
import datetime
import operator


if __name__ == "__main__":
    from .base import django_setup
    django_setup()


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S%z'
DATE_FORMAT = '%Y-%m-%d'


def field_dumper(field):
    field_name = field.name

    if field.__class__.__name__ == 'DateTimeField':
        def dump_field(self, instance):
            v = getattr(instance, field_name)
            return v and v.strftime(DATETIME_FORMAT)
    elif field.__class__.__name__ == 'DateField':
        def dump_field(self, instance):
            v = getattr(instance, field_name)
            return v and v.strftime(DATE_FORMAT)
    elif field.__class__.__name__ == 'DecimalField':
        def dump_field(self, instance):
            v = getattr(instance, field_name)
            return v if v is None else str(v)
    else:
        if field.__class__.__name__ == 'ForeignKey':
            field_name += '_id'

        def dump_field(self, instance):
            return getattr(instance, field_name)

    return dump_field


def field_loader(field):
    field_name = field.name

    if field.__class__.__name__ == 'DateTimeField':
        def load_field(self, data, instance):
            v = data[field_name]
            setattr(instance, field_name,
                    v and datetime.datetime.strptime(v, DATETIME_FORMAT))
    elif field.__class__.__name__ == 'DateTimeField':
        def load_field(self, data, instance):
            v = data[field_name]
            setattr(instance, field_name,
                    v and datetime.datetime.strptime(v, DATE_FORMAT).date())
    elif field.__class__.__name__ == 'DecimalField':
        def load_field(self, data, instance):
            v = data[field_name]
            setattr(instance, field_name, v and decimal.Decimal(v))
    else:
        if field.__class__.__name__ == 'ForeignKey':
            attr_name = field_name + '_id'
        else:
            attr_name = field_name

        def load_field(self, data, instance):
            setattr(instance, attr_name, data[field_name])

    return load_field


class SetParents:
    def __init__(self, objects, parent_field):
        self.objects = list(objects)
        self.parent_field = parent_field

    def __call__(self):
        for o in self.objects:
            setattr(o, self.parent_field, getattr(o, self.parent_field))

    def __repr__(self):
        return 'SetParents(%r, %r)' % (self.objects, self.parent_field)


class SaveAll:
    def __init__(self, objects):
        self.objects = list(objects)

    def __call__(self):
        for o in self.objects:
            o.save()

    def __repr__(self):
        return 'SaveAll(%r)' % (self.objects,)


class BulkSaveAll:
    def __init__(self, objects):
        self.objects = list(objects)

    def __call__(self):
        if self.objects:
            self.objects[0].__class__.objects.bulk_create(self.objects)

    def __repr__(self):
        return 'SaveAll(%r)' % (self.objects,)


class Data:
    OMIT = object()

    def _fields(self):
        try:
            return self._fields_cache
        except AttributeError:
            pass
        try:
            self._fields_cache = self.fields
            return self._fields_cache
        except AttributeError:
            pass
        try:
            exclude = set(self.exclude)
        except AttributeError:
            exclude = set()
        method_order = []
        dump_methods = set()
        load_methods = set()
        for k in dir(self):
            if k.startswith('dump_'):
                dump_methods.add(k[5:])
                if k[5:] not in exclude:
                    method_order.append(k[5:])
            elif k.startswith('load_'):
                load_methods.add(k[5:])
        diff = (dump_methods - exclude) ^ (load_methods - exclude)
        if diff:
            raise TypeError(diff)
        explicit_fields = getattr(self, 'fields', ())
        self._fields_cache = list(explicit_fields) + method_order
        return self._fields_cache

    def dump(self):
        by_parent = {}
        try:
            parent_field = self.parent_field
        except AttributeError:
            parent_fn = lambda instance: None  # noqa
            result = by_parent[None] = []
        else:
            parent_fn = operator.attrgetter(parent_field + '_id')
            result = by_parent

        children = {}
        for child_name, child_type in getattr(self, 'children', {}).items():
            try:
                child_dump_fn = getattr(self, 'dump_' + child_name)
            except AttributeError:
                child_dump_fn = child_type().dump
            child_dump = child_dump_fn()
            assert isinstance(child_dump, dict)
            for parent, data in child_dump.items():
                if data is not self.OMIT:
                    children.setdefault(parent, {})[child_name] = data

        field_names = self._fields()
        for instance in self.get_queryset():
            instance_data = {}
            for field_name in field_names:
                dump_method = getattr(self, 'dump_' + field_name)
                dumped_value = dump_method(instance)
                if dumped_value is not self.OMIT:
                    instance_data[field_name] = dumped_value
            instance_data.update(children.get(instance.pk, {}))
            by_parent.setdefault(parent_fn(instance), []).append(instance_data)
        return result

    def load_children(self, parent, child_data):
        field_names = self._fields()
        children = []
        for d in child_data:
            instance = self.new_instance()
            for field_name in field_names:
                getattr(self, 'load_' + field_name)(d, instance)
            children.append(instance)
        try:
            for instance in children:
                setattr(instance, self.parent_field, parent)
        except AttributeError:
            pass
        return children

    def load(self, data_lists, parents):
        callbacks = []
        result = []
        parent_field = getattr(self, 'parent_field', None)
        for parent, child_data in zip(parents, data_lists):
            result.extend(self.load_children(parent, child_data))

        if parent_field is not None:
            callbacks.append(SetParents(result, parent_field))
        if getattr(self, 'bulk', False):
            callbacks.append(BulkSaveAll(result))
        else:
            callbacks.append(SaveAll(result))

        for child_name, child_type in getattr(self, 'children', {}).items():
            try:
                child_load_fn = getattr(self, 'load_' + child_name)
            except AttributeError:
                child_load_fn = child_type().load
            data_flat = [d.get(child_name, ())
                         for child_data in data_lists for d in child_data]
            callbacks.extend(child_load_fn(data_flat, result))

        return callbacks


def base(model):
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
