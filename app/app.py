from dash import Dash, dash_table, dcc, html, Input, Output, State, callback
from pymongo_get_db import get_database
import pandas as pd
from bson import ObjectId

app = Dash(__name__)
#TODO: Create
#TODO: Deletes
#TODO: Change between collections
#TODO: Searchable
#TODO: Upload CSV
#TODO: Verify user when changes are made
#TODO: Vizualize statistics
#TODO: Improve Aesthetics


#mongoDB
mongo_db = get_database('Covid19_Risk_Factors')
collection = mongo_db['Test']
df = pd.DataFrame(collection.find())
#covnvert object ID to string
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
        row_deletable=True
    ),
    html.Button('Add Row', id='add-row-button', n_clicks=0),
    html.Button('Update Database', id='mongo-update-button', n_clicks=0),

    #confirmation popup
    dcc.ConfirmDialog(
        id='update-confirm-box',
        message='Updated Confirmed',
    )
])

#add new rows
@callback(
    Output('editable-table', 'data'),
    Input('add-row-button', 'n_clicks'),
    State('editable-table', 'data'),
    State('editable-table', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

#TODO: should new columns be addable?

#update mongoDB
@callback(
    Output('update-confirm-box', 'displayed'),
    Input('mongo-update-button', 'n_clicks'),
    Input('editable-table', 'data'),
)
def update_mongo(click, rows):
    if click > 0:
        #TODO: also probably can make this not a for loop
        '''TODO: so what should happen is when the 'update' button is pressed 
        this method compares the difference between the the database from pymongo (old)
        and the current edited dataframe (new). Then any rows that have been edited it can update
        any rows deleted it can remove, and any rows added it can add. 
        '''
        for row in rows:
            #convert doc ID to an ObjectId
            doc_id = ObjectId(row['_id'])
            # remove string _id from row
            new_doc = {key: value for key, value in row.items() if key != '_id'}
            #update the document by the _id
            collection.update_one({'_id': doc_id}, {'$set': new_doc})

        return True

if __name__ == '__main__':
    app.run_server(debug=True)
