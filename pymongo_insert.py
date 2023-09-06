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


def main():
    parser = argparse.ArgumentParser(description="Upload CSV data to MongoDB.")
    parser.add_argument("--db_name", required=True, help="Name of the MongoDB database.")
    parser.add_argument("--collection_name", required=True, help="Name of the MongoDB collection.")
    parser.add_argument("--csv_path", required=True, help="Path to the CSV file to upload.")

    args = parser.parse_args()
    upload_csv_to_mongodb(args.db_name, args.collection_name, args.csv_path)

if __name__ == "__main__":
    main()
