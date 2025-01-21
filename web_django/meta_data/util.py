import os
import sys
import time
import json
import requests
import numpy as np
import pandas as pd
from io import StringIO
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .models import StockMetaData

ROOT = Path(__file__).resolve().parent

def get_meta_data():
    if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
        return StockMetaData.objects.all()
    return []

def get_stocks():
    if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
        return [stock.__str__() for stock in StockMetaData.objects.all()]
    return []


def preprocess(x):
    return int(x.replace(',', ''))


def convert(x):
    if x == '--':
        return np.nan
    if type(x) == str:
        return x.replace(',', '')#float(x.replace(',', ''))
    else:
        return x

def download_meta_data():
    url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
    res = requests.get(url)
    df = pd.read_html(res.text)[0]
    df.columns = df.iloc[0]
    df = df.drop([0,1])
    df['code'] = df['有價證券代號及名稱'].apply(lambda x: x.split('\u3000')[0])
    return df

def download_stock_price(datestr):  # 下載某天股價
    r = requests.post(
        'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' +
        datestr + '&type=ALL')
    if len(r.text):
        df = pd.read_csv(StringIO(r.text.replace("=", "")),
                         header=["證券代號" in l
                                 for l in r.text.split("\n")].index(True) - 1)
        df = df[['證券代號', '開盤價', '最高價', '最低價', '收盤價', '成交股數', '本益比']]
        df.columns = ['code', 'Open', 'High', 'Low', 'Close', 'Volume', 'PE']
        df = df[df['code'].str.len() <= 4]
        # stock_codes = [c.split(' ')[0] for c in get_stocks()]
        # df = df[df['code'].isin(stock_codes)].reset_index(drop=True)
        df = df.reset_index(drop=True)
        converted_df = {}
        for col in df.columns:
            converted_df[col] = df[col].apply(convert)
        converted_df = pd.DataFrame(converted_df).dropna().reset_index(drop=True)
    else:
        print(datestr, 'no data')
        return

    date = datetime.strptime(datestr, '%Y%m%d')
    roc_year = date.year - 1911
    formatted_date = f"{roc_year}/{date.month:02d}/{date.day:02d}"

    url = f"https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes?l=zh-tw&d={formatted_date}&s=0,asc,0"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            df = df[['SecuritiesCompanyCode', 'Open', 'High', 'Low', 'Close', 'TradingShares']]
            df.columns = ['code', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[df['code'].str.len() <= 4]
            df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
            df['High'] = pd.to_numeric(df['High'], errors='coerce')
            df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            df['Volume'] = pd.to_numeric(df['Volume'].str.replace(',', ''), errors='coerce')
            df['PE'] = 0
            df = df.dropna().reset_index(drop=True)
            combined = pd.concat([converted_df, df], axis=0).reset_index(drop=True)
            return combined
        else:
            print(f"{datestr} no data")
            return None
    else:
        print(f"Request fail, statue code：{response.status_code}")
        return None

def download_institutional_investor(date):
    # 下載某天三大法人
    time.sleep(5)
    r = requests.get('https://www.twse.com.tw/rwd/zh/fund/T86?date=' +
                     date + '&selectType=ALL&response=csv')
    try:
        df = pd.read_csv(StringIO(r.text),
                         header=1).dropna(how='all', axis=1).dropna(how='any')
    except pd.errors.EmptyDataError:
        print(f'{date} no data')
        return
    except Exceptions as e:
        print(e)
        return
    #stock_codes = [c.split(' ')[0] for c in get_stocks()]
    #df = df[np.isin(df['證券代號'], stock_codes)].reset_index(drop=True)
    df = df.reset_index(drop=True)
    df['外資買進股數'] = df['外陸資買進股數(不含外資自營商)'].apply(preprocess)
    df['外資賣出股數'] = df['外陸資賣出股數(不含外資自營商)'].apply(preprocess)
    df['自營商買進股數'] = df['自營商買進股數(自行買賣)'].apply(
        preprocess) + df['自營商買進股數(避險)'].apply(preprocess)
    df['自營商賣出股數'] = df['自營商賣出股數(自行買賣)'].apply(
        preprocess) + df['自營商賣出股數(避險)'].apply(preprocess)
    df = df[[
        '證券代號', '外資買進股數', '外資賣出股數', '自營商買進股數', '自營商賣出股數', '投信買進股數', '投信賣出股數'
    ]]
    df['投信買進股數'] = df['投信買進股數'].apply(preprocess)
    df['投信賣出股數'] = df['投信賣出股數'].apply(preprocess)
    df.columns = [
        'code', 'foreign_buy', 'foreign_sell', 'dealer_buy', 'dealer_sell',
        'invest_buy', 'invest_sell'
    ]
    df = df[df['code'].str.len() <= 4]
    
    date_obj = datetime.strptime(date, '%Y%m%d')
    roc_year = date_obj.year - 1911
    formatted_date = f"{roc_year}/{date_obj.month:02d}/{date_obj.day:02d}"

    url = f"https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading?l=zh-tw&d={formatted_date}&s=0,asc,0"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            otc_df = pd.DataFrame(data)
            otc_df = otc_df[['SecuritiesCompanyCode', 'Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Total Buy', ' Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Total Sell', 'Dealers-TotalBuy', 'Dealers-TotalSell', 'SecuritiesInvestmentTrustCompanies-TotalBuy', 'SecuritiesInvestmentTrustCompanies-TotalSell']]
            otc_df.columns = ['code', 'foreign_buy', 'foreign_sell', 'dealer_buy', 'dealer_sell', 'invest_buy', 'invest_sell']
            otc_df = otc_df[otc_df['code'].str.len() <= 4]
            otc_df['foreign_buy'] = pd.to_numeric(otc_df['foreign_buy'], errors='coerce')
            otc_df['foreign_sell'] = pd.to_numeric(otc_df['foreign_sell'], errors='coerce')
            otc_df['dealer_buy'] = pd.to_numeric(otc_df['dealer_buy'], errors='coerce')
            otc_df['dealer_sell'] = pd.to_numeric(otc_df['dealer_sell'], errors='coerce')
            otc_df['invest_buy'] = pd.to_numeric(otc_df['invest_buy'], errors='coerce')
            otc_df['invest_sell'] = pd.to_numeric(otc_df['invest_sell'], errors='coerce')
            otc_df = otc_df.dropna().reset_index(drop=True)
            combined = pd.concat([df, otc_df], axis=0).reset_index(drop=True)
            return combined
    return None


def download_punishment(compare_date):
    # 查詢處置股票
    punished_file = f'{ROOT}/punished.csv'

    # Check if the file exists
    if os.path.exists(punished_file):
        modify_time = os.path.getmtime(punished_file)
        modify_time = time.strftime('%Y%m%d', time.localtime(modify_time))
        if modify_time == compare_date:  # If already checked today, skip 這天已經查過 不用再查了
            return
    else:
        modify_time = datetime.strftime(datetime.strptime(compare_date, '%Y%m%d'), '%Y%m%d')
        print(f"{punished_file} not found. Creating a new file.")
    end = datetime.strptime(compare_date, '%Y%m%d') + timedelta(days=1)
    end = datetime.strftime(end, '%Y%m%d')
    r = requests.post(
        f'https://www.twse.com.tw/announcement/punish?response=json&startDate={modify_time}&endDate={end}'
    )
    df = pd.DataFrame(json.loads(r.text)['data'])[[2, 6]]
    df.columns = ['code', 'duration']
    df.to_csv(f'{ROOT}/punished.csv', index=False)


def download_profile(stock_code):
    url = f'https://tw.stock.yahoo.com/quote/{stock_code}.TW/profile'
    res = requests.get(url)
    res.encoding = 'utf-8'
    table = soup.find('div', class_='table-grid row-fit-half')
    keys = [span.text for span in table.find_all('span', class_='')]
    values = [div.text for div in table.find_all('div', class_='Py(8px) Pstart(12px) Bxz(bb)')]
    data = {key: value for key, value in zip(keys, values)}
    return data

def download_new_listing(date):
    url = f'https://www.twse.com.tw/rwd/zh/company/newlisting?date={date}&response=json'
    res = requests.get(url)
    res.encoding = 'utf-8'
    data = json.loads(res.text)
    df = pd.DataFrame(data['data'], columns=data['fields'])[['公司代號', '公司簡稱', '股票上市買賣日期']]
    listed_date = []
    for date in df['股票上市買賣日期']:
        year, month, day = date.split('.')
        year = str(int(year) + 1911)
        listed_date.append('/'.join([year, month, date]))
    df['listed_date'] = pd.DataFrame(listed_date)
    meta_data = download_meta_data()[['code', '產業別']]
    meta_data = meta_data[meta_data['code'].isin(df['公司代號'])]
    df = df.merge(meta_data, left_on='公司代號', right_on='code')
    return df


def download_delisting(date):
    url = f'https://www.twse.com.tw/rwd/zh/company/suspendListing?date={date}&response=json'
    res = requests.get(url)
    res.encoding = 'utf-8'
    data = json.loads(res.text)
    df = pd.DataFrame(data['data'], columns=data['fields'])[['上市編號', '公司名稱', '終止上市日期']]
    return df

        
