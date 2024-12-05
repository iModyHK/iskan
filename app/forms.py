from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length
from .models import Property  # Use relative import

class PropertyForm(FlaskForm):
    cluster = StringField('الحي', validators=[DataRequired()])
    villa = StringField('الوحدة', validators=[DataRequired()])
    status = StringField('الحالة', validators=[DataRequired()])
    floors = SelectField('نوع الفلة', choices=[
        ('دورين', 'دورين'),
        ('ثلاثة أدوار', 'ثلاثة أدوار')
    ], validators=[DataRequired()])
    type = SelectField('مخصصة', choices=[
        ('ضباط', 'ضباط'),
        ('أفراد', 'أفراد')
    ], validators=[DataRequired()])
    submit = SubmitField('إرسال')

class TenantForm(FlaskForm):
    name = StringField('اسم الساكن', validators=[DataRequired()])
    tenant_id = StringField('رقم السجل المدني', validators=[DataRequired()])
    mobile = StringField('رقم الجوال', validators=[DataRequired()])
    start_date = DateField('تاريخ استلام الوحدة', validators=[DataRequired()])
    workplace = SelectField('القطاع', choices=[
        ('الأمن العام - الشرطة', 'الأمن العام - الشرطة'),
        ('الأمن العام - المرور', 'الأمن العام - المرور'),
        ('الأمن العام - الدوريات الأمنية', 'الأمن العام - الدوريات الأمنية'),
        ('حرس الحدود', 'حرس الحدود'),
        ('الدفاع المدني', 'الدفاع المدني'),
        ('المخدرات', 'المخدرات'),
        ('السجون', 'السجون'),
        ('المجاهدين', 'المجاهدين'),
        ('الطوارئ الخاصة', 'الطوارئ الخاصة'),
        ('أمن المنشآت', 'أمن المنشآت'),
        ('الأفواج الأمنية', 'الأفواج الأمنية'),
        ('المباحث', 'المباحث'),
        ('الجوازات', 'الجوازات')
    ], validators=[DataRequired()])
    property_id = SelectField('الوحدة السكنية', coerce=int, validators=[DataRequired()])
    submit = SubmitField('إرسال')

    def __init__(self, *args, **kwargs):
        super(TenantForm, self).__init__(*args, **kwargs)
        self.property_id.choices = [(property.id, f"الحي {property.cluster} - الوحدة {property.villa}") for property in Property.query.all()]

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember = BooleanField('تذكر الدخول')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    submit = SubmitField('Register')