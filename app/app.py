from dash import Dash, dash_table, dcc, ctx, html, Input, Output, State, callback
from pymongo_get_db import get_database
from mongo_manip import id_df_change
import pandas as pd
from bson import ObjectId
from pymongo import UpdateOne, UpdateMany

app = Dash(__name__)
#TODO: Searchable
#TODO: Don't allow editing of _id
#TODO: include input limiting
#TODO: Upload CSV
#TODO: refresh dataframe manually and/or intervally
#TODO: reset dataframe
#TODO: Serverside Caching (fine with small datasets but should be scaleable)
#TODO: Verify user when changes are made
#TODO: Vizualize statistics
#TODO: Improve Aesthetics
#TODO: Vizualize changes that have been made before update


# get data from mongoDB return as dataframe
#TODO: delete this and replace it
mongo_db = get_database('Covid19_Risk_Factors')
collection = mongo_db['Test']
df = pd.DataFrame(collection.find())
# covnvert object ID to string
df['_id'] = df['_id'].astype(str)
print('========')

app.layout = html.Div(children=[
    #datatable
    dash_table.DataTable(
        id='editable-table',
        columns=[
            {'name': col, 'id': col, 'deletable':False} for col in df.columns
        ],
        data=df.to_dict('records'),
        editable=True,
        row_deletable=True,
        filter_action='native',
        sort_action='native',
        page_action='native',
        page_current=0,
        page_size=10,
    ),
    html.Button('Add Row', id='add-row-button', n_clicks=0),
    html.Button('Update Database', id='mongo-update-button', n_clicks=0),
    dcc.Dropdown(id='collection-dropdown', options=sorted(mongo_db.collection_names()), value='Test'),

    #confirmation popup
    dcc.ConfirmDialog(
        id='update-confirm-box',
        message='Updated Confirmed',
    ),

    #store initial dataframe in dcc.Store to compare usermade changes later
    dcc.Store(id='original-dataframe', data=df.to_dict("records")),
    #dcc.Store(id='collection-id', data='Test')
])

#edit dataframe
@callback([Output('editable-table', 'data'),
           Output('editable-table','columns'),
           Output('editable-table', 'page_current'),],
          Input('collection-dropdown', 'value'),
          Input('add-row-button', 'n_clicks'),
          Input('editable-table', 'data'),
          State('editable-table', 'data'),
          State('editable-table', 'columns'),
          State('editable-table', 'page_size'))
def build_dataframe(selected_collection, n_clicks, data_frame, rows, columns, page_size):
    trigger = ctx.triggered_id


    #get number of pages from pagination
    last_page = len(data_frame) // page_size + (len(data_frame) % page_size > 0)

    #append new rows if add rows is clicked
    if trigger == 'add-row-button':
        rows.append({c['id']: str(ObjectId()) for c in columns})



        return rows, None, last_page-1
    #switch to a new dataframe
    elif trigger == 'collection-dropdown':
        # get data from mongoDB return as dataframe
        mongo_db = get_database('Covid19_Risk_Factors')
        collection = mongo_db[selected_collection]
        df = pd.DataFrame(collection.find())
        # covnvert object ID to string
        df['_id'] = df['_id'].astype(str)

        #get columns
        columns=[
            {'name': col, 'id': col, 'deletable':False} for col in df.columns
        ]

        return df.to_dict('records'), columns, 0


#TODO: should new columns be addable?

#update mongoDB
@callback(
    Output('update-confirm-box', 'displayed'), #TODO: output change dcc.store
    Input('mongo-update-button', 'n_clicks'),
    State('editable-table', 'data'),
    State('original-dataframe', 'data')
)
def update_mongo(click, edited_df, unedited_df):
    if click > 0:
        #compare dataframes
        df_diff = id_df_change(unedited_df, edited_df)
        #get rows deleted, added, and updated
        df_diff_del = [ObjectId(diff['_id']) for diff in df_diff if diff['change_type'] == 'deleted']
        df_diff_add = [diff['_id'] for diff in df_diff if diff['change_type'] == 'added']
        df_diff_upd = [diff['_id'] for diff in df_diff if diff['change_type'] == 'updated']
        #execute deletion
        if len(df_diff_del) > 0:
            collection.delete_many({'_id':{'$in':df_diff_del}})

        #execute addition
        if len(df_diff_add) > 0:
            added_rows = [doc for doc in edited_df if doc['_id'] in df_diff_add]

            for doc in added_rows:
                doc['_id'] = ObjectId(doc['_id'])

            collection.insert_many(added_rows)

        #execute updates
        if len(df_diff_upd) > 0:
            updated_rows = [doc for doc in edited_df if doc['_id'] in df_diff_upd]
            #remove
            updated_rows_noid = [{key: value for key, value in doc.items() if key != '_id'} for doc in updated_rows]

            bulk_operations = []
            for i,doc in enumerate(updated_rows):
                bulk_operations.append(UpdateOne({'_id': ObjectId(doc['_id'])},
                                                 {'$set':updated_rows_noid[i]}))
            print(bulk_operations)
            collection.bulk_write(bulk_operations)

        return True

if __name__ == '__main__':
    app.run_server(debug=True)
