#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""替代 fetch.py：用 westock-data（腾讯自选股）获取今日 TMT 四行业成分股行情"""
import subprocess, json, os, re, sys, datetime

NODE = '/Users/marklee/.workbuddy/binaries/node/versions/22.22.2/bin/node'
SCRIPT = '/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'
OUT = os.path.dirname(os.path.abspath(__file__))

IND = {
    '电子': 'pt01801080',
    '通信': 'pt01801770',
    '计算机': 'pt01801750',
    '传媒': 'pt01801760',
}
TOPN = {'电子': 20, '通信': 10, '计算机': 10, '传媒': 10}


def run(*args):
    """Run westock-data node script, return stdout."""
    cmd = [NODE, SCRIPT] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"ERR: {' '.join(args)} -> {r.stderr[:200]}")
        return ''
    return r.stdout


def parse_table(text):
    """Parse markdown table into list of dicts."""
    lines = text.strip().split('\n')
    rows = []
    header = None
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue
        if '---' in line:
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if header is None:
            header = cells
        else:
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
    return rows


def get_constituents(sector_code):
    """Get list of stock codes for a sector."""
    out = run('sector', 'constituent', sector_code)
    rows = parse_table(out)
    return [r['StockCode'] for r in rows if 'StockCode' in r]


def batch_quote(codes, batch_size=50):
    """Batch quote stocks, return dict code -> data."""
    result = {}
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        code_str = ','.join(batch)
        out = run('quote', code_str)
        rows = parse_table(out)
        for r in rows:
            code = r.get('symbol', r.get('code', ''))
            if code:
                result[code] = r
        print(f"  batch {i//batch_size+1}: {len(batch)} codes, got {len(rows)} results")
    return result


def fmt(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def main():
    print("=== TMT 四行业 westock-data 数据抽取 ===")
    print(f"时间: {datetime.datetime.now().isoformat()}")

    # Step 1: Get constituent lists
    all_codes = {}
    for ind_name, sec_code in IND.items():
        print(f"\n获取 {ind_name} 成分股列表...")
        codes = get_constituents(sec_code)
        all_codes[ind_name] = codes
        print(f"  {ind_name}: {len(codes)} 只")

    # Step 2: Batch quote all stocks
    all_stock_codes = []
    for codes in all_codes.values():
        all_stock_codes.extend(codes)
    all_stock_codes = list(set(all_stock_codes))
    print(f"\n批量查询 {len(all_stock_codes)} 只股票行情...")
    quotes = batch_quote(all_stock_codes, batch_size=60)

    # Step 3: Get today's trade date from any quote
    dt = None
    for q in quotes.values():
        t = q.get('time', '')
        if t:
            dt = t.replace('-', '')
            break
    if not dt:
        dt = datetime.datetime.now().strftime('%Y%m%d')
    print(f"\n交易日: {dt}")

    # Step 4: Build data_stocks.json structure
    data = {
        'trade_dt': dt,
        'prev_dt': '',  # westock-data doesn't easily provide prev date
        'generated_at': datetime.datetime.now().isoformat(),
        'source': 'westock-data (腾讯自选股)',
        'industries': {},
    }

    for ind_name, sec_code in IND.items():
        codes = all_codes[ind_name]
        rows = []
        for code in codes:
            q = quotes.get(code, {})
            if not q or not q.get('price'):
                continue
            pct = fmt(q.get('change_percent'))
            if pct is None:
                continue
            amount_raw = fmt(q.get('amount'))
            # Unit conversion: westock returns yuan, Wind uses 千元
            amount_wind = (amount_raw or 0) / 1000  # 元 -> 千元
            # Market cap: westock returns 亿元, Wind uses 万元
            mv_raw = fmt(q.get('total_market_cap'))
            float_mv_raw = fmt(q.get('circulating_market_cap'))
            rows.append({
                'code': code,
                'name': q.get('name', code),
                'sub': '',  # westock-data constituent doesn't provide SW2 level
                'sub_code': '',
                'sub3': '',
                'close': fmt(q.get('price')),
                'pct': pct,
                'amount': amount_wind,  # 千元（兼容 Wind 格式）
                'volume': fmt(q.get('volume')),
                'turn': fmt(q.get('turnover_rate')),
                'freeturn': fmt(q.get('turnover_rate')),  # approximate
                'mv': (mv_raw or 0) * 10000 if mv_raw else None,  # 亿 -> 万
                'float_mv': (float_mv_raw or 0) * 10000 if float_mv_raw else None,
                'pe': fmt(q.get('pe_ratio')),
                'pb': fmt(q.get('pb_ratio')),
            })

        rows.sort(key=lambda x: -x['pct'])
        n = TOPN[ind_name]

        tot_amt = sum(r['amount'] or 0 for r in rows)
        data['industries'][ind_name] = {
            'code': sec_code,
            'count': len(rows),
            'topn': n,
            'gainers': rows[:n],
            'losers': rows[-n:][::-1],
            'subs': [],  # No SW2 detail from westock-data
            'amt_yi': round(tot_amt / 1e5, 2) if tot_amt else 0,
            'pct_avg': round(sum(r['pct'] for r in rows) / len(rows), 3) if rows else 0,
            'pct_w': round(sum((r['pct'] or 0) * (r['amount'] or 0) for r in rows) / tot_amt, 3) if tot_amt else 0,
            'up': sum(1 for r in rows if r['pct'] > 0),
            'down': sum(1 for r in rows if r['pct'] < 0),
            'all': rows,
        }
        print(f"{ind_name}: {len(rows)}只 加权{data['industries'][ind_name]['pct_w']}% "
              f"成交{data['industries'][ind_name]['amt_yi']}亿 "
              f"涨{data['industries'][ind_name]['up']}/跌{data['industries'][ind_name]['down']}")

    # No semiconductor L3 from westock-data
    data['semiconductor_l3'] = []

    json.dump(data, open(os.path.join(OUT, 'data_stocks.json'), 'w'),
              ensure_ascii=False, indent=1)
    print(f"\nsaved data_stocks.json ({len(all_stock_codes)} stocks, {len(quotes)} with quotes)")


if __name__ == '__main__':
    main()
