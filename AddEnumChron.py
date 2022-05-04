import pandas as pd
from pprint import pprint as pp
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

###################################################################
### Split the Description out to appropriate Enum/Chron columns ###
###################################################################
print("Doing the replacements . . .")
# Add the fields to be filled
df[['EnumA', 'EnumB', 'ChronI', 'ChronJ']] = None
# Create a dataframe to hold JUST records that get filled
filled = pd.DataFrame()
