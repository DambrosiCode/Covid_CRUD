from pymongo import MongoClient
import json


def get_database():
    #load in password etc from config json file
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    username = config['username']
    password = config['password']
    socket = config['mongodb_socket']

    URI = "mongodb+srv://%s:%s@%s" % (
        username, password, socket)

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(URI)
    print(client)
    # Create the database for our example (we will use the same database throughout the tutorial
    return client['Cluster0']


if __name__ == "__main__":
    # Get the database
    dbname = get_database()