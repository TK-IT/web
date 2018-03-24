from django.conf import settings


if settings.USE_MEDIUM_EDITOR:
    from mediumeditor.widgets import MediumEditorTextarea as RichTextarea
else:
    from django.forms import Textarea as RichTextarea
