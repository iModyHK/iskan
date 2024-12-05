from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegistrationForm, PropertyForm, TenantForm  # Use relative import
from .models import User, Property, Tenant  # Use relative import
from . import app, db
from sqlalchemy import or_
import pandas as pd
from io import BytesIO
from datetime import datetime

@app.route('/')
@login_required
def index():
    vacant_properties = Property.query.filter_by(status='شاغرة').count()
    occupied_properties = Property.query.filter_by(status='مشغولة').count()
    tenants_by_workplace = db.session.query(Tenant.workplace, db.func.count(Tenant.id)).filter(Tenant.archived == False).group_by(Tenant.workplace).all()
    return render_template('index.html', vacant_properties=vacant_properties, occupied_properties=occupied_properties, tenants_by_workplace=tenants_by_workplace)

@app.route('/properties')
@login_required
def properties():
    properties = Property.query.all()
    return render_template('properties.html', properties=properties)

@app.route('/tenants')
@login_required
def tenants():
    tenants = Tenant.query.filter_by(archived=False).all()
    return render_template('tenants.html', tenants=tenants)

@app.route('/archived_tenants')
@login_required
def archived_tenants():
    tenants = Tenant.query.filter_by(archived=True).all()
    return render_template('archived_tenants.html', tenants=tenants)

@app.route('/export_archived_tenants')
@login_required
def export_archived_tenants():
    tenants = Tenant.query.filter_by(archived=True).all()
    data = [{
        'اسم الساكن': tenant.name,
        'رقم السجل المدني': tenant.tenant_id,
        'رقم الجوال': tenant.mobile,
        'القطاع': tenant.workplace,
        'الحي': tenant.cluster,
        'الوحدة': tenant.villa,
        'تاريخ بدء الإيجار': tenant.start_date
    } for tenant in tenants]
    df = pd.DataFrame(data)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Archived Tenants')
    writer.close()  # Use close instead of save
    output.seek(0)
    return send_file(output, download_name='archived_tenants.xlsx', as_attachment=True)

@app.route('/add_property', methods=['GET', 'POST'])
@login_required
def add_property():
    form = PropertyForm()
    if form.validate_on_submit():
        property = Property(cluster=form.cluster.data, villa=form.villa.data, status='شاغرة')
        db.session.add(property)
        db.session.commit()
        flash('تمت إضافة الوحدة السكنية بنجاح!', 'success')
        return redirect(url_for('properties'))
    return render_template('add_property.html', form=form)

@app.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    property = Property.query.get_or_404(property_id)
    form = PropertyForm(obj=property)
    if form.validate_on_submit():
        property.cluster = form.cluster.data
        property.villa = form.villa.data
        property.status = form.status.data
        db.session.commit()
        flash('تم تحديث الوحدة السكنية بنجاح!', 'success')
        return redirect(url_for('properties'))
    return render_template('edit_property.html', form=form)

@app.route('/delete_property/<int:property_id>', methods=['POST'])
@login_required
def delete_property(property_id):
    property = Property.query.get_or_404(property_id)
    db.session.delete(property)
    db.session.commit()
    flash('تم حذف الوحدة السكنية بنجاح!', 'success')
    return redirect(url_for('properties'))

@app.route('/add_tenant', methods=['GET', 'POST'])
@login_required
def add_tenant():
    form = TenantForm()
    
    # Populate the property_id field with available properties
    available_properties = Property.query.filter_by(status='شاغرة').all()
    form.property_id.choices = [(property.id, f"{property.cluster} - {property.villa}") for property in available_properties]
    
    if form.validate_on_submit():
        if form.property_id.choices:
            property = Property.query.get(form.property_id.data)
            tenant = Tenant(
                name=form.name.data,
                tenant_id=form.tenant_id.data,
                mobile=form.mobile.data,
                start_date=form.start_date.data,
                workplace=form.workplace.data,
                property_id=form.property_id.data,
                cluster=property.cluster,
                villa=property.villa
            )
            db.session.add(tenant)
            db.session.commit()
            property.update_status()
            flash('تمت إضافة الساكن بنجاح!', 'success')
            return redirect(url_for('tenants'))
        else:
            flash('لا توجد وحدات سكنية شاغرة. لا يمكن إضافة ساكن جديد.', 'danger')
    
    return render_template('add_tenant.html', form=form)

@app.route('/edit_tenant/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def edit_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    form = TenantForm(obj=tenant)
    if form.validate_on_submit():
        tenant.name = form.name.data
        tenant.tenant_id = form.tenant_id.data
        tenant.mobile = form.mobile.data
        tenant.start_date = form.start_date.data
        tenant.workplace = form.workplace.data
        tenant.property_id = form.property_id.data
        tenant.cluster = tenant.property.cluster
        tenant.villa = tenant.property.villa
        db.session.commit()
        tenant.property.update_status()
        flash('تم تحديث الساكن بنجاح!', 'success')
        return redirect(url_for('tenants'))
    return render_template('edit_tenant.html', form=form)

@app.route('/archive_tenant/<int:tenant_id>', methods=['POST'])
@login_required
def archive_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    tenant.archived = True
    tenant.eviction_date = datetime.utcnow().date()  # Set eviction date
    db.session.commit()
    property = Property.query.get(tenant.property_id)
    if property:
        property.update_status()
    flash('تمت اخلاء الوحدة بنجاح!', 'success')
    return redirect(url_for('tenants'))

@app.route('/unarchive_tenant/<int:tenant_id>', methods=['POST'])
@login_required
def unarchive_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    tenant.archived = False
    db.session.commit()
    property = Property.query.get(tenant.property_id)
    if property:
        property.update_status()
    flash('تم إلغاء اخلاء الوحدة بنجاح!', 'success')
    return redirect(url_for('archived_tenants'))

@app.route('/delete_archived_tenant/<int:tenant_id>', methods=['POST'])
@login_required
def delete_archived_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    db.session.delete(tenant)
    db.session.commit()
    flash('تم حذف السكان نهائيًا بنجاح!', 'success')
    return redirect(url_for('archived_tenants'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user is None:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            try:
                db.session.commit()
                flash('Registration successful! You can now log in.')
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'danger')
        else:
            flash('Username already exists. Please choose a different username.', 'danger')
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/protected')
@login_required
def protected():
    return 'This is a protected route.'

@app.route('/index')
@login_required
def dashboard():
    return render_template('index.html')