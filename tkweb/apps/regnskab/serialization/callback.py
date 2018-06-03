class DataLoadCallback:
    """
    Base class of callbacks returned by Data.load().

    The 'objects' attribute is a homogenous list of Django model instances.
    The callback either modifies the instances somehow, or saves them to
    the database.
    """

    def __repr__(self):
        if self.objects:
            return "<%s on %d\N{MULTIPLICATION SIGN} %s>" % (
                self.__class__.__name__,
                len(self.objects),
                self.objects[0].__class__.__name__,
            )
        else:
            return "<%s on 0 objects>" % self.__class__.__name__


class SetParents(DataLoadCallback):
    """
    Update the PARENT_id attribute on the child objects.
    When the PARENT attribute is set to a Django model instance
    without a pk, the PARENT_id is set to None.
    After saving the parent object, we must update the PARENT attribute
    in order to refresh the PARENT_id attribute.
    """

    def __init__(self, objects, parent_field):
        self.objects = list(objects)
        self.parent_field = parent_field

    def __call__(self):
        for o in self.objects:
            setattr(o, self.parent_field, getattr(o, self.parent_field))


class SaveAll(DataLoadCallback):
    """
    Save the list of objects to the database, retrieving their pks.
    """

    def __init__(self, objects):
        self.objects = list(objects)

    def __call__(self):
        for o in self.objects:
            o.save()


class BulkSaveAll(DataLoadCallback):
    """
    Save the list of objects to the database with bulk_create
    (in case no other objects need the pks).
    Used when the 'bulk' attribute on the Data subclass is True.
    """

    def __init__(self, objects):
        self.objects = list(objects)

    def __call__(self):
        if self.objects:
            self.objects[0].__class__.objects.bulk_create(self.objects)
