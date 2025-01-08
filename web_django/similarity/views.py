import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from django.shortcuts import render
from django.http import HttpResponse

from meta_data.models import StockMetaData
from price.models import PriceData
from profit_loss.models import *
from asset_debt.models import *
from dividend.models import DividendData
# Create your views here.

from .util import create_dash

# 90 day price, today close, PE, PBR, EPS

root = str(Path(__file__).resolve().parent.parent) + '/meta_data'
#print(root)
correlation = None
file_path = f'{root}/daily_corr.csv'
if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
    if os.path.exists(file_path):
        correlation = pd.read_csv(file_path)
    else:
        print(f"{file_path} not found. Using empty DataFrame as fallback.")
        correlation = pd.DataFrame()
same_trade = []
meta_data = StockMetaData.objects.all()
price_data = PriceData.objects.all().order_by('date')
profit_loss_table_dict = {
    'holdings': HoldingsProfitLossData,
    'bank': BankProfitLossData,
    'insurance': InsuranceProfitLossData,
    'standard': StandardProfitLossData,
    'other': OtherProfitLossData
}


def get_same_trade(industry_type):
    global same_trade
    same_trade = StockMetaData.objects.filter(industry_type=industry_type)


def get_score(stock_code):
    df = correlation[['Unnamed: 0', stock_code]]
    df.columns = ['stock_id', 'corr']
    price = PriceData.objects.filter(code=stock_code).order_by('-date')[0]
    today = price.date
    print(today)
    close = price.Close
    volume = price.Volume
    price = [[row.code, row.Close, row.Volume]
             for row in PriceData.objects.filter(date=today)]
    price = pd.DataFrame(price, columns=['stock_id', 'close', 'volume'])
    df['stock_id'] = df['stock_id'].astype(str)
    price['stock_id'] = price['stock_id'].astype(str)
    df = df.merge(price, on='stock_id', how='left')
    df['close_sim'] = 1 - abs(np.log10(close) - np.log10(df['close']))
    df['volume_sim'] = 1 - abs(
        np.log(volume) / np.log(100) - np.log(df['volume']) / np.log(100))
    same_trade_id = [row.code for row in same_trade]
    same_trade_id = [row.code for row in same_trade]
    industry_sim = []
    for code in df['stock_id']:
        if str(code) in same_trade_id:
            industry_sim.append(1)
        else:
            industry_sim.append(0)
    df['industry_sim'] = pd.DataFrame(industry_sim)
    df['score'] = df['corr'] + df['close_sim'] + df['volume_sim'] + df[
        'industry_sim']
    #    df['score'] = df['corr'] + df['industry_sim']
    return df


def prepare_data(stock_code):
    df = get_score(stock_code)
    sorted_df = df.sort_values(by='score',
                               ascending=False).reset_index(drop=True)
    #    print(sorted_df)
    data = {}
    i = 0
    #    for i in sorted_df.index:
    while len(data) < 11:
        id_ = sorted_df.stock_id.iloc[i]
        print(i, id_)
        corr = sorted_df['corr'].iloc[i]
        score = sorted_df['score'].iloc[i]
        basic = StockMetaData.objects.filter(code=id_)[0]
        price = price_data.filter(code=id_).order_by('-date')
        company_type = basic.company_type
        if company_type == 'other':
            i += 1
            continue
        try:
#             EPS = profit_loss_table_dict[company_type].objects.filter(
#                 code=id_).order_by('-season')[0]
            for key in profit_loss_table_dict:
                EPS = profit_loss_table_dict[key].objects.filter(
                    code=id_).order_by('-season')
                if len(EPS) > 0:
                    break
            EPS = EPS[0]
#             if company_type in ['standard', 'other']:
#                 PBR = StandardAssetDebtData.objects.filter(code=id_)
#             else:
#                 PBR = NonStandardAssetDebtData.objects.filter(code=id_)
#             PBR = PBR.order_by('-season')[0]
            for sadd in [StandardAssetDebtData, NonStandardAssetDebtData]:
                PBR = sadd.objects.filter(code=id_)
                if len(PBR) > 0:
                    break
            PBR = PBR.order_by('-season')[0]
            dividend = DividendData.objects.filter(code=id_).order_by('-year')
            data[id_] = {
                'price': price,
                'corr': corr,
                'score': score,
                'basic': basic,
                'eps': EPS,
                'pbr': PBR,
                'dividend': dividend,
            }
        except Exception as e:
            print(e)
            print(id_, ' failed')
        i += 1

    return data


def main(request, stock_id):
    info = meta_data.filter(code=stock_id)[0]
    #    global industry_type
    #    industry_type = info.industry_type
    get_same_trade(info.industry_type)
    data = {}
    data['stock_id'] = f"{stock_id} {info.name}"
    data['stock_info'] = info
    data['listed_date'] = info.listed_date
    data['industry_type'] = info.industry_type
    data['same_trade'] = same_trade
    data['stock_list'] = meta_data
    data['same_trade'] = same_trade
    data_for_dash = prepare_data(stock_id)
    try:
        app = create_dash(stock_id, data_for_dash)
    except:
        return HttpResponse('此公司沒有相似性比較 :/')
    return render(request, 'similarity_dashboard.html', context=data)
