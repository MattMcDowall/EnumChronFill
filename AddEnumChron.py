import pandas as pd
from pprint import pprint as pp
import re
import Credentials      # Get API keys, etc.
pp()    # So linter thinks it's being used

apikey = Credentials.apikey

baseurl = 'https://api-na.hosted.exlibrisgroup.com'
queryUpdateItem = '/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}?apikey={apikey}'

### Get MMS/Holding/Item IDs, Descriptions, Locations from spreadsheet ###
print("Reading Excel file . . .")
df = pd.read_csv("FullItemList.csv", converters={'Item ID': str, 'Holdings ID': str, 'MMS ID': str})
# Strip it down to just the necessary columns
df = df[['MMS ID', 'Holdings ID', 'Item ID', 'Description', 'Permanent Location']]
# Remove leading/trailing space from Description
df.Description = df.Description.str.strip()
# Collapse multiple spaces within the Description
df.Description.replace(' +', ' ', regex=True, inplace=True)
# Remove spaces from column names
df.columns = [c.replace(' ', '') for c in df.columns]

###################################################################
### Split the Description out to appropriate Enum/Chron columns ###
###################################################################
print("Doing the replacements . . .")
# Add the fields to be filled
fields = ['EnumA', 'EnumB', 'ChronI', 'ChronJ']
df[fields] = None


def fillAndExtract(regex, fields):
    exp = re.compile(regex)
    for i, f in enumerate(fields):
        df[f] = df['Description'].str.extract(exp, expand=True)[i]


###     Here will be a list of steps to find & extract Enum/Chron info  ###
# Match descriptions with just volume & nothing else
fillAndExtract(r'^(v)\.(\d)+$', ['EnumA', 'EnumB'])

###     Once ALL those steps are done, pull those lines out to a new dataframe   ###
# Create a dataframe to hold JUST records that get filled
filled = pd.DataFrame()
# Populate the new dataframe with any records that now have Enum/Chron info
filled = df.dropna(subset=fields, thresh=1)
# Purge records from the original dataframe if they are now in the new one
df = df.loc[~df['ItemID'].isin(filled['ItemID'])]
