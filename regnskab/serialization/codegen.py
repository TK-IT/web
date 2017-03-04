import decimal
import datetime
import operator

from .base import Data


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S%z'
DATE_FORMAT = '%Y-%m-%d'


def remove_exponent(d):
    '''From Python docs decimal FAQ'''
    return (d.quantize(decimal.Decimal(1)) if d == d.to_integral()
            else d.normalize())


def field_dumper(field):
    '''
    Return a method for dumping data for the given Django model field.
    If the model field data is not directly serializable to JSON,
    the returned method converts it to a suitable representation:

    * datetime to str (via DATETIME_FORMAT)
    * date to str (via DATE_FORMAT)
    * Decimal to str
    * ForeignKey to int
    '''

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
            return v if v is None else str(remove_exponent(v))
    else:
        if field.__class__.__name__ == 'ForeignKey':
            field_name += '_id'

        def dump_field(self, instance):
            return getattr(instance, field_name)

    return dump_field


def field_loader(field):
    '''
    Return a method for loading data for the Django model field
    dumped by field_dumper(field). See field_dumper for the conversions.
    '''

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
    members['new_instance'] = lambda self, **kwargs: model(**kwargs)
    return type(model.__name__, (Data,), members)
