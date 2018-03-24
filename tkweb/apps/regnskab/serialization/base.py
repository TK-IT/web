import os
import sys
import glob
import django
import operator

from .callback import SetParents, SaveAll, BulkSaveAll


def django_setup():
    if os.path.exists('manage.py'):
        BASE_DIR = '.'
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.extend(
        glob.glob(os.path.join(BASE_DIR, 'venv/lib/*/site-packages')))
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        with open(os.path.join(BASE_DIR, 'manage.py')) as fp:
            settings_line = next(l for l in fp
                                 if 'DJANGO_SETTINGS_MODULE' in l)
            eval(settings_line.strip())
    django.setup()


class Data:
    '''
    Base class for Django model (un-)serializers.
    '''

    OMIT = object()
    shape = 'dict'

    def _fields(self):
        return self.fields

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

        for instance in self.get_queryset():
            instance_data = self.get_instance_data(instance, children)
            by_parent.setdefault(parent_fn(instance), []).append(instance_data)
        return result

    def get_instance_data(self, instance, children):
        instance_data = {}
        for field_name in self._fields():
            dump_method = getattr(self, 'dump_' + field_name)
            dumped_value = dump_method(instance)
            if dumped_value is not self.OMIT:
                instance_data[field_name] = dumped_value
        instance_data.update(children.get(instance.pk, {}))
        if self.shape == 'dict':
            return instance_data
        elif self.shape == 'list':
            return [instance_data[n] for n in self._fields()]
        elif self.shape == 'value':
            value, = instance_data.values()
            return value
        else:
            raise ValueError(self.shape)

    def load_children(self, parent, child_data):
        field_names = self._fields()
        children = []
        for d in child_data:
            if self.shape == 'dict':
                pass
            elif self.shape == 'list':
                d = dict(zip(field_names, d))
            elif self.shape == 'value':
                d = dict(zip(field_names, [d]))
            else:
                raise ValueError(self.shape)
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
