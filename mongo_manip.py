import pandas as pd

def id_df_change(unedited_df, edited_df):
    changes = []

    # Create a dictionary for quick access to original data
    original_dict = {item['_id']: item for item in unedited_df}

    # Identify deletions
    deleted_ids = set(item['_id'] for item in unedited_df) - set(item['_id'] for item in edited_df)
    for _id in deleted_ids:
        changes.append({'_id': _id, 'change_type': 'deleted'})

    # Identify insertions and modifications
    for item in edited_df:
        _id = item['_id']
        original_item = original_dict.get(_id)

        if original_item is None:
            changes.append({'_id': _id, 'change_type': 'added'})
        elif item != original_item:
            changes.append({'_id': _id, 'change_type': 'updated'})

    return changes

