import requests
import datetime
import os
import sys
import itertools
import json
import pathlib
import time

from retry import retry
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
MARKETAUX_API_TOKEN = os.environ['MARKETAUX_API_TOKEN']
INTERIM_DATA_FOLDER_PATH = pathlib.Path("./data/interim")

def extract_marketaux_news():
    # Load instances of reference data to continue mining
    with open(INTERIM_DATA_FOLDER_PATH.joinpath('latest_config.json'), "r") as f:
        last_config = json.load(f)
        
    reference_store, start_date = get_reference_to_fill()
    end_date = datetime.datetime(2023, 12, 31)
    date_range = [(start_date + datetime.timedelta(days=x)).strftime("%Y-%m-%d") for x in range(1, (end_date - start_date).days)]

    configs = (x for l in [
        [entry for entry in itertools.product(reference_store.keys(),
                                            reference_store[etf].keys(),
                                            date_range) if (entry[1] in reference_store[entry[0]].keys())
            ] for etf in reference_store.keys()] for x in l)

    for etf_symbol, company_symbol, date in configs:
        try:
            response_dict = get_marketaux_news(company_symbol, date)
            time.sleep(2)
        except Exception:
            print("Connection error, skipping entry")
            continue
        
        if response_dict == 1:
            print("No API calls left.")
            return  reference_store, last_config
            
        if (response_dict is None) or (response_dict['meta']['found'] == 0):
            continue
        
        response_metadata = response_dict['meta']
        response_data = list(response_dict['data'])
        # total_found = response_metadata['found']
        # limit = response_metadata['limit']
        # required_calls = total_found // limit + min(1, total_found % limit)
        # for page in range(2, required_calls + 1):
        #     try:
        #         response_dict = get_marketaux_news(company_symbol, date, page)
        #         time.sleep(2)
        #     except Exception:
        #         print("Connection error, skipping entry")
        #         continue
            
        #     if response_dict == 1:
        #         print("No API calls left.")
        #         return reference_store, last_config
            
        #     if (response_dict is None) or (response_dict['meta']['found'] == 0):
        #         continue
            
        #     response_metadata = response_dict['meta']
        #     response_data = list(response_dict['data'])
        #     response_data.append(list(response_data))
        
        reference_store[etf_symbol][company_symbol].update({date: response_data})
        last_config = {
            'etf': etf_symbol,
            'company': company_symbol,
            'date': date,
            'metadata': response_metadata,
        }
    
    return reference_store, last_config
    

@retry(ConnectionError, delay=60, tries=3)
def get_marketaux_news(symbol, date, page=1):
    endpoint = "https://api.marketaux.com/v1/news/all"
    payload = {
            "meta": 'true',
            "symbols": symbol,
            "filter_entities": 'true',
            "must_have_entities": "true",
            "language": 'en',
            "page": page,
            "published_on": date,
            "api_token": MARKETAUX_API_TOKEN,
            }
    r = requests.request(method='GET', url=endpoint, params=payload)
    if r.status_code in (400, 401, 403, 404):
        print("Unable to complete opperation with the current inputs")
        return
    elif r.status_code == 402:
        print("API limit reached")
        return 1
    elif r.status_code in (429, 500, 503):
        print("Error encountered while processing the request.")
        return 

    return r.json()

def get_reference_to_fill():
    with open(INTERIM_DATA_FOLDER_PATH.joinpath('reference_store.json'), "r") as f:
        reference_store = json.load(f)

    with open(INTERIM_DATA_FOLDER_PATH.joinpath('latest_config.json'), "r") as f:
        last_config = json.load(f)
        
    last_date = datetime.datetime.strptime((last_config['date']), '%Y-%m-%d')
    end_date = datetime.datetime(2023, 12, 31)
    last_etf = last_config['etf']
    listed_etfs = list(reference_store.keys())
    last_company = last_config['company']
    listed_companies = list(reference_store[last_etf].keys())

    reached_last_date = last_date == end_date
    reached_last_company = listed_companies.index(last_company) + 1 == len(listed_companies)
    reached_last_etf = listed_etfs.index(last_etf) + 1 == len(listed_etfs)

    # End of the reference store
    if reached_last_date and reached_last_company and reached_last_etf:
        start_date = datetime.datetime(2021, 1, 1)
        return reference_store, start_date

    start_date = last_date
    for etf in listed_etfs[:listed_etfs.index(last_etf)]:
        reference_store.pop(etf)

    for company in listed_companies[: listed_companies.index(last_company)]:
        reference_store[last_etf].pop(company)

    for date in list(reference_store[last_etf][last_company].keys()):
        reference_store[last_etf][last_company].pop(date)
        if datetime.datetime.strptime(date, '%Y-%m-%d') == last_date:
            break
        
    return reference_store, start_date

if __name__ == "__main__":
    print("Extracting data...")
    marketaux_response = extract_marketaux_news()
    if marketaux_response is None:
        sys.exit("No data returned")
    
    latest_reference_store, last_config = marketaux_response
    with open(INTERIM_DATA_FOLDER_PATH.joinpath('reference_store.json'), "r") as f:
        reference_store = json.load(f)
    
    print("Updating reference store...")
    for etf, company_dict in latest_reference_store.items():
        for company, news_dict in company_dict.items():
            reference_store[etf][company].update(news_dict)
    
    print("Writing new info...")
    with open(INTERIM_DATA_FOLDER_PATH.joinpath('reference_store.json'), "w") as f:
        json.dump(reference_store, f)

    with open(INTERIM_DATA_FOLDER_PATH.joinpath('latest_config.json'), "w") as f:
        json.dump(last_config, f)

    print("Reference files written.")