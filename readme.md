
# Covid19 Metadata Explorer (CovMetEr)

This project is a Dash CRUD application designed to allow the user to make, view, and edit metadata collection from the CORD19 dataset "Risk Factors" [here](https://www.kaggle.com/datasets/allen-institute-for-ai/CORD-19-research-challenge) stored in a mongoDB server.
## Installation

Currently CovMetEr must be installed locally. 

To ensure proper installation of packages and no conflicts create a new python venv and clone this repo to a new directory

```bash
  conda create --name myenv
  conda activate myenv
  git clone https://github.com/DambrosiCode/Covid_CRUD.git
```
After changing your working directory to inside the project, install required python packages 
```bash
  cd CRUD
  conda install --yes --file requirements.txt
```
Your venv should be set up now. 

Currently the Covid metadata live in mongoDB, which is accessible through a configured config file. For security reasons, a user needs to either generate their own mongoDB repository through https://cloud.mongodb.com (see Generating a config.json) or contact the repo owner.

### Generating a config.json
To access a mongoDB cloud server a user needs a password, username, and socket to a cluster. If a user wishes to use their own cloud server they should first follow the instructions laid out in https://www.mongodb.com/basics/create-database. (Note: Databases up to 512MB are free) 

Once a server is setup a config file named "CRUD/config.json" should be created in the main directory with the following format 
```json
{
  "mongodb_username": "userName",
  "mongodb_password": "passWord",
  "mongodb_socket": "socketURI"
}
```
A user should now have access to their mongoDB cloud with the pymongo API and "Covid_CRUD/pymongo_get_db.py" script.

#### Setup mongoDB
Finally the user should download the [required databased](https://www.kaggle.com/datasets/allen-institute-for-ai/CORD-19-research-challenge) (8_risk_factors) from kaggle. The directory should have the structure of ~28 risk factors saved as separate .csv files. Each of these will be uploaded as a collection to mongoDB, with each row/study being a document and column as a field (NOTE: spaces in column names must be replaced with "_").

The user can choose to upload the .CSV files as they see fit (provided the format above is kept), however "Covid_CRUD/pymongo_insert.py" script offers a user a native way to upload files properly formatted. 

```bash
python pymongo_insert.py \
--db_name database_name \
--collection_name collection_name \
--csv_path path/to/folder/of/8_risk_factors/
```
Afterwards the app.py script can be run and the app can viewd locally. 
## Roadmap

* Plotly integration 
* More responsive to user interaction 
    * Visualize edits
    * Regex filtering
* Server-side Caching
* Allow users to apply for an account
    * Record which users made what changes 
* Study tags + tag filtering


## License

[MIT](https://choosealicense.com/licenses/mit/)

