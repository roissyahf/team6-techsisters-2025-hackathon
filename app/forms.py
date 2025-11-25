from flask_security.forms import RegisterForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Optional, ValidationError

def validate_country(form, field):
    """Validate that a country is selected (not the default 0)."""
    if field.data == 0 or field.data is None:
        raise ValidationError('Please select a country.')

class ExtendedRegisterForm(RegisterForm):
    """Extended registration form with firstname, lastname, and country."""
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    country_id = SelectField('Country', coerce=int, validators=[DataRequired(), validate_country], choices=[], default=0)
    
    def __init__(self, *args, **kwargs):
        super(ExtendedRegisterForm, self).__init__(*args, **kwargs)
        # Populate country choices dynamically
        self._populate_country_choices()
    
    def _populate_country_choices(self):
        """Populate country dropdown choices from database."""
        try:
            from .models import Country
            countries = Country.query.order_by(Country.name.asc()).all()
            if countries:
                self.country_id.choices = [(0, '-- Select Country --')] + [(c.id, c.name) for c in countries]
            else:
                # No countries in database yet
                self.country_id.choices = [(0, '-- Select Country --')]
        except Exception as e:
            # Fallback if countries can't be loaded (e.g., database not ready)
            import logging
            logging.warning(f"Could not load countries for registration form: {e}")
            self.country_id.choices = [(0, '-- Select Country --')]

