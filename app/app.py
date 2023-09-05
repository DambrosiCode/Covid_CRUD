from dash import Dash, dash_table, dcc, ctx, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

from pymongo_get_db import get_database
from mongo_manip import id_df_change, data_validation
import pandas as pd
from bson import ObjectId
from pymongo import UpdateOne, UpdateMany
import io
import base64
#import user hashed passwords
from user_config import USER_PW
from bcrypt import checkpw

#import config
from table_config import table_config_cond
import dash_auth

app = Dash(
    external_stylesheets=[dbc.themes.CYBORG]
           )
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
    html.H1('Covid19 Risk Analysis Explorer', style={'textAlign': 'center'}),
    html.P('Select a population collection'),
    dcc.Dropdown(id='collection-dropdown', options=sorted(mongo_db.list_collection_names()),
                 value='Age',
                 className='dropdown'),

    # datatable
    dash_table.DataTable(
        id='editable-table',
        columns=[
            {'name': col, 'id': col, 'deletable': False, 'editable': (col != '_id')}
            for col in mongo_initial_df.columns
        ],
        style_header={
            'backgroundColor': 'rgb(71, 91, 90)',
            'color': 'white'
        },
        style_table={
            'overflowX': 'auto',
            'maxHeight': '90vh',
            'overflowY': 'auto',  # Enable vertical scrolling
        },
        style_data={
            'backgroundColor': 'rgb(163, 169, 170)',
            'color': 'black'
        },
        style_filter={
            'backgroundColor': 'rgb(141, 142, 142)',
            'color': 'white',
        },
        style_cell={'minWidth': '175px',
                    'maxWidth': '175px',
                    'maxHeight': 'auto',
                    'textAlign': 'left',
                    'whiteSpace': 'normal',
                    'textOverflow': 'ellipsis',
                    'font_size':'10px',
                    'color':'black'},
        style_data_conditional=table_config_cond,

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
    html.Div([
        dbc.Button('Add Row', id='add-row-button', n_clicks=0),
        html.Div([
            dcc.Upload(dbc.Button('Upload .csv'), id='csv-upload-button',),
        ],  style={'display': 'inline-block', 'float': 'right'}),
    ]),



    dcc.Input(id='login-user', type='text', placeholder='username'),
    dcc.Input(id='login-pass', type='password', placeholder='password'),
    dbc.Button('Update Database', id='mongo-update-button', n_clicks=0),

    # confirmation popup
    dcc.ConfirmDialog(
        id='update-confirm-box',
        message='Updated Confirmed',
    ),

    dcc.ConfirmDialog(
        id='validation-error'
    ),

    dcc.ConfirmDialog(
        id='validation-success',
        message='Validation Successful!\nUpload?'
    ),

    dcc.ConfirmDialog(
        id='incorrect-password',
        message='Incorrect password\nPlease check CaSe SenSitIve'
    ),

    # store initial dataframe in dcc.Store to compare usermade changes later
    dcc.Store(id='old-dataframe', data=mongo_initial_df.to_dict("records")),
    dcc.Store(id='valid-data', data=True),
], style={'padding':'10px'})

@callback(Output('incorrect-password', 'displayed'),
          State('login-user','value'),
          State('login-pass','value'),
          Input('mongo-update-button', 'n_clicks'),
          prevent_initial_call=True)
def login_fail(username, password, update):
    # if password fails alert user

    try:
        if checkpw(password.encode('utf-8'), USER_PW[username]) and update > 0:
            pass
        else:
            return True
    except:
        return True


# update user if validation fails
@callback([Output('validation-error', 'message'),
          Output('validation-error', 'displayed'),
          Output('validation-success', 'displayed')],

          Input('mongo-update-button', 'n_clicks'),

          State('editable-table', 'data'),
          State('old-dataframe', 'data'),
          State('login-user', 'value'),
          State('login-pass', 'value'),
          )
def validate_notification(clicks, edited_df, old_df, username, password):
    # run if password correct
    if checkpw(password.encode('utf-8'), USER_PW[username]):
        df_diff = id_df_change(old_df, edited_df)
        new_entry_ids = [_id['_id'] for _id in df_diff]
        edited_df = pd.DataFrame(edited_df)
        new_entries = edited_df[edited_df['_id'].isin(new_entry_ids)]

        validation = True

        if validation and clicks > 0:
            results = data_validation(new_entries)
            # if data is not valid alert the user and don't allow uploads
            if results is not True:
                return results, True, False
            else:
            # if the data is valid alert the user and allow uploads
                return 'Validation Successful!', False, True


# edit dataframe
@callback([Output('editable-table', 'data'),
           Output('editable-table', 'columns'),
           Output('editable-table', 'page_current'),
           Output('old-dataframe', 'data'),
           Output('update-confirm-box', 'displayed'), ],

          Input('collection-dropdown', 'value'),
          Input('add-row-button', 'n_clicks'),
          # Input('mongo-update-button', 'n_clicks'),
          Input('csv-upload-button', 'contents'),
          Input('csv-upload-button', 'filename'),
          Input('validation-success', 'submit_n_clicks'),

          State('editable-table', 'columns'),
          State('editable-table', 'page_size'),
          State('editable-table', 'data'),
          State('old-dataframe', 'data'),
          )
def build_dataframe(selected_collection, n_clicks, contents, filename, upload_submit,
                    columns, page_size, edited_df, old_df):
    # run if password correct

    # callback context
    trigger = ctx.triggered_id


    # if user uploads a csv dataframe
    if trigger == 'csv-upload-button':
        # convert upload to dataframe
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        csv_df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

        # remove _id column if applicable, then add new ObjectIds
        csv_df = csv_df.drop(['_id'], axis=1, errors='ignore')
        new_ids = [str(ObjectId()) for x in csv_df.index]

        csv_df['_id'] = new_ids

        # append dataframe to current collection
        combined_df = pd.concat([pd.DataFrame(edited_df), csv_df], ignore_index=True)

        last_page = (len(combined_df) + 1) // page_size + ((len(combined_df) + 1) % page_size > 0)

        # return new dataframe as editable_df+csv_df, columns, go to last page of new df, don't update old df, no notifcation box
        return combined_df.to_dict('records'), columns, last_page - 1, old_df, False

    # get number of pages from pagination
    last_page = (len(edited_df) + 1) // page_size + ((len(edited_df) + 1) % page_size > 0)

    # append new rows if add rows is clicked
    if trigger == 'add-row-button':
        edited_df.append({c['id']: str(ObjectId()) for c in columns})

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
    elif trigger == 'validation-success':
        # set new cursor to selected collection
        mongo_collection_cursor = mongo_connector.get_mongo_collection(selected_collection)

        if upload_submit > 0:

            # compare dataframes
            df_diff = id_df_change(old_df, edited_df)

            # get rows deleted, added, and updated
            df_diff_del = [ObjectId(diff['_id']) for diff in df_diff if diff['change_type'] == 'deleted']
            df_diff_add = [diff['_id'] for diff in df_diff if diff['change_type'] == 'added']
            df_diff_upd = [diff['_id'] for diff in df_diff if diff['change_type'] == 'updated']

            # execute deletion
            if len(df_diff_del) > 0:
                mongo_collection_cursor.delete_many({'_id': {'$in': df_diff_del}})

            # execute addition
            if len(df_diff_add) > 0:
                added_rows = [doc for doc in edited_df if doc['_id'] in df_diff_add]

                for doc in added_rows:
                    doc['_id'] = ObjectId(doc['_id'])

                mongo_collection_cursor.insert_many(added_rows)

            # execute updates
            if len(df_diff_upd) > 0:
                updated_rows = [doc for doc in edited_df if doc['_id'] in df_diff_upd]
                # remove
                updated_rows_noid = [{key: value for key, value in doc.items() if key != '_id'} for doc in updated_rows]

                bulk_operations = []
                for i, doc in enumerate(updated_rows):
                    bulk_operations.append(UpdateMany({'_id': ObjectId(doc['_id'])},
                                                      {'$set': updated_rows_noid[i]}))
                mongo_collection_cursor.bulk_write(bulk_operations)

            # return update notification, store edited df in dcc.Store
            return edited_df.to_dict('records'), columns, 0, edited_df.to_dict('records'), True


if __name__ == '__main__':
    app.run_server(debug=True)
