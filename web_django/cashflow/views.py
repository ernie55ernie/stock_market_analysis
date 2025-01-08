from django.shortcuts import render
from django.http import HttpResponse
from dashboard_utils.common_functions import *
from .models import CashflowData
from meta_data.models import StockMetaData
from .util import create_dash

# Create your views here.
meta_data = StockMetaData.objects.all()

def get_raw_data(stock_id):
    table = CashflowData.objects.filter(code=stock_id)
    return create_df(table)


def main(request, stock_id):
    info = meta_data.filter(code=stock_id)[0]
    same_trade = meta_data.filter(industry_type=info.industry_type)
    try:
        df = get_raw_data(stock_id).astype(float)
    except:
        return HttpResponse('此公司在公開資訊觀測站上沒有現金流量表資料 :/')
    df = transform_by_season(df)
    #    listed_year = int(info.listed_date[0:4]) - 1911
    #    if listed_year >= int(df.iloc[0]['season'][0:3]):  # 上市日期早於最早紀錄的那年
    #        listed_year = f"{listed_year}_1"
    #        df = df[df.season >= listed_year]
    print(df)
    app = create_dash(df)
    data = {}
    data['stock_id'] = f"{stock_id} {info.name}"
    data['listed_date'] = info.listed_date
    data['industry_type'] = info.industry_type
    data['same_trade'] = same_trade
    data['stock_list'] = meta_data
    data['stock_info'] = info
    return render(request, 'cashflow_dashboard.html', context=data)
