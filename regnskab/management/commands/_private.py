from django.core.management.base import BaseCommand, CommandError


class RegnskabCommand(BaseCommand):
    def progress(self, elements, n=None):
        if n is None:
            elements = list(elements)
            n = len(elements)
        w = len(str(n))
        for i, x in enumerate(elements):
            self.stdout.write('\r\x1B[K(%s/%s) %s' % (str(i+1).rjust(w), n, x), ending='')
            self.stdout.flush()
            yield x
        self.stdout.write('')

    def save_all(self, objects, unique_attrs=None, only_new=False, bulk=False):
        if not objects:
            return []
        existing = []
        new = []
        if unique_attrs:
            unique_attrs = tuple(unique_attrs)

            def key(o):
                return tuple(getattr(o, k) for k in unique_attrs)

            main_model = type(objects[0])
            existing_dict = {key(o): o for o in main_model.objects.all()}
            for o in self.progress(objects):
                try:
                    e = existing_dict[key(o)]
                except KeyError:
                    new.append(o)
                else:
                    existing.append(e)
        else:
            new.extend(objects)

        if new:
            self.stdout.write("Save %s %s objects" %
                              (len(new), type(new[0]).__name__))
            if bulk:
                type(new[0]).objects.bulk_create(new)
            else:
                if type(new[0]).objects.all().exists() or not unique_attrs:
                    for o in self.progress(new):
                        o.save()
                else:
                    # No objects exist in database,
                    # so we might just bulk insert them
                    # and retrieve the pks in bulk.
                    type(new[0]).objects.bulk_create(new)
                    pks = {key(o): o.id for o in type(new[0]).objects.all()}
                    for o in new:
                        o.id = pks[key(o)]
        if only_new:
            return new
        else:
            return new + existing

    def filter_related(self, parent_objects, related_objects, related_field):
        parent_objects = set(parent_objects)
        new = []
        for o in self.progress(related_objects):
            r = getattr(o, related_field)
            if r.pk and r in parent_objects:
                setattr(o, related_field, r)
                new.append(o)
        return new

    def at_least_one(self, options, choices):
        if not any(o in options for o in choices):
            raise CommandError("At least one of %s must be provided" %
                               ', '.join('--%s' % k.replace('_', '-')
                                         for k in choices))
