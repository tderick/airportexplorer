from wtforms import Form, StringField,validators

class UserOnboardingForm(Form):
    first_name = StringField('first_name', [validators.Length(min=4, max=100)])
    last_name = StringField('last_name', [validators.Length(min=6, max=100)])
   