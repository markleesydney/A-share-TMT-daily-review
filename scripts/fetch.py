#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""每日复盘数据抽取：电子/通信/计算机/传媒（申万）"""
import pymysql, json, os, datetime

DB = dict(host=os.environ.get('WIND_DB_HOST', ''), user=os.environ.get('WIND_DB_USER', ''),
          password=os.environ.get('WIND_DB_PASS', ''), database=os.environ.get('WIND_DB_NAME', 'financedata'),
          port=int(os.environ.get('WIND_DB_PORT', 3306)), charset='utf8')

IND = {'电子': '7605', '通信': '760r', '计算机': '760p', '传媒': '760q'}
TOPN = {'电子': 20, '通信': 10, '计算机': 10, '传媒': 10}
OUT = os.path.dirname(os.path.abspath(__file__))


def q(cur, sql, args=None):
    cur.execute(sql, args or ())
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    cur.execute("select max(TRADE_DT) from ashareeodprices")
    dt = cur.fetchone()[0]
    cur.execute("select max(TRADE_DT) from ashareeodprices where TRADE_DT < %s", (dt,))
    prev_dt = cur.fetchone()[0]
    print("交易日:", dt, "前一日:", prev_dt)

    data = {'trade_dt': dt, 'prev_dt': prev_dt, 'generated_at': datetime.datetime.now().isoformat(),
            'industries': {}}

    # 1. 二级行业名称字典
    l3 = q(cur, "select INDUSTRIESCODE, INDUSTRIESNAME from ashareindustriescode where INDUSTRIESCODE like '76%%' and LEVELNUM=3")
    sub_name = {r['INDUSTRIESCODE'][:6]: r['INDUSTRIESNAME'] for r in l3}

    # 2. 全部成分股 + 二级归属
    members = q(cur, "select S_INFO_WINDCODE, SW_IND_CODE from ashareswnindustriesclass where CUR_SIGN='1'")
    # 3. 股票名称
    names = {r['S_INFO_WINDCODE']: r['S_INFO_NAME'] for r in
             q(cur, "select S_INFO_WINDCODE, S_INFO_NAME from asharedescription")}
    # 4. 当日行情
    eod = {r['S_INFO_WINDCODE']: r for r in q(cur,
        "select S_INFO_WINDCODE,S_DQ_CLOSE,S_DQ_PCTCHANGE,S_DQ_AMOUNT,S_DQ_VOLUME,S_DQ_PRECLOSE,S_DQ_HIGH,S_DQ_LOW,S_DQ_OPEN from ashareeodprices where TRADE_DT=%s", (dt,))}
    # 5. 衍生指标（换手率/市值/PE）
    der = {r['S_INFO_WINDCODE']: r for r in q(cur,
        "select S_INFO_WINDCODE,S_DQ_TURN,S_DQ_FREETURNOVER,S_VAL_MV,S_DQ_MV,S_VAL_PE_TTM,S_VAL_PB_NEW from ashareeodderivativeindicator where TRADE_DT=%s", (dt,))}

    json.dump({'sub_name': sub_name}, open(os.path.join(OUT, 'raw_subname.json'), 'w'), ensure_ascii=False)

    f = lambda x: float(x) if x is not None else None

    for ind, pre in IND.items():
        ms = [m for m in members if m['SW_IND_CODE'].startswith(pre)]
        rows = []
        for m in ms:
            c = m['S_INFO_WINDCODE']
            e, d = eod.get(c), der.get(c) or {}
            if not e or e['S_DQ_PCTCHANGE'] is None:
                continue
            sub6 = m['SW_IND_CODE'][:6]
            rows.append({
                'code': c, 'name': names.get(c, c),
                'sub': sub_name.get(sub6, '其他'), 'sub_code': sub6,
                'close': f(e['S_DQ_CLOSE']), 'pct': f(e['S_DQ_PCTCHANGE']),
                'amount': f(e['S_DQ_AMOUNT']), 'volume': f(e['S_DQ_VOLUME']),
                'turn': f(d.get('S_DQ_TURN')), 'freeturn': f(d.get('S_DQ_FREETURNOVER')),
                'mv': f(d.get('S_VAL_MV')), 'float_mv': f(d.get('S_DQ_MV')),
                'pe': f(d.get('S_VAL_PE_TTM')), 'pb': f(d.get('S_VAL_PB_NEW')),
            })
        rows.sort(key=lambda x: -x['pct'])
        n = TOPN[ind]
        # 二级行业排名（成交额加权涨跌幅）
        subs = {}
        for r in rows:
            s = subs.setdefault(r['sub'], {'sub': r['sub'], 'n': 0, 'amt': 0.0, 'w': 0.0, 'up': 0, 'down': 0})
            s['n'] += 1
            a = r['amount'] or 0
            s['amt'] += a
            s['w'] += (r['pct'] or 0) * a
            if r['pct'] > 0: s['up'] += 1
            elif r['pct'] < 0: s['down'] += 1
        sublist = []
        for s in subs.values():
            s['pct'] = round(s['w'] / s['amt'], 3) if s['amt'] else 0.0
            s['amt_yi'] = round(s['amt'] / 1e5, 2)  # 千元->亿元
            del s['w'], s['amt']
            sublist.append(s)
        sublist.sort(key=lambda x: -x['pct'])

        tot_amt = sum(r['amount'] or 0 for r in rows)
        data['industries'][ind] = {
            'code': pre, 'count': len(rows),
            'topn': n,
            'gainers': rows[:n], 'losers': rows[-n:][::-1],
            'subs': sublist,
            'amt_yi': round(tot_amt / 1e5, 2),
            'pct_avg': round(sum(r['pct'] for r in rows) / len(rows), 3) if rows else 0,
            'pct_w': round(sum((r['pct'] or 0) * (r['amount'] or 0) for r in rows) / tot_amt, 3) if tot_amt else 0,
            'up': sum(1 for r in rows if r['pct'] > 0),
            'down': sum(1 for r in rows if r['pct'] < 0),
            'all': rows,
        }
        print(f"{ind}: {len(rows)}只 加权{data['industries'][ind]['pct_w']}% 成交{data['industries'][ind]['amt_yi']}亿 二级{len(sublist)}个")

    json.dump(data, open(os.path.join(OUT, 'data_stocks.json'), 'w'), ensure_ascii=False, indent=1)
    conn.close()
    print("saved data_stocks.json")


if __name__ == '__main__':
    main()
