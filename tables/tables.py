from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session
from __init__ import create_app
import datetime 
import json
import os

# BLUEPRINTS
tables_bp = Blueprint('tables_bp', __name__,
    template_folder='templates')

# PAGE'S REQUIREMENTS
app, mysql = create_app()

def get_json_form(form):
    if form == 'st':
        stformFullPath = os.path.realpath('./stform.json')
        f = open(stformFullPath,)
        data = json.load(f)
    elif form == 'dy':
        dyformFullPath = os.path.realpath('./dyform.json')
        f = open(dyformFullPath,)
        data = json.load(f)
    return data, f

# PAGES
@tables_bp.route('/dynamic_table/<form>-<formreq>')
def dynamic_table(form, formreq):
    if 'loggedin' in session:
        data, f = get_json_form(form)
        attrb = data[formreq]['attributes']
        query = data[formreq]['query']
        if formreq == 'client' and session['user_type'] == 'admin':
            query = "SELECT cl.id, sl.username, cl.username, cl.phone, cl.email, cl.password FROM client cl, seller sl WHERE cl.user = sl.id"
        elif form == 'dy' or (formreq == 'client' and session['user_type'] != 'admin'):
            query = query + str(session['id'])
            
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()
        tableData = list(cur.fetchall())

        # Finding the index
        index = 0
        fileIndex = None
        for i in attrb:
            if i['type'] == 'file':
                fileIndex = index
            elif i['type'] == 'date':
                x = 0
                for tb in tableData:
                    tb = list(tb)
                    tb[index] = datetime.datetime.strptime(str(tb[index]), "%Y-%m-%d").strftime('%d-%m-%Y')
                    tableData[x] = tb
                    x = x + 1
            index = index + 1

        return render_template('tables/dynamic_table.html', formreq = formreq, attrb = attrb, tableData = tableData, 
        fileIndex = fileIndex, form = form, user_type = session['user_type'])
        
        f.close()
    return redirect('/auth/login')