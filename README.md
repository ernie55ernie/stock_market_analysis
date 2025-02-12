# stock_market_analysis

A UI to present stock data of listed market

### data

1. profit loss:

- 一般公司：
  - 營業收入 = 營業成本 + 營業毛利
  - 營業利益 = 營業收入 - 營業成本 - 營業費用
  - (稅前)淨利 = 營業收入 - 營業成本 - 營業費用 + 營業外收入及支出
  - 本期淨利 = 稅後淨利
  - 毛利率 ＝營業毛利/營業收入
- 銀行：
  - 營業收入 = 利息淨收益＋利息以外淨損益
  - 淨損 ＝營業收入 - 呆帳費用 - 營業費用
  - 沒有毛利
- 金控：
  - 營業收入＝淨收益 ＝利息淨收益＋利息以外淨收益
  - 沒有毛利
- 壽險:
  - 營業利益＝營業收入 - 營業成本 - 營業費用
  - 毛利率 ＝（營業收入-營業成本）/營業收入
- 其他：（可放棄）
  - 淨損 ＝ 收入 - 支出

2. cashflow table:

- 自由現金流: 營業淨現金流-資本支出（取得不動產）
- 淨現金流: 營業淨現金流-投資淨現金流+籌資淨現金流

3. asset debt:

- 權益總額 = 資產總額 - 負債總額

4. ROE (股東權益報酬）= 稅後淨利/權益總額

### django

1. start project: `django-admin startproject <project name>`

2. start app: `python3 manage.py startapp <app name>`

3. create table in database:

- in `<app name>/models.py`
  - `class <table name>`:
  - set class attributes as table columns
- in `<project name>/settings.py` in `INSTALLED_APPS`, add `<app name>.apps.<app name>Config`
- `python3 manage.py makemigrations`
- `python3 manage.py migrate`

4. check table: `sqlite3 db.sqlite3`, `.tables`

5. use django's database API: `python3 manage.py shell`

- interact with table: `from <app name>.models import <table name>`
- add data: `data = <table name>(....)`, `data.save()`
- fetch all data: `<table name>.objects.all()`, return is a query set
- query data by condition: `<table name>.objects.filter(<column name> = ...>`
- sort data: `<table name>.objects.order_by(<column name>)`(add '-' for decending)
- distinct: `<table name>.objects.values(<column name>).distinct()`

### misc

1. download data to data_samples
`code/acknowledgement.ipynb`

2. sqlite migration
`python manage.py makemigrations meta_data`
`python manage.py makemigrations price`
`python manage.py makemigrations monthly_revenue`
`python manage.py makemigrations dividend`
`python manage.py makemigrations asset_debt`
`python manage.py makemigrations cashflow`
`python manage.py makemigrations profit_loss`
create sqlite database
`python manage.py migrate`

3. import csv to sqlite
```
sqlite3 db.sqlite3
.mode csv
.import -skip 1 stock_market_analysis/data_sample/stock_meta_data.csv(absolute path) meta_data_stockmetadata
.quit
```

4. 
```
python manage.py shell
from monthly_revenue.update_db import main
main(102, 1)~main(103, 11)
```

```
from profit_loss.update_db import main
main('add_data', 102, 1)~main('add_data', 103, 4)
```

```
from asset_debt.update_db import main
main('add_data', 102, 1)~main('add_data', 103, 4)
```

```
from cashflow.update_db import main
main('add_data', 103, 1)~main('add_data', 103, 4)
```

```
from dividend.update_db import main
main()
```

5.
```
python manage.py runserver ip:port
```

### Todo

metadata company_type download_new_listing delete_delisting
profit_loss 損益表
asset_debt 資產負債表
cashflow 現金流量表
similarity 相似性比較