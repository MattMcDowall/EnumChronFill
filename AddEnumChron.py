import Credentials      # Get API keys, etc.
import pandas as pd
from pprint import pprint as pp

pp()    # So linter thinks it's being used

apikey = Credentials.apikey

baseurl = 'https://api-na.hosted.exlibrisgroup.com'
queryUpdateItem = '/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items/{item_pid}?apikey={apikey}'

### Get MMS/Holding/Item IDs, Descriptions, Locations from spreadsheet ###
print("Reading Excel file . . .")
df = pd.read_csv("FullItemList.csv", converters={'Item ID': str})
