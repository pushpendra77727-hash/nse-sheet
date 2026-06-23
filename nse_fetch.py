import gspread, json, os, time, requests, zipfile, io
from datetime import datetime, timedelta
import pandas as pd

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','Close','Delivery %','Del Qty','Traded Qty','Change %','Signal','Date','Status'])

# Get last 3 trading days - try them in order
dates_to_try = []
for i in range(3):
    d = datetime.now() - timedelta(days=i)
    while d.weekday() > 4: # Skip weekends
        d = d - timedelta(days=1)
    dates_to_try.append(d)

df = pd.DataFrame()
final_status = ''
date_display = ''

for trade_date in dates_to_try:
    date_file = trade_date.strftime("%d%b%Y").upper()
    date_display = trade_date.strftime("%d-%m-%Y")
    month_folder = trade_date.strftime('%b').upper()
    year_folder = trade_date.strftime('%Y')

    url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year_folder}/{month_folder}/cm{date_file}bhav.csv.zip"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.nseindia.com/'
    }

    try:
        r = requests.get(url, headers=headers, timeout=20)

        # Check if we actually got a zip file
        if r.status_code == 200 and 'zip' in r.headers.get('Content-Type', ''):
            z = zipfile.ZipFile(io.BytesIO(r.content))
            csv_name = z.namelist()[0]
            df = pd.read_csv(z.open(csv_name))
            df = df[df['SERIES'] == 'EQ']
            df['SYMBOL'] = df['SYMBOL'].str.strip()
            final_status = 'OK'
            break # Success, stop trying dates
        elif r.status_code == 200:
            final_status = f'Not Zip: Got {r.headers.get("Content-Type")}'
        else:
            final_status = f'HTTP {r.status_code} for {date_file}'

    except zipfile.BadZipFile:
        final_status = f'Bad Zip for {date_file}'
    except Exception as e:
        final_status = f'Error: {str(e)[:40]}'

    time.sleep(2) # Wait before trying next date

if df.empty:
    ws.append_row(['ALL', '', '', '', '', '', '', '', final_status])
    exit()

for sym in symbols:
    try:
        row = df[df['SYMBOL'] == sym].iloc[0]
        close = float(row['CLOSE'])
        prev_close = float(row['PREVCLOSE'])
        del_qty = int(row['DELIV_QTY'])
        trd_qty = int(row['TOTTRDQTY'])

        chg_pct = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0
        del_pct = round((del_qty / trd_qty * 100), 2) if trd_qty > 0 else 0

        signal = ''
        if del_pct > 60 and chg_pct > 1:
            signal = 'Strong Accumulation'
        elif del_pct > 50 and chg_pct > 0.5:
            signal = 'BUY'
        elif del_pct < 30 and chg_pct < -1:
            signal = 'Distribution'

        ws.append_row([sym, close, del_pct, del_qty, trd_qty, round(chg_pct,2), signal, date_display, 'OK'])
    except:
        ws.append_row([sym, 'N/A', '', date_display, 'Not in Bhavcopy'])

print("Done")
