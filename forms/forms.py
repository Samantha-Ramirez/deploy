from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session
from __init__ import create_app
from werkzeug.utils import secure_filename
from datetime import datetime, date
from os import path
import urllib.request
import datetime 
import json
import os

# BLUEPRINTS
forms_bp = Blueprint('forms_bp', __name__,
    template_folder='templates',
    static_folder='static')

# PAGE'S REQUIREMENTS
app, mysql, environment = create_app()

def get_json_form(form):
    if environment == 'development':
        stformFullPath = os.path.realpath('./stform.json')
    else:
        stformFullPath = os.path.realpath('./deploy/stform.json')
    f = open(stformFullPath,)
    data = json.load(f)
    return data, f

def form_select(table):
    query = 'SELECT * FROM ' + table
    cur = mysql.connection.cursor()
    cur.execute(query)
    mysql.connection.commit()
    data = cur.fetchall()

    return data

def get_date():
    today = date.today()
    value = today.strftime("%d/%m/%Y")
    return value

# PAGES
@forms_bp.route('/dynamic_form/<form>-<formreq>')
def dynamic_form(form, formreq):
    # GENERAL
    data, f = get_json_form(form)
    attrb = data[formreq]['attributes']
    label = data[formreq]['label']
    payDict = {}
    for i in attrb:
        # Select
        if i['type'] == 'select' and i['selectTable'] != None:
            i['options'] = form_select(i['selectTable'])

        # Date
        elif i['type'] == 'date':
            i['value'] = get_date()

    f.close()
    link = '/forms/add/' + str(form) + '-' + str(formreq)
    type = 'Crear'

    return render_template('forms/dynamic_form.html', attrb = attrb, formreq = formreq, form = form, user_type = session['user_type'], id = session['id'], environment = environment, label = label, link = link, type = type)

@forms_bp.route('/add/<form>-<formreq>', methods=['GET', 'POST'])
def add(form, formreq):
    if request.method == 'POST':
        data, f = get_json_form(form)
        attrb = data[formreq]['attributes']
        into = []
        values = []
        
        for i in attrb:
            # USER
            if i['name'] == 'user':
                into.append(i['name']) 
                values.append('"' + str(session['id']) + '"')
            # USER_TYPE
            elif (formreq == 'seller' or formreq == 'client') and i['name'] == 'user_type':
                into.append(i['name'])
                values.append('"' + formreq + '"')
            # DATE
            elif formreq == 'recharge_request' and i['name'] == 'date':                    
                today = date.today().strftime('%Y-%m-%d')
                into.append('date') 
                values.append('"' + today + '"') 
            # FILE
            elif i['type'] == 'file':
                file = request.files[i['name']]
                fileName = secure_filename(file.filename)
                route = path.abspath(path.join(app.static_folder, 'img', fileName))
                file.save(route)
                into.append(i['name']) 
                values.append('"' + fileName + '"')
            # CHECKBOX AND RADIO
            elif i['type'] == 'checkbox' or i['type'] == 'radio' :
                if i['label'] != None:
                    checkbox = request.form.getlist(i['name'])
                    string = ', '.join(checkbox)
                    into.append(i['name']) 
                    values.append('"' + string + '"')
            # MULTIPLE SELECT
            elif formreq == 'supplier' and i['name'] == 'platform_that_supplies':
                into.append(i['name'])
                platforms = request.form.getlist(i['name'])
                platforms_names = []
                for pl in platforms:
                    query = 'SELECT name FROM platform WHERE id = ' + pl
                    cur = mysql.connection.cursor()
                    cur.execute(query)
                    mysql.connection.commit()
                    platforms_names.append(cur.fetchone()[0])
                string = ', '.join(platforms_names)
                values.append('"' + string + '"')
            # GENERAL
            elif i['type'] != 'hidden' and i['name'] != 'platform':
                into.append(i['name']) 
                values.append('"' + request.form[i['name']] + '"')
            # LAST SCREENS OF STREAMING ACCOUNT 
            elif formreq == 'streaming_account' and i['name'] == 'last_screens':
                into.append(i['name']) 
                q = 'SELECT screen_amount FROM platform WHERE id = ' + request.form['select_platform']
                cur = mysql.connection.cursor()
                cur.execute(q)
                mysql.connection.commit()
                screen_amount = cur.fetchone()[0]
                values.append('"' + str(screen_amount) + '"')

        sep = ',' 
        if formreq == 'client' or formreq == 'seller':
            query = 'INSERT INTO user (' + sep.join(into) + ') ' +  'VALUES (' + sep.join(values) + ')'
        else:
            query = 'INSERT INTO ' + formreq + '(' + sep.join(into) + ') ' +  'VALUES (' + sep.join(values) + ')'
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()

        # RECHARGE REQUEST FEEDBACK
        if formreq == 'recharge_request':
            flash('Su petición está siendo procesada')  
            return redirect('/')
        else: 
            flash('Agregado exitosamente')                 

        # ADD SCREENS 
        if formreq == 'streaming_account':
            query2 = 'SELECT * FROM streaming_account WHERE id=(SELECT MAX(id) FROM streaming_account)'
            cur.execute(query2)
            mysql.connection.commit()
            saData = cur.fetchone()

            query3 = 'SELECT * FROM platform WHERE id = ' + str(saData[2])
            cur.execute(query3)
            mysql.connection.commit()
            plData = cur.fetchone()
            
            values1 = ['"' + str(saData[0]) + '"', '"' + str(saData[2]) + '"', '"' + str(saData[4]) + '"', '"' + str(saData[5]) + '"']
            for x in range(1, plData[4] + 1):
                values1.insert(1, '"' + str(x) + '"')
                sep = ', '
                query3 = 'INSERT INTO screen (account_id, profile, platform, start_date, end_date) VALUES (' + sep.join(values1) + ')'
                cur.execute(query3)
                mysql.connection.commit()
                del values1[1]
                    
        f.close()
    return redirect('/tables/dynamic_table/' + form + '-' + formreq)

@forms_bp.route('/edit/<form>-<formreq>/<id>')
def edit(form, formreq, id):
    data, f = get_json_form(form)
    attrb = data[formreq]['attributes']
    label = data[formreq]['label']
    if formreq == 'client' or formreq == 'seller':
        query = 'SELECT * FROM user WHERE id = ' + id
    else:
        query = 'SELECT * FROM ' + formreq + ' WHERE id = ' + id
    cur = mysql.connection.cursor()
    cur.execute(query)
    mysql.connection.commit()
    formData = cur.fetchall()
    payDict = {}
    for i in attrb:
        # Select
        if i['type'] == 'select' and i['selectTable'] != None:
            i['options'] = form_select(i['selectTable'])

        # Date
        elif i['type'] == 'date':
            i['value'] = get_date() 
    
    f.close()
    link = '/forms/update/' + str(form) + '-' + str(formreq) + '/' + str(formData[0][0])
    type = 'Editar'

    return render_template('forms/dynamic_form.html', rowToEdit = formData[0], attrb = attrb, formreq = formreq, form = form, user_type = session['user_type'], id = session['id'], label = label, link = link, type = type)

@forms_bp.route('/update/<form>-<formreq>/<id>', methods=['GET', 'POST'])
def update(form, formreq, id):
    if request.method == 'POST':
        data, f = get_json_form(form)
        attrb = data[formreq]['attributes']
        values = []
        for i in attrb:
            # USER
            if i['name'] == 'user':
                string = i['name'] + ' = ' + '"' + str(session['id']) + '"'
                values.append(string)
            # USER_TYPE
            elif (formreq == 'seller' or formreq == 'client') and i['name'] == 'user_type':
                string = i['name'] + ' = ' + '"' + formreq + '"'
                values.append(string)
            # FILE
            elif i['type'] == 'file':
                file = request.files[i['name']]
                fileName = secure_filename(file.filename)
                route = path.abspath(path.join(app.static_folder, 'img', fileName))
                file.save(route)
                string = i['name'] + ' = ' + '"' + fileName + '"'
                values.append(string)
            # CHECKBOX AND RADIO
            elif i['type'] == 'checkbox' or i['type'] == 'radio' :
                if i['label'] != None:
                    checkbox = request.form.getlist(i['name'])
                    string = ', '.join(checkbox)
                    string = i['name'] + ' = ' + '"' + string + '"'
                    values.append(string)
            # MULTIPLE SELECT
            elif formreq == 'supplier' and i['name'] == 'platform_that_supplies':
                platforms = request.form.getlist(i['name'])
                platforms_names = []
                for pl in platforms:
                    query = 'SELECT name FROM platform WHERE id = ' + pl
                    cur = mysql.connection.cursor()
                    cur.execute(query)
                    mysql.connection.commit()
                    platforms_names.append(cur.fetchone()[0])
                string = ', '.join(platforms_names)
                string = string = i['name'] + ' = ' + '"' + string + '"'
                values.append(string)
            # GENERAL
            elif i['type'] != 'hidden' and i['name'] != 'platform':
                string = i['name'] + ' = ' + '"' + request.form[i['name']] + '"'
                values.append(string)
            # LAST SCREENS OF STREAMING ACCOUNT 
            elif formreq == 'streaming_account' and i['name'] == 'last_screens':
                q = 'SELECT screen_amount FROM platform WHERE id = ' + request.form['select_platform']
                cur = mysql.connection.cursor()
                cur.execute(q)
                mysql.connection.commit()
                screen_amount = cur.fetchone()[0]
                values.append(i['name'] + ' = ' + '"' + str(screen_amount) + '"')

        sep = ', '
        if formreq == 'client' or formreq == 'seller':
            query2 = 'UPDATE user SET ' + sep.join(values) + ' WHERE id = ' + id
        else:
            query2 = 'UPDATE ' + formreq + ' SET ' + sep.join(values) + ' WHERE id = ' + id
        cur = mysql.connection.cursor()
        cur.execute(query2)
        mysql.connection.commit()
        flash('Editado exitosamente')

        f.close()
        return redirect('/tables/dynamic_table/' + form + '-' + formreq)

@forms_bp.route('/delete/<form>-<formreq>/<id>')
def delete(form, formreq, id):
    cur = mysql.connection.cursor()
    # DYNAMIC
    if formreq == 'streaming_account':
        query1 = 'DELETE FROM screen WHERE account_id = ' + id
        cur.execute(query1)
        mysql.connection.commit()
    
    elif formreq == 'platform':
        query1 = 'DELETE FROM streaming_account WHERE select_platform = ' + id
        cur.execute(query1)
        mysql.connection.commit()
        query2 = 'DELETE FROM screen WHERE platform = ' + id
        cur.execute(query2)
        mysql.connection.commit()

    elif formreq == 'supplier':
        query1 = 'SELECT id FROM streaming_account WHERE select_supplier = ' + id 
        cur.execute(query1)
        mysql.connection.commit()
        saId = cur.fetchone()
        if saId:
            query2 = 'DELETE FROM screen WHERE account_id = ' + str(saId[0])
            cur.execute(query2)
            mysql.connection.commit()
            query3 = 'DELETE FROM streaming_account WHERE select_supplier = ' + id
            cur.execute(query3)
            mysql.connection.commit()
    
    elif formreq == 'client':
        query1 = 'UPDATE screen SET client = NULL WHERE client = ' + id
        cur.execute(query1)
        mysql.connection.commit()
    
    # STATIC
    if formreq == 'client' or formreq == 'seller':
        query3 = 'DELETE FROM user WHERE id = ' + id
    else:
        query3 = 'DELETE FROM ' + formreq + ' WHERE id = ' + id
    cur.execute(query3)
    mysql.connection.commit()
       
    flash('Borrado exitosamente')
    return redirect('/tables/dynamic_table/' + form + '-' + formreq)