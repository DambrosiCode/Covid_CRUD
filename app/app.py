from dash import Dash, dash_table, dcc, ctx, html, Input, Output, State, callback
from pymongo_get_db import get_database
from mongo_manip import id_df_change, data_validation
import pandas as pd
from bson import ObjectId
from pymongo import UpdateOne, UpdateMany
import io
import base64

app = Dash(__name__)
# TODO: include input limiting
# TODO: Verify user when changes are made
# TODO: Vizualize statistics
# TODO: Vizualize changes that have been made before update
# TODO: refresh dataframe manually and/or intervally
# TODO: Serverside Caching (fine with small datasets but should be scaleable)
# TODO: Improve Aesthetics


# connect to mongoDB
mongo_db = get_database('Covid19_Risk_Factors')


class MongoDBConnector:
    def __init__(self, database='Covid19_Risk_Factors', default_collection_name='Age'):
        self.db = get_database(database)
        self.default_collection = default_collection_name

    def get_mongo_collection(self, collection_name=None):
        if collection_name is None:
            collection_name = self.default_collection

        collection = self.db[collection_name]
        return collection

    def get_mongo_as_df(self, collection_name=None):
        if collection_name is None:
            collection_name = self.default_collection

        collection = self.db[collection_name]
        df = pd.DataFrame(collection.find())
        df['_id'] = df['_id'].astype(str)
        return df


# get mongo connection
mongo_connector = MongoDBConnector(default_collection_name='Age')
# dataframe at startup
mongo_initial_df = mongo_connector.get_mongo_as_df()
target_cols = ['Date', 'Study', 'Study_Link', 'Journal', 'Sample_Size', 'Study_Type',
               'Severe', 'Fatality',

               'Severe_lower_bound', 'Severe_upper_bound', 'Severe_p-value',
               'Severe_Adjusted', 'Severe_Calculated',
               'Fatality_lower_bound', 'Fatality_upper_bound', 'Fatality_p-value',
               'Fatality_Adjusted', 'Fatality_Calculated',
               'Multivariate_adjustment',
               'Critical_only', 'Discharged_vs._death?',
               '_id'
               ]
mongo_initial_df = mongo_initial_df.loc[:, target_cols]  # subset desired cols
# collection cursor
# mongo_collection_cursor = mongo_connector.get_mongo_collection()

app.layout = html.Div(children=[
    # datatable
    dash_table.DataTable(
        id='editable-table',
        columns=[
            {'name': col, 'id': col, 'deletable': False, 'editable': (col != '_id')}
            for col in mongo_initial_df.columns
        ],
        style_table={
            'overflowX': 'auto',
            'maxHeight': '90vh',
            'overflowY': 'auto',  # Enable vertical scrolling
        },
        style_cell={'minWidth': '150px',
                    'maxWidth': '150px',
                    'maxHeight': 'auto',
                    'textAlign': 'left',
                    'whiteSpace': 'normal',
                    'textOverflow': 'ellipsis'},

        fixed_rows={'headers': True},
        data=mongo_initial_df.to_dict('records'),
        editable=True,
        row_deletable=True,
        filter_action='native',
        sort_action='native',
        page_action='native',
        page_current=0,
        page_size=5,
    ),
    html.Button('Add Row', id='add-row-button', n_clicks=0),
    dcc.Upload(html.Button('Upload .csv'), id='csv-upload'),
    html.Button('Update Database', id='mongo-update-button', n_clicks=0),
    dcc.Dropdown(id='collection-dropdown', options=sorted(mongo_db.list_collection_names()), value='Age'),

    # confirmation popup
    dcc.ConfirmDialog(
        id='update-confirm-box',
        message='Updated Confirmed',
    ),

    dcc.ConfirmDialog(
        id='validation-error'
    ),

    # store initial dataframe in dcc.Store to compare usermade changes later
    dcc.Store(id='old-dataframe', data=mongo_initial_df.to_dict("records")),
    # dcc.Store(id='collection-id', data='Test')
])


# update user if validation fails
@callback([Output('validation-error', 'message'),
          Output('validation-error', 'displayed')],

          Input('mongo-update-button', 'n_clicks'),

          State('editable-table', 'data'),
          State('old-dataframe', 'data'))
def validate_notification(clicks, edited_df, old_df):
    df_diff = id_df_change(old_df, edited_df)
    new_entry_ids = [_id['_id'] for _id in df_diff]
    edited_df = pd.DataFrame(edited_df)
    new_entries = edited_df[edited_df['_id'].isin(new_entry_ids)]

    validation = True

    if validation and clicks > 0:
        results = data_validation(new_entries)
        print(results)
        if results is not True:
            return results, True
        else:
            return 'Validation Successful!', True


