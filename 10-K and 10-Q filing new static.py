import requests
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime

CIK_List = ['0001678124', '0001803498', '0001842754', '0001736035', '0001061630']

df_raw_data = []
for cik in CIK_List:
    header = {
        'Accept':'*/*',
        'Accept-Encoding':'gzip, deflate, br, zstd',
        'Accept-Language':'en-US,en;q=0.9',
        'Cache-Control':'no-cache',
        'Origin':'https://www.sec.gov',
        'Pragma':'no-cache',
        'Priority':'u=1, i',
        'Referer':'https://www.sec.gov/',
        'Sec-Ch-Ua':'"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'Sec-Ch-Ua-Mobile':'?0',
        'Sec-Ch-Ua-Platform':'"Windows"',
        'Sec-Fetch-Dest':'empty',
        'Sec-Fetch-Mode':'cors',
        'Sec-Fetch-Site':'same-site',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    resp = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json', headers=header)
    try:
        data = resp.json()['facts']['us-gaap']
        data2 = resp.json()
    except:continue
    for fact, details in data.items():
        for unit in details["units"]:
            for item in details["units"][unit]:
                row = item.copy()
                row["fact"] = fact
                row["FactID"] = details['label']
                row['Measure'] = unit
                row['Scale'] = 'Thousand'
                row['Decimals'] = 'Thousand'
                row['ValueType'] = 'Num'
                row['CIK'] = cik
                row['FundID'] = data2['entityName']
                row['FactTag'] = 'us-gaap:'+ fact
                df_raw_data.append(row)

def get_quarter_dates(year):
    quarters = {
        'Q1': str(datetime(year, 3, 31).strftime('%Y-%m-%d')),
        'Q2': str(datetime(year, 6, 30).strftime('%Y-%m-%d')),
        'Q3': str(datetime(year, 9, 30).strftime('%Y-%m-%d')),
        'FY': str(datetime(year, 12, 31).strftime('%Y-%m-%d')),
    }
    return quarters

df_data = []
for i in df_raw_data:
    end = i['end']
    year = end.split('-')[0]
    fp = i['fp']
    quarter_dates = get_quarter_dates(int(year))
    if quarter_dates[fp] == end:
        df_data.append(i)

df = pd.DataFrame(df_data)
df.rename(columns={'val': 'ValueNum','form':'FormCode', 'fy':'PeriodFY','fp':'PeriodFP','end':'reportDate','start':'StartDate', 'filed':'filingDate'}, inplace=True)
df['ValueNum'] = df['ValueNum']/1000
df['filingDate'] = pd.to_datetime(df['filingDate'], format='%Y-%m-%d')
df = df[df['filingDate'] > '2019-01-01']
df = df[df['filingDate'] <= '2024-07-12']
df['Period'] = pd.to_datetime(df['reportDate'], format='%Y-%m-%d')
# df = df[df['Period'] > '2019-01-01']
df['Period'] = df['Period'].dt.strftime('%m/%d/%Y')
df['reportDate'] = pd.to_datetime(df['reportDate'])
df['reportDate'] = df['reportDate'].dt.strftime('%m/%d/%Y')
df['StartDate'] = pd.to_datetime(df['StartDate'])
df['StartDate'] = df['StartDate'].dt.strftime('%m/%d/%Y')
df['EndDate'] = pd.to_datetime(df['reportDate'])
df['EndDate'] = df['EndDate'].dt.strftime('%m/%d/%Y')
df = df.drop_duplicates(subset=["FactID", "Period", "ValueNum","PeriodFP"])
df = df.sort_values(by=['CIK','reportDate','PeriodFY','PeriodFP'],ascending=False)
df = df[['CIK','FundID','FactID','FactTag','Measure','Scale','Decimals','ValueType','ValueNum','FormCode','Period','reportDate','PeriodFY','PeriodFP','StartDate','EndDate']]

df.to_excel('10-K & 10-Q filing data.xlsx', index=False)

df1 = df[(df['CIK']=='0001803498') & (df['FactID']=='Assets')]
# df1 = df[df['CIK']=='0001803498']
df1 = df1.sort_values(by='PeriodFY', ascending=True)
pivot_df = df1.pivot_table(index=['CIK', 'FactID'], columns='Period', values='ValueNum', aggfunc='mean')
pivot_df = pivot_df.reset_index()
columns = pivot_df.columns.to_list()
columns = sorted(columns[2:], key=lambda date: datetime.strptime(date, '%m/%d/%Y'))
columns = ['CIK','FactID'] + columns
pivot_df = pivot_df[columns]

pivot_df.to_excel('10-K & 10-Q pivot table.xlsx', index=False)