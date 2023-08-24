# Making config.json
To run this software user must connect to a pymongoDB by making a config.json file in the main directory with the necessary credentials  
`{  
  "mongodb_username": "username",  
  "mongodb_password": "password",  
  "mongodb_socket": "socketID"  
}`

# pymongo_get_db.py

## get_database()
### Function:  
interact with mongoDB API  
### params:  
* db_name(str) - name of database to upload to
### returns: 
mongoDB database of specified name and login credentials (see config.json)

# pymongo_insert.py

## upload_csv()
### Function:  
Allows upload of CSV to mongoDB  
### params:  
* db_name(str) - name of database to upload to
* collection_name (str) - name of collection in database
* csv_path (str) - path of csv file to upload
### returns: 
csv converted to json format to upload to mongoDB