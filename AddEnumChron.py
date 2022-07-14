from datetime import datetime
from os.path import exists as file_exists
import pandas as pd
import re
import requests
from time import sleep
import xmltodict
import Credentials      # Get API keys, etc.

apikey = Credentials.prod_api
baseurl = 'https://api-na.hosted.exlibrisgroup.com'
item_query = '/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}?apikey={apikey}'

exported_csv = "FullItemList.csv"
filled_csv = "FilledEnumChron.csv"
err_log_txt = "log.txt"

### Get MMS/Holding/Item IDs, Descriptions, Locations from spreadsheet ###
print("Reading Excel file . . .")
# Depending on how the file was exported, column names may or may have either spaces or underscores
df = pd.read_csv(exported_csv, dtype=str)
# Remove spaces from column names
df.columns = [c.replace(' ', '_') for c in df.columns]
# Rename 'Location' column
df = df.rename(columns={'Permanent_Location': 'Location'})
# Strip leading/trailing space from Description
df.Description = df.Description.str.strip()
# Collapse multiple spaces within the Description
df.Description.replace(' +', ' ', regex=True, inplace=True)

###################################################################
### Split the Description out to appropriate Enum/Chron columns ###
###################################################################
print("Doing the replacements . . .")
# Add columns for the Enum/Chron fields
EC_fields = ['Enum_A', 'Enum_B', 'Enum_C', 'Chron_I', 'Chron_J']
df[EC_fields] = None


def fill_and_extract(regex, these_fields):
    exp = re.compile(regex, re.IGNORECASE)
    for i, f in enumerate(these_fields):
        df[f] = df['Description'].str.extract(exp, expand=True)[i].fillna(df[f])


###     Here will be a list of steps to find & extract Enum/Chron info  ###

# Set some common expressions that can be used in a modular way
# Month/season
mmmRE = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|Spr(?:ing)?|Sum(?:mer)?|Fall?|Aut(?:umn)?|Win(?:ter)?)'
# Month + date(s)
mmm_ddRE = mmmRE + r'(?: \d{1,2}(?:[\-\/]\d{1,2})?)?'
# 4-digit year (post-18th-century)
yyyyRE = r'(?:1[89]|20)\d{2}'
# 4-digit year leading to a range
yyyy_yyRE = r'(?:1[89]|20)\d{2}-(?:\d{2}|\d{4})'

# Just volume(s) & nothing else
fill_and_extract(r'^v\. ?(\d+[a-z]?(?:[\&\-]\d+)?)$',
    ['Enum_A'])
# Volume + issue
fill_and_extract(r'^v\. ?(\d+)[ \/]no\. ?(\d+)$',
    ['Enum_A', 'Enum_B'])
# Vol + issue + date + year
fill_and_extract(r'^v\. ?(\d+)[ \/]no\. ?(\d+) (' + mmm_ddRE + r'),? (' + yyyyRE + ')$',
    ['Enum_A', 'Enum_B', 'Chron_J', 'Chron_I'])
# Volume + year(s)
fill_and_extract(r'^v\. ?(\d+) +(\(?' + yyyy_yyRE + r'\)?)$',
    ['Enum_A', 'Chron_I'])
# Just issue
fill_and_extract(r'^no\. ?(\d+)$',
    ['Enum_B'])
# Issue + year(s)
fill_and_extract(r'^no\. ?(\d+) (' + yyyy_yyRE + r')$',
    ['Enum_B', 'Chron_I'])
# Just part(s) & nothing else
fill_and_extract(r'^pt\. ?(\d+[a-z]?(?:[\&\-]\d+)?)$',
    ['Enum_C'])
# Range of dates within one calendar year
fill_and_extract(r'^(' + mmm_ddRE + r'[\-\/]' + mmm_ddRE + '), (' + yyyyRE + ')$',
    ['Chron_J', 'Chron_I'])
# Date(s) + year
fill_and_extract(r'^(' + mmm_ddRE + '),? (' + yyyyRE + ')$',
    ['Chron_J', 'Chron_I'])
# Just year(s)
fill_and_extract(r'^(' + yyyy_yyRE + r')$',
    ['Chron_I'])
# Year(s) + volume(s)
fill_and_extract(r'^(' + yyyy_yyRE + r') v\. ?(\d+(?:[\-\/]\d+)?)$',
    ['Chron_I', 'Enum_A'])
# Year(s) + part(s)
fill_and_extract(r'^(' + yyyy_yyRE + r') pt\. ?(\d+(?:[\-\/]\d+)?)$',
    ['Chron_I', 'Enum_C'])
# Year + month/season/date
fill_and_extract(r'^(' + yyyyRE + r') (' + mmm_ddRE + r')$',
    ['Chron_I', 'Chron_J'])
###


