import gspread, json, os, time
from nsepython import *
from datetime import datetime

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','LTP','Delivery %','OI Change %','Price Change %','Signal','Updated At','Status'])

for sym in symbols:
    # Default values
    ltp = del_pct = p_chg = oi_chg = 'N/A'
    signal = ''
    status = 'Processing'

    # Equity data
    try:
        q = nse_quote(sym)
        ltp = q.get('lastPrice', 'N/A')
        del_pct = q.get('deliveryToTradedQuantity', 'N/A')
        p_chg = q.get('pChange', 'N/A')
        status = 'OK'
    except Exception as e:
        status = f'EQ Error: {str(e)[:40]}'
        ws.append_row([sym, ltp, del_pct, oi_chg, p_chg, signal, str(datetime.now())[:16], status])
        time.sleep(2)
        continue

    # F&O data - SAFE VERSION, no 'data' crash
    try:
        fo = nse_quote_derivative(sym)
        oi_chg = 'No F&O'
        if fo: # Check if fo is not None
            if isinstance(fo, dict): # Check if it's a dict
                if 'data' in fo: # Check if 'data' key exists
                    if isinstance(fo['data'], list) and len(fo['data']) > 0: # Check if data is list with items
                        if isinstance(fo['data'][0], dict): # Check if first item is dict
                            oi_chg = fo['data'][0].get('pchangeinOpenInterest', 'No F&O')
    except:
        oi_chg = 'No F&O'

    # Signal
    try:
        if all(isinstance(x, (int, float)) for x in [del_pct, oi_chg, p_chg]):
            if del_pct > 50 and oi_chg > 5 and p_chg > 0:
                signal = 'STRONG BUY'
            elif oi_chg > 5 and p_chg < 0:
                signal = 'Short Buildup'
    except:
        pass

    ws.append_row([sym, ltp, del_pct, oi_chg, p_chg, signal, str(datetime.now())[:16], status])
    time.sleep(3)

print("Done")
