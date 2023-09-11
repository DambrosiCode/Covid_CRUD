import pandas as pd
import re
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


# Ensure that data is in a valid format for each row before uploading
def data_validation(df):
    errors = []

    # validation schema
    date_r = r'^\d{4}-\d{2}-\d{2}$'
    link_r = r'^http.*$'
    Sample_Size_r = int
    Critical_only_r = ['Y', 'N', '']
    Discharged_vs_death_r = ['Y', 'N', '']

    for index in df['_id']:
        row = df[df['_id']==index]
        # validate date
        if re.match(date_r, str(row['Date'].values[0])) is None:
            errors.append('index: ' + str(index) + " Date: YYYY-MM-dd")

        # validate Study Link
        if re.match(link_r, str(row['Study_Link'].values[0])) is None:
            errors.append('index: ' + str(index) + ' Study Link: http(s) link')

        # validate Sample Size as int
        try:
            int(row['Sample_Size'].values[0])
        except ValueError:
            errors.append('index: ' + str(index) + ' Sample Size: int')
        except TypeError:
            errors.append('index: ' + str(index) + ' Sample Size: int')

            # validate Critical Only
        if str(row['Critical_only'].values[0]) not in Critical_only_r:
            errors.append('index: ' + str(index) + ' Critical Only: "Y/N/''"')

            # validate Discharged vs death
        if str(row['Discharged_vs._death?'].values[0]) not in Discharged_vs_death_r:
            errors.append('index: ' + str(index) + ' Discharged_vs._death?: "Y/N/''"')

    if len(errors) > 0:
        return "\n".join(errors)
    else:
        return True
