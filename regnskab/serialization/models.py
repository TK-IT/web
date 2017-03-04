from .codegen import base


class TitleData(base('Title')):
    parent_field = 'profile'
    fields = ('root', 'period')
    shape = 'list'

    def load_children(self, parent, child_data):
        children = super().load_children(parent, child_data)
        for title in children:
            if title.root.startswith('FU'):
                title.kind = 'FU'
            elif title.root.startswith('EFU'):
                title.kind = 'EFU'
            else:
                title.kind = 'BEST'
        return children


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
    shape = 'value'
    bulk = True


class PurchaseData(base('Purchase')):
    parent_field = 'row'
    fields = ('kind', 'count')
    shape = 'list'
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
