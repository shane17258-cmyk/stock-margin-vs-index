import requests
import csv
import os
import datetime
import sys
import yfinance as yf

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

def twse_date(ymd):
    return ymd.strftime("%Y%m%d")

def tpex_date(ymd):
    return ymd.strftime("%Y/%m/%d")

def safe_json_get(url, headers=None):
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.text.strip().startswith("{"):
            return r.json()
    except Exception:
        pass
    return None

def get_twse_margin_summary(ymd):
    url = f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={twse_date(ymd)}&selectType=MS&response=json"
    data = safe_json_get(url)
    if not data or data.get("stat") != "OK" or not data.get("tables"):
        return None
    result = {"date": ymd.strftime("%Y-%m-%d")}
    for table in data["tables"]:
        for row in table.get("data", []):
            if row[0] == "融資金額(仟元)":
                result["margin_amount"] = int(row[5].replace(",", ""))
                result["margin_amount_prev"] = int(row[4].replace(",", ""))
            elif row[0] == "融資(交易單位)":
                result["margin_shares"] = int(row[5].replace(",", ""))
                result["margin_shares_prev"] = int(row[4].replace(",", ""))
    if "margin_amount" in result:
        return result
    return None

def get_tpex_margin(ymd, avg_price):
    url = f"https://www.tpex.org.tw/www/zh-tw/margin/balance?date={tpex_date(ymd)}"
    data = safe_json_get(url)
    if not data or data.get("stat") != "ok" or not data.get("tables"):
        return None
    total_today = 0
    total_prev = 0
    valid = 0
    for table in data["tables"]:
        for row in table.get("data", []):
            t = row[6].replace(",", "")
            p = row[2].replace(",", "")
            if t.replace("-", "").isdigit() and p.replace("-", "").isdigit():
                total_today += int(t)
                total_prev += int(p)
                valid += 1
    if valid == 0:
        return None
    return {
        "date": ymd.strftime("%Y-%m-%d"),
        "margin_balance": round(total_today * avg_price),
        "margin_prev": round(total_prev * avg_price),
        "margin_change": round((total_today - total_prev) * avg_price),
    }

def get_index_from_yahoo(ticker):
    end = datetime.date.today()
    start = datetime.date(2025, 12, 31)
    try:
        df = yf.download(ticker, start=start, end=end + datetime.timedelta(days=1),
                         progress=False, auto_adjust=True)
        if df.empty:
            print(f"  {ticker}: empty response")
            return {}
        result = {}
        for date_idx, row in df.iterrows():
            d = date_idx.strftime("%Y-%m-%d")
            if isinstance(row["Close"], (int, float)):
                result[d] = float(row["Close"])
            else:
                result[d] = float(row["Close"].iloc[0])
        print(f"  {ticker}: {len(result)} days")
        return result
    except Exception as e:
        print(f"  Yahoo {ticker} error: {e}")
        return {}

def collect_all_data():
    today = datetime.date.today()
    print(f"Today: {today}")

    all_dates = []
    d = datetime.date(2026, 1, 2)
    while d <= today:
        if d.weekday() < 5:
            all_dates.append(d)
        d += datetime.timedelta(days=1)
    print(f"Scanning {len(all_dates)} weekdays (will only query margin if index data exists)")

    print("\nFetching index data from Yahoo Finance...")
    twse_index = get_index_from_yahoo("^TWII")
    tpex_index = get_index_from_yahoo("^TWOII")

    print("\nFetching margin data from TWSE/TPEx for dates with index data...")
    twse_margin = {}
    tpex_margin = {}

    margin_dates = sorted(set(list(twse_index.keys()) + list(tpex_index.keys())))
    for i, ds in enumerate(margin_dates):
        if i % 20 == 0:
            print(f"  Progress: {i}/{len(margin_dates)}")
        d = datetime.date.fromisoformat(ds)

        if ds in twse_index:
            m = get_twse_margin_summary(d)
            if m:
                twse_margin[ds] = {
                    "date": m["date"],
                    "margin_balance": m["margin_amount"],
                    "margin_change": m["margin_amount"] - m["margin_amount_prev"],
                }
                avg_price = m["margin_amount"] / m["margin_shares"] if m["margin_shares"] else 65
                if ds in tpex_index:
                    p = get_tpex_margin(d, avg_price)
                    if p:
                        tpex_margin[ds] = p
        elif ds in tpex_index:
            p = get_tpex_margin(d, 65)
            if p:
                tpex_margin[ds] = p

    save_csv("twse_data.csv", twse_margin, twse_index)
    save_csv("tpex_data.csv", tpex_margin, tpex_index)

    print(f"\n上市: {len(twse_margin)} margin days, {len(twse_index)} index days")
    print(f"上櫃: {len(tpex_margin)} margin days, {len(tpex_index)} index days")

def save_csv(filename, margin_data, index_data):
    filepath = os.path.join(DATA_DIR, filename)
    all_dates = sorted(set(list(margin_data.keys()) + list(index_data.keys())))
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "margin_balance", "margin_change", "index_value", "unit"])
        for dt in all_dates:
            m = margin_data.get(dt, {})
            idx = index_data.get(dt, "")
            unit = "(仟元)"
            writer.writerow([
                dt,
                m.get("margin_balance", ""),
                m.get("margin_change", ""),
                idx if idx else "",
                unit if m.get("margin_balance") is not None else "",
            ])
    print(f"  Saved {filepath} ({len(all_dates)} rows)")

if __name__ == "__main__":
    collect_all_data()
