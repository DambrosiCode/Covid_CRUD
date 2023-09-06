# method to upload csv files to mongoDB
import csv
from pymongo_get_db import get_database


def upload_csv(db_name, collection_name, csv_path):
    # Get db and collection
    db = get_database(db_name)
    collection = db[collection_name]

    # Read csv file
    with open(csv_path) as csvfile:
        csv_reader = csv.DictReader(csvfile)
        collection_json = []

        for row in csv_reader:
            # Remove spaces from column names
            cleaned_row = {key.replace(' ', '_'): value for key, value in row.items()}
            collection_json.append(cleaned_row)

        # Upload to collection
        collection.insert_many(collection_json)



if __name__ == "__main__":
    # Specify your database name, collection name, and CSV file path here
    database_name = "database_name"
    collection_name = "collection_name"
    csv_file_path = "csv/folder/path/"
    
    # Call the function to upload the CSV data to MongoDB
    upload_csv_to_mongodb(database_name, collection_name, csv_file_path)
