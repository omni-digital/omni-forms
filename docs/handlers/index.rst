Bundled Handlers
================

Omniforms currently ships with 3 form handlers for use in your application.

Send Static Email
-----------------

This form handler allows administrators to send an email to a set of predefined email addresses on successful form submission. In addition to the standard fields that every handler has, this handler allows the administrator to specify the following fields:

 - ``subject``: The subject for outgoing emails
 - ``recipients``: A list of email addresses the email will be sent to (one address per line)
 - ``template``: The email template. This template string will be rendered using djangos template rendering library. The forms cleaned data will be made available to the template rendering context meaning it is possible to render submitted form data in the template.

It is also worth noting that any files uploaded via the form will be attached to the outbound emails.

Send Email Confirmation
-----------------------

This form handler works in an almost identical way to the ``Send Static Email`` handler. However, rather than allowing a static list of recipients to be defined, the handler allows the administrator to select an ``OmniEmailField`` instance from the associated form that holds the recipient email address.

For example, a job application form may hold a field for the applicant to enter their email address.  This handler would allow you to select that field and send a confirmation email to the applicant on form submission.

Save Data
---------

This form handler is designed to emulate a model forms ``save`` method and allows submitted form data to be persisted to the database if valid.

This handler may only be attached to forms that:

 - Are ``OmniModelForm`` instances;
 - Have all of the models ``required`` fields configured correctly