###     Once ALL those steps are done, pull those lines out to a new dataframe   ###
# Create a dataframe to hold JUST records that get filled
filled = pd.DataFrame()
# Populate the new dataframe with any records that now have Enum/Chron info
filled = df.dropna(subset=EC_fields, thresh=1)

# Make the updates via API
print("Applying the changes . . .")

records = len(filled)
c = 0
needs_header = not file_exists(filled_csv)    # Apparently we're creating the file, so it needs a header

with open(err_log_txt, 'a') as err_log:
    for index, row in filled.fillna('').iterrows():
        c += 1
        r = requests.get(''.join([baseurl,
                                  item_query.format(mms_id=str(row['MMS_ID']),
                                                    holding_id=str(row['Holdings_ID']),
                                                    item_pid=str(row['Item_ID']),
                                                    apikey=apikey)]))
        rdict = xmltodict.parse(r.text)
        if (c % (records / 100) < 1):
            print(int(100 * c / records), '% complete', sep='')  # , end='\r')
            sleep(5)
        if r.status_code == 429:  # Too many requests--daily limit
            print()
            print('Reached API request limit for today. Stopping execution.')
            print()
            # Drop this record & everything after from "filled"
            filled = filled.iloc[:c - 1]
            break
        if r.status_code != 200:
            e = xmltodict.parse(r._content)
            # Log the error
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  ' Error FETCHING item ', row['Item_ID'], ': (', r.status_code, ') ',
                  e['web_service_result']['errorList']['error']['errorMessage'],
                  sep='',
                  file=err_log)
            # Remove this item from the "filled" df
            filled = filled.drop([index])
            print(c, ' / '.join([row['MMS_ID'], row['Holdings_ID'], row['Item_ID']]), "Retrieval error logged", sep="\t")
            continue

        # Merge derived values into the retrieved data (rdict)
        rdict['item']['item_data']['enumeration_a'] = str(row['Enum_A'])
        rdict['item']['item_data']['enumeration_b'] = str(row['Enum_B'])
        rdict['item']['item_data']['enumeration_c'] = str(row['Enum_C'])
        rdict['item']['item_data']['chronology_i'] = str(row['Chron_I'])
        rdict['item']['item_data']['chronology_j'] = str(row['Chron_J'])
        # Set an internal note, if there's an empty one available
        if ('Enum/Chron derived from Description' not in rdict['item']['item_data'].values()):
            if (not rdict['item']['item_data']['internal_note_1']):
                rdict['item']['item_data']['internal_note_1'] = 'Enum/Chron derived from Description'
            elif (not rdict['item']['item_data']['internal_note_2']):
                rdict['item']['item_data']['internal_note_2'] = 'Enum/Chron derived from Description'
            elif (not rdict['item']['item_data']['internal_note_3']):
                rdict['item']['item_data']['internal_note_3'] = 'Enum/Chron derived from Description'
            else:  # Nbd, just log it
                print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ' No internal note available for item MMS ID ',
                    str(row['MMS_ID']), sep="", file=err_log)

        # Push the altered record back into Alma
        pxml = xmltodict.unparse(rdict)
        p = requests.put(''.join([baseurl,
                                  item_query.format(mms_id=row['MMS_ID'],
                                                    holding_id=row['Holdings_ID'],
                                                    item_pid=row['Item_ID'],
                                                    apikey=apikey)]),
                         data=pxml.encode('utf-8'), headers={'Content-Type': 'application/xml'})
        if r.status_code == 429:  # Too many requests--daily limit
            print()
            print('Reached API request limit for today. Stopping execution.')
            print()
            # Drop this record & everything after from "filled"
            filled = filled.iloc[:c - 1]
            break
        if p.status_code != 200:
            e = xmltodict.parse(p._content)
            # Log the error
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ' Error UPDATING item ', row['Item_ID'], ': (', p.status_code, ') ',
                e['web_service_result']['errorList']['error']['errorMessage'],
                sep='', file=err_log)
            # Remove this item from the "filled" df
            filled = filled.drop([index])
            print(c, ' / '.join([row['MMS_ID'], row['Holdings_ID'], row['Item_ID']]), "Record update error logged", sep="\t")
            continue
        print(c, ' / '.join([row['MMS_ID'], row['Holdings_ID'], row['Item_ID']]),
              row['Description'],
              ' | '.join(x or '' for x in [row['Enum_A'], row['Enum_B'], row['Enum_C'], row['Chron_I'], row['Chron_J']]),
              sep="\t")

        # Log it to the CSV
        #    Btw, the 'to_frame().T' transposes it, so it all goes in as a single comma-separated row
        row.to_frame().T.to_csv(filled_csv, mode='a', index=False, header=needs_header)
        needs_header = False  # Henceforth

# Purge filled records from the original df
df = df.loc[~df['Item_ID'].isin(filled['Item_ID'])]
# Re-create the original CSV from that df
df.to_csv(exported_csv, index=False)  # By default, will overwrite
