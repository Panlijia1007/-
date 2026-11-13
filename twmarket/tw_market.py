"""證交所(TWSE)與櫃買中心(TPEx)開放資料 API 工具,免金鑰。

  python tw_market.py search 本益比            # 依關鍵字找端點
  python tw_market.py get twse /exchangeReport/BWIBBU_ALL --code 2330
  python tw_market.py get tpex /tpex_mainborad_highlight
  python tw_market.py catalog                  # 重新產生 CATALOG.md
"""
import json, sys, argparse, pathlib
import requests

HERE = pathlib.Path(__file__).parent
BASE = {"twse": "https://openapi.twse.com.tw/v1", "tpex": "https://www.tpex.org.tw/openapi/v1"}
SPEC = {"twse": HERE / "twse_swagger.json", "tpex": HERE / "tpex_swagger.json"}
CODE_KEYS = ("公司代號", "證券代號", "Code", "SecuritiesCompanyCode", "股票代號")

def endpoints(src):
    for path, v in json.load(open(SPEC[src]))["paths"].items():
        o = v.get("get", {})
        yield path, (o.get("tags") or ["其他"])[0], o.get("summary", "")

def get(src, path, code=None):
    r = requests.get(BASE[src] + path, timeout=30)
    r.raise_for_status()
    data = r.json()
    if code and isinstance(data, list):
        data = [row for row in data if any(str(row.get(k, "")).strip() == code for k in CODE_KEYS)]
    return data

def catalog():
    out = ["# 證交所 / 櫃買中心開放資料 API 清單", "",
           "全部免金鑰。查詢:`python tw_market.py get <twse|tpex> <路徑> [--code 2330]`", ""]
    for src, name in (("twse", "證交所 TWSE"), ("tpex", "櫃買中心 TPEx")):
        by = {}
        for p, t, s in endpoints(src):
            by.setdefault(t, []).append((p, s))
        out.append(f"## {name}(基底網址 {BASE[src]})\n")
        for t, items in sorted(by.items(), key=lambda x: -len(x[1])):
            out.append(f"### {t}({len(items)})\n")
            out += [f"- `{p}` {s}" for p, s in sorted(items)]
            out.append("")
    (HERE / "CATALOG.md").write_text("\n".join(out), encoding="utf-8")
    print("已寫入", HERE / "CATALOG.md")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search", "get", "catalog"])
    ap.add_argument("a", nargs="?"); ap.add_argument("b", nargs="?")
    ap.add_argument("--code"); ap.add_argument("--limit", type=int, default=20)
    n = ap.parse_args()
    if n.cmd == "catalog":
        catalog()
    elif n.cmd == "search":
        for src in SPEC:
            for p, t, s in endpoints(src):
                if n.a in s or n.a in p:
                    print(f"[{src}] {p}  ({t}) {s}")
    else:
        data = get(n.a, n.b, n.code)
        rows = data[: n.limit] if isinstance(data, list) else data
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        if isinstance(data, list): print(f"# 共 {len(data)} 筆,顯示 {len(rows)}", file=sys.stderr)
