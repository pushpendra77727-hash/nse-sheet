import gspread, json, os, time
from nsepython import *
from datetime import datetime
import pandas as pd

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','LTP','Delivery %','OI Change %','Price Change %','Signal','Updated At','Status'])

for sym in symbols:
    ltp = del_pct = p_chg = oi_chg = 'N/A'
    signal = ''
    status = ''

    try:
        # Try live quote first
        q = nse_quote(sym)
        ltp = q.get('lastPrice', 'N/A')
        del_pct = q.get('deliveryToTradedQuantity', 'N/A')
        p_chg = q.get('pChange', 'N/A')
        status = 'Live'
    except:
        # If live fails, get previous close
        try:
            hist = equity_history(sym, series="EQ", start_date="01-06-2026", end_date="23-06-2026")
            if not hist.empty:
                ltp = hist.iloc[-1]['CH_CLOSING_PRICE']
                p_chg = hist.iloc[-1]['CH_PCT_CHANGE']
                status = 'Prev Close'
            else:
                status = 'No Data'
        except Exception as e:
            status = f'Hist Error: {str(e)[:40]}'

    # F&O data - safe version
    try:
        fo = nse_quote_derivative(sym)
        if isinstance(fo, dict) and fo.get('data') and len(fo['data']) > 0:
            oi_chg = fo['data'][0].get('pchangeinOpenInterest', 'N/A')
        else:
            oi_chg = 'No F&O'
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
