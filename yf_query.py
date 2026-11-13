"""Yahoo Finance 快速查詢(免金鑰)。用法:
  python yf_query.py 2330 [period]      # 台股代號自動加 .TW,period 預設 1mo
  python yf_query.py 6488 3mo --otc     # 上櫃加 --otc (.TWO)
"""
import sys
import yfinance as yf

def symbol(code, otc=False):
    return code if "." in code else code + (".TWO" if otc else ".TW")

if __name__ == "__main__":
    code = sys.argv[1]
    period = next((a for a in sys.argv[2:] if not a.startswith("--")), "1mo")
    df = yf.Ticker(symbol(code, "--otc" in sys.argv)).history(period=period)
    print(df.round(2).to_string() if not df.empty else "查無資料")
