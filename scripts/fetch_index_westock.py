#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""替代 fetch_index.py：用 westock-data 获取指数/ETF 数据"""
import subprocess, json, os, sys, datetime

NODE = '/Users/marklee/.workbuddy/binaries/node/versions/22.22.2/bin/node'
SCRIPT = '/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js'
OUT = os.path.dirname(os.path.abspath(__file__))

IND = {
    '电子': 'pt01801080',
    '通信': 'pt01801770',
    '计算机': 'pt01801750',
    '传媒': 'pt01801760',
}


def run(*args):
    cmd = [NODE, SCRIPT] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"ERR: {' '.join(args)} -> {r.stderr[:200]}")
        return ''
    return r.stdout


def parse_table(text):
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


def fmt(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def main():
    print("=== 指数/ETF 数据抽取 (westock-data) ===")

    dt = datetime.datetime.now().strftime('%Y%m%d')
    out = {'trade_dt': dt, 'source': 'westock-data (腾讯自选股)'}

    # --- 指数行情 ---
    idx_codes = {
        'sh000001': '上证指数', 'sz399001': '深证成指', 'sh000300': '沪深300',
        'sz399006': '创业板指', 'sh000688': '科创50', 'sh000998': '中证TMT',
    }
    code_list = ','.join(idx_codes.keys())
    idx_out_raw = run('quote', code_list)
    idx_rows = parse_table(idx_out_raw)

    idx_out = []
    for r in idx_rows:
        code = r.get('symbol', '')
        if code in idx_codes:
            price = fmt(r.get('price'))
            pct = fmt(r.get('change_percent'))
            amount = fmt(r.get('amount'))
            idx_out.append({
                'code': code,
                'name': idx_codes[code],
                'close': price or 0,
                'pct': pct or 0,
                'amt_yi': round((amount or 0) / 1e5, 2),
                'ma5_yi': 0, 'ma20_yi': 0,  # No historical data from single quote
                'vr5': None, 'vr20': None,
                'hist': [],
            })
    idx_out.sort(key=lambda x: -(x.get('vr20') or 0))
    out['indexes'] = idx_out
    print(f"指数: {len(idx_out)} 个")

    # --- ETF: use sector ranking lists ---
    # We can't easily get ETF volume from westock-data in batch.
    # Use sector ranking which includes ETF-related sectors.
    etf_list = run('sector', 'ranking')
    out['etfs'] = []  # Simplified - ETF data not easily batchable
    print("ETF: skipped (not batchable from westock-data)")

    # --- 拥挤度 simplified ---
    stocks = json.load(open(os.path.join(OUT, 'data_stocks.json')))
    crowd = {}
    for ind_name in IND:
        iv = stocks['industries'].get(ind_name, {})
        all_rows = iv.get('all', [])
        turns = [r.get('turn') or 0 for r in all_rows if r.get('turn')]
        crowd[ind_name] = {
            'series': [],
            'share_now': None,
            'share_pctile_60d': None,
            'share_ma20': None,
            'turn_med': round(sorted(turns)[len(turns)//2], 2) if turns else None,
            'turn_avg': round(sum(turns)/len(turns), 2) if turns else None,
        }
    out['crowding'] = crowd
    print(f"拥挤度: simplified (no 60d history)")

    json.dump(out, open(os.path.join(OUT, 'data_market.json'), 'w'),
              ensure_ascii=False, indent=1)
    print("saved data_market.json")


if __name__ == '__main__':
    main()
