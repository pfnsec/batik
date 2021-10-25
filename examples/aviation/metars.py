
import requests
import pandas as pd
import io


metars_url = "https://www.aviationweather.gov/adds/dataserver_current/current/metars.cache.csv"

def fetch_metars_df():
    r = requests.get(metars_url)
    r = r.content
    r = r.decode('utf-8')
    rawData = pd.read_csv(io.StringIO(r), skiprows=5)

    print(rawData.columns)
    return rawData


print(fetch_metars_df().query("station_id == 'EGLL'"))
