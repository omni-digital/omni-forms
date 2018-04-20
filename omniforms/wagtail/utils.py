from wagtail.wagtailcore import hooks


def run_permission_hooks(action, instance):
    """
    Simple method that runs permission hooks for the given instance
    Loops through all 'omniform_permission_check' hooks and calls each
    in turn passing:

     - action: The action being performed (create, update, delete, clone)
     - instance: The instance being operated on

    :param action: The action being performed
    :param instance: The model instance being worked on
    """
    for hook in hooks.get_hooks('omniform_permission_check'):
        hook(action, instance)
