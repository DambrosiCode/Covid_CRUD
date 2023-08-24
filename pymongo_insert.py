# method to upload csv files to mongoDB
import csv
from pymongo_get_db import get_database

def upload_csv(db_name, collection_name, csv_path):
    # get db and collection
    db_name = get_database(db_name)
    collection_name = db_name[collection_name]

    #read csv file
    csv_json = csv.DictReader(open(csv_path))
    collection_json = []
    for row in csv_json:
        collection_json.append(row)
    print(collection_json)
    # upload to collection
    collection_name.insert_many(collection_json)



