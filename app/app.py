# import packages
from flask import Flask, render_template, redirect, request, flash, jsonify
from flask_bootstrap import Bootstrap
from pymongo_get_db import get_database
from bson import ObjectId
import pandas as pd
import os

#TODO: set collection
#TODO: filter by column
#TODO: upload csv data
#TODO: download as csv
#TODO: change tab title
#TODO: favicon

current_collection = "Test"

#load Flask
app = Flask(__name__)
app.secret_key = 'throughthemountain42'
#get mongoDB
db = get_database('Covid19_Risk_Factors')

#homepage route
@app.route('/')
def index():
    #get names of all collections
    collection_list = sorted(db.collection_names())
    #get collection documents
    all_data = db[current_collection].find()

    return render_template("index.html",
                           data=all_data, #dataframe of current collection
                           collection_list=collection_list) #all collections)


#add a new row
@app.route('/insert', methods=['POST'])
def insert():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        db[current_collection].insert_one({'name':name, 'email':email, 'phone':phone})
        flash("New Data Successfully Added")
        return redirect('/')

#TODO: have this run on string id in URL like delete
#update a row
@app.route('/update', methods=['GET','POST'])
def update():
    if request.method == 'POST':
        #_id = request.form.get('_id')
        #print(ObjectId(_id))
        print(request.form['_id'])
        db[current_collection].update_one(
            {'_id':ObjectId(request.form['_id'])},
            {'$set':{
                'name':request.form['name'],
                'email':request.form['email'],
                'phone':request.form['phone']
            }}
        )

        flash("Data Successfully Updated")

        return redirect('/')

#delete row
@app.route('/delete/<string:_id>', methods=['POST'])
def delete(_id):
    _id = ObjectId(_id)
    db[current_collection].delete_one({'_id':_id})

    flash("Document Successfully Deleted")


    return redirect('/')

@app.route('/update_variable')
def update_variable():
    selected_collection = request.args.get('collection')
    global current_collection
    current_collection = f"Selected collection: {selected_collection}"
    return jsonify({"updatedVariable": current_collection})

if __name__ == "__main__":
    app.run(debug=True)