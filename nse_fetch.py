import gspread, json, os, time
from nsepython import *
from datetime import datetime

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','LTP','Delivery %','OI Change %','Price Change %','Signal','Updated At'])

for sym in symbols:
    try:
        q = nse_quote(sym)
        fo = nse_quote_derivative(sym)

        ltp = q['lastPrice']
        del_pct = q['deliveryToTradedQuantity']
        p_chg = q['pChange']
        oi_chg = fo['data'][0]['pchangeinOpenInterest']

        signal = ''
        if del_pct > 50 and oi_chg > 5 and p_chg > 0:
            signal = 'STRONG BUY'
        elif del_pct > 50 and oi_chg < -5 and p_chg > 0:
            signal = 'Short Covering'

        ws.append_row([sym, ltp, del_pct, oi_chg, p_chg, signal, str(datetime.now())[:16]])
        time.sleep(2)
    except:
        ws.append_row([sym, 'Error', '', '', '', '', ''])
