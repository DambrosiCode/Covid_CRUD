from dash import Dash, dash_table, dcc, ctx, html, Input, Output, State, callback
from pymongo_get_db import get_database
from mongo_manip import id_df_change
import pandas as pd
from bson import ObjectId
from pymongo import UpdateOne, UpdateMany

app = Dash(__name__)
# TODO: Don't allow editing of _id
# TODO: include input limiting
# TODO: Upload CSV
# TODO: refresh dataframe manually and/or intervally
# TODO: reset dataframe
# TODO: Serverside Caching (fine with small datasets but should be scaleable)
# TODO: Verify user when changes are made
# TODO: Vizualize statistics
# TODO: Improve Aesthetics
# TODO: Vizualize changes that have been made before update


# connect to mongoDB
mongo_db = get_database('Covid19_Risk_Factors')


class MongoDBConnector:
    def __init__(self, database = 'Covid19_Risk_Factors', default_collection_name = 'Test'):
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


#get mongo connection
mongo_connector = MongoDBConnector(default_collection_name='Test')
#dataframe at startup
mongo_initial_df = mongo_connector.get_mongo_as_df()
#collection cursor
mongo_collection_cursor = mongo_connector.get_mongo_collection()

app.layout = html.Div(children=[
    # datatable
    dash_table.DataTable(
        id='editable-table',
        columns=[
            {'name': col, 'id': col, 'deletable': False} for col in mongo_initial_df.columns  # TODO: custom columns
        ],
        data=mongo_initial_df.to_dict('records'),
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

    # confirmation popup
    dcc.ConfirmDialog(
        id='update-confirm-box',
        message='Updated Confirmed',
    ),

    # store initial dataframe in dcc.Store to compare usermade changes later
    dcc.Store(id='old-dataframe', data=mongo_initial_df.to_dict("records")),
    # dcc.Store(id='collection-id', data='Test')
])


# edit dataframe
@callback([Output('editable-table', 'data'),
           Output('editable-table', 'columns'),
           Output('editable-table', 'page_current'),
           Output('old-dataframe', 'data')],
          Input('collection-dropdown', 'value'),
          Input('add-row-button', 'n_clicks'),
          Input('editable-table', 'data'),
          State('editable-table', 'data'),
          State('editable-table', 'columns'),
          State('editable-table', 'page_size'),
          State('old-dataframe', 'data'))
def build_dataframe(selected_collection, n_clicks, edited_data_frame, rows, columns, page_size, old_dataframe):
    trigger = ctx.triggered_id

    # get number of pages from pagination
    last_page = len(edited_data_frame) // page_size + (len(edited_data_frame) % page_size > 0)

    # append new rows if add rows is clicked
    if trigger == 'add-row-button':
        rows.append({c['id']: str(ObjectId()) for c in columns})

        #add new row to editable dataframe, update columns, set start page to last page, keep dcc.Store dataframe to unupdated fd
        return rows, columns, last_page - 1, old_dataframe
    # switch to a new dataframe
    elif trigger == 'collection-dropdown':
        new_df = mongo_connector.get_mongo_as_df(selected_collection)

        # get columns
        columns = [
            {'name': col, 'id': col, 'deletable': False} for col in new_df.columns
        ]
        #change editable table to new collection, update columns, set start page, update dcc.Store dataframe to new collection
        return new_df.to_dict('records'), columns, 0, new_df.to_dict('records')


# TODO: should new columns be addable?

# update mongoDB
@callback(
    [Output('update-confirm-box', 'displayed'),
    Output('old-dataframe','data'),],
    Input('mongo-update-button', 'n_clicks'),
    State('editable-table', 'data'),
    State('old-dataframe', 'data')
)
def update_mongo(click, edited_df, old_df):
    if click > 0:
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
                bulk_operations.append(UpdateOne({'_id': ObjectId(doc['_id'])},
                                                 {'$set': updated_rows_noid[i]}))
            print(bulk_operations)
            mongo_collection_cursor.bulk_write(bulk_operations)

        #return update notification, store edited df in dcc.Store
        return True, edited_df


if __name__ == '__main__':
    app.run_server(debug=True)