# edit dataframe
@callback([Output('editable-table', 'data'),
           Output('editable-table', 'columns'),
           Output('editable-table', 'page_current'),
           Output('old-dataframe', 'data'),
           Output('update-confirm-box', 'displayed'), ],

          Input('collection-dropdown', 'value'),
          Input('add-row-button', 'n_clicks'),
          Input('mongo-update-button', 'n_clicks'),
          Input('csv-upload', 'contents'),
          Input('csv-upload', 'filename'),

          State('editable-table', 'columns'),
          State('editable-table', 'page_size'),
          State('editable-table', 'data'),
          State('old-dataframe', 'data'))
def build_dataframe(selected_collection, n_clicks, update_button, contents, filename,
                    columns, page_size, edited_df, old_df):
    # callback context
    trigger = ctx.triggered_id

    # if user uploads a csv dataframe
    if trigger == 'csv-upload':
        # convert upload to dataframe
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        csv_df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

        # remove _id column if applicable, then add new ObjectIds
        csv_df = csv_df.drop(['_id'], axis=1, errors='ignore')
        new_ids = [str(ObjectId()) for x in csv_df.index]

        csv_df['_id'] = new_ids

        # append dataframe to current collection
        print(edited_df)
        combined_df = pd.concat([pd.DataFrame(edited_df), csv_df], ignore_index=True)

        print(combined_df)
        last_page = (len(combined_df) + 1) // page_size + ((len(combined_df) + 1) % page_size > 0)

        # return new dataframe as editable_df+csv_df, columns, go to last page of new df, don't update old df, no notifcation box
        return combined_df.to_dict('records'), columns, last_page - 1, old_df, False

    # get number of pages from pagination
    last_page = (len(edited_df) + 1) // page_size + ((len(edited_df) + 1) % page_size > 0)

    # append new rows if add rows is clicked
    if trigger == 'add-row-button':
        edited_df.append({c['id']: str(ObjectId()) for c in columns})
        print(last_page)

        # add new row to editable dataframe, update columns, set start page to last page, keep dcc.Store dataframe to unupdated fd
        return edited_df, columns, last_page - 1, old_df, False
    # switch to a new dataframe
    elif trigger == 'collection-dropdown':
        new_df = mongo_connector.get_mongo_as_df(selected_collection)

        # get columns
        columns = [
            {'name': col, 'id': col, 'deletable': False} for col in new_df.columns
        ]
        # change editable table to new collection, update columns, set start page, update dcc.Store dataframe to new collection
        return new_df.to_dict('records'), columns, 0, new_df.to_dict('records'), False

    # update mongoDB
    elif trigger == 'mongo-update-button':
        print('update button')
        print(selected_collection)
        # set new cursor to selected collection
        mongo_collection_cursor = mongo_connector.get_mongo_collection(selected_collection)

        if update_button > 0:

            # compare dataframes
            df_diff = id_df_change(old_df, edited_df)
            print(df_diff)

            # get rows deleted, added, and updated
            df_diff_del = [ObjectId(diff['_id']) for diff in df_diff if diff['change_type'] == 'deleted']
            df_diff_add = [diff['_id'] for diff in df_diff if diff['change_type'] == 'added']
            df_diff_upd = [diff['_id'] for diff in df_diff if diff['change_type'] == 'updated']

            # execute deletion
            if len(df_diff_del) > 0:
                print({'_id': {'$in': df_diff_del}})
                mongo_collection_cursor.delete_many({'_id': {'$in': df_diff_del}})

            # execute addition
            if len(df_diff_add) > 0:
                added_rows = [doc for doc in edited_df if doc['_id'] in df_diff_add]

                for doc in added_rows:
                    doc['_id'] = ObjectId(doc['_id'])

                mongo_collection_cursor.insert_many(added_rows)

            # execute updates
            if len(df_diff_upd) > 0:
                print('updates')
                updated_rows = [doc for doc in edited_df if doc['_id'] in df_diff_upd]
                print(updated_rows)
                # remove
                updated_rows_noid = [{key: value for key, value in doc.items() if key != '_id'} for doc in updated_rows]

                bulk_operations = []
                for i, doc in enumerate(updated_rows):
                    bulk_operations.append(UpdateMany({'_id': ObjectId(doc['_id'])},
                                                      {'$set': updated_rows_noid[i]}))
                print(bulk_operations)
                mongo_collection_cursor.bulk_write(bulk_operations)

            # return update notification, store edited df in dcc.Store
            return edited_df.to_dict('records'), columns, 0, edited_df.to_dict('records'), True


if __name__ == '__main__':
    app.run_server(debug=True)
