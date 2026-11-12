"""TEJ 快速查詢。用法:
  python tej_query.py TRAIL/TAPRCD coid=2330 mdate.gte=2025-01-01
金鑰從環境變數 TEJAPI_KEY 讀取(不要寫進程式碼或 commit)。
"""
import os, sys
import tejapi

key = os.environ.get("TEJAPI_KEY")
if not key:
    sys.exit("找不到 TEJAPI_KEY,請在環境設定加入環境變數")
tejapi.ApiConfig.api_key = key

def q(table, **kw):
    return tejapi.get(table, paginate=True, **kw)

if __name__ == "__main__":
    table, params = sys.argv[1], {}
    for a in sys.argv[2:]:
        k, v = a.split("=", 1)
        if "." in k:
            k, op = k.split(".", 1)
            params.setdefault(k, {})[op] = v
        else:
            params[k] = v
    print(q(table, **params).to_string())
