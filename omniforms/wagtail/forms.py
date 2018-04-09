from django import forms

from omniforms.models import OmniForm


class WagtailOmniFormCloneForm(forms.ModelForm):
    """
    Form class for cloning an OmniForm
    """
    class Meta(object):
        """
        Django form meta
        """
        fields = ('title',)
        model = OmniForm

    def __init__(self, *args, **kwargs):
        """
        Ensures that the forms title field is not pre-filled

        :param args: Default positional args
        :param kwargs: Default keyword args
        """
        super(WagtailOmniFormCloneForm, self).__init__(*args, **kwargs)
        self.initial['title'] = None

    def save(self, commit=True):
        """
        Create a new form instance using the submitted title
        before cloning all fields associated with the source form
        and attaching them to the newly created OmniForm instance

        :param commit: Whether or not to commit the changes to the DB
        :return: Cloned form instance
        """
        instance = OmniForm.objects.create(title=self.cleaned_data['title'])

        # Clone the fields attached to the form
        for base_field in self.instance.fields.all():
            field = base_field.specific
            field.id = None
            field.omnifield_ptr = None
            field.form = instance
            field.save()

        # Clone the handlers attached to the form
        for base_handler in self.instance.handlers.all():
            handler = base_handler.specific
            handler.id = None
            handler.omniformhandler_ptr = None
            handler.form = instance
            handler.save()

        return instance
