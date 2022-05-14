import pandas as pd
from pprint import pprint as pp
import re
import Credentials      # Get API keys, etc.
pp()    # So linter thinks it's being used

apikey = Credentials.prod_api
baseurl = 'https://api-na.hosted.exlibrisgroup.com'
query_update_item = '/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}?apikey={apikey}'

### Get MMS/Holding/Item IDs, Descriptions, Locations from spreadsheet ###
print("Reading Excel file . . .")
df = pd.read_csv("FullItemList.csv", converters={'Item ID': str, 'Holdings ID': str, 'MMS ID': str})
# Pare it down to just the necessary columns
df = df[['MMS ID', 'Holdings ID', 'Item ID', 'Description', 'Permanent Location']]
# Strip leading/trailing space from Description
df.Description = df.Description.str.strip()
# Collapse multiple spaces within the Description
df.Description.replace(' +', ' ', regex=True, inplace=True)
# Remove spaces from column names
df.columns = [c.replace(' ', '_') for c in df.columns]

###################################################################
### Split the Description out to appropriate Enum/Chron columns ###
###################################################################
print("Doing the replacements . . .")
# Add columns for the Enum/Chron fields
EC_fields = ['Enum_A', 'Enum_B', 'Chron_I', 'Chron_J']
df[EC_fields] = None


def fill_and_extract(regex, these_fields):
    exp = re.compile(regex)
    for i, f in enumerate(these_fields):
        df[f] = df['Description'].str.extract(exp, expand=True)[i]


###     Here will be a list of steps to find & extract Enum/Chron info  ###
# Match descriptions with just volume & nothing else
fill_and_extract(r'^(v)\.(\d)+$', ['Enum_A', 'Enum_B'])

###     Once ALL those steps are done, pull those lines out to a new dataframe   ###
# Create a dataframe to hold JUST records that get filled
filled = pd.DataFrame()
# Populate the new dataframe with any records that now have Enum/Chron info
filled = df.dropna(subset=EC_fields, thresh=1)
# Purge records from the original dataframe if they are now in the new one
df = df.loc[~df['Item_ID'].isin(filled['Item_ID'])]
