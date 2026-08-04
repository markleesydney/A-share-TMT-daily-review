#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""指数/ETF 成交量 + 行业与龙头股拥挤度"""
import pymysql, json, os

DB = dict(host=os.environ.get('WIND_DB_HOST', ''), user=os.environ.get('WIND_DB_USER', ''),
          password=os.environ.get('WIND_DB_PASS', ''), database=os.environ.get('WIND_DB_NAME', 'financedata'),
          port=int(os.environ.get('WIND_DB_PORT', 3306)), charset='utf8')
OUT = os.path.dirname(os.path.abspath(__file__))
IND = {'电子': '7605', '通信': '760r', '计算机': '760p', '传媒': '760q'}


def q(cur, sql, args=None):
    cur.execute(sql, args or ())
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main():
    conn = pymysql.connect(**DB); cur = conn.cursor()
    cur.execute("select max(TRADE_DT) from ashareeodprices"); dt = cur.fetchone()[0]
    # 最近60个交易日
    cur.execute("select distinct TRADE_DT from ashareeodprices where TRADE_DT<=%s order by TRADE_DT desc limit 60", (dt,))
    days = [r[0] for r in cur.fetchall()]
    d60, d20 = days[-1], days[19]
    print("窗口:", d60, "~", dt)

    out = {'trade_dt': dt, 'days': days[::-1]}

    # ---- 指数 ----
    idx_codes = {
        '000001.SH': '上证指数', '399001.SZ': '深证成指', '000300.SH': '沪深300',
        '399006.SZ': '创业板指', '000688.SH': '科创50', '000998.SH': '中证TMT',
        '399363.SZ': '国证通信', '930713.CSI': '中证人工智能', '931743.CSI': '中证半导体',
    }
    sw_codes = {'801080.SI': '申万电子', '801770.SI': '申万通信',
                '801750.SI': '申万计算机', '801760.SI': '申万传媒'}
    codes = tuple(idx_codes)
    rows = q(cur, f"""select S_INFO_WINDCODE,TRADE_DT,S_DQ_CLOSE,S_DQ_PCTCHANGE,S_DQ_AMOUNT,S_DQ_VOLUME
        from aindexeodprices where TRADE_DT>=%s and S_INFO_WINDCODE in ({','.join(['%s']*len(codes))})""",
             (d60,) + codes)
    swc = tuple(sw_codes)
    swr = q(cur, f"""select S_INFO_WINDCODE,TRADE_DT,S_DQ_CLOSE,S_DQ_PRECLOSE,S_DQ_AMOUNT,S_DQ_VOLUME
        from aswsindexeod where TRADE_DT>=%s and S_INFO_WINDCODE in ({','.join(['%s']*len(swc))})""",
             (d60,) + swc)
    for r in swr:
        pc, cl = r.pop('S_DQ_PRECLOSE'), r['S_DQ_CLOSE']
        r['S_DQ_PCTCHANGE'] = (float(cl) / float(pc) - 1) * 100 if pc and cl else None
    idx_codes.update(sw_codes)
    rows += swr
    print("index rows:", len(rows))
    idx = {}
    for r in rows:
        idx.setdefault(r['S_INFO_WINDCODE'], []).append(r)
    idx_out = []
    for c, rs in idx.items():
        rs.sort(key=lambda x: x['TRADE_DT'])
        amt = [float(x['S_DQ_AMOUNT'] or 0) for x in rs]
        cur_amt = amt[-1]
        ma5 = sum(amt[-5:]) / min(5, len(amt))
        ma20 = sum(amt[-20:]) / min(20, len(amt))
        idx_out.append({'code': c, 'name': idx_codes[c],
                        'close': float(rs[-1]['S_DQ_CLOSE'] or 0),
                        'pct': float(rs[-1]['S_DQ_PCTCHANGE'] or 0),
                        'amt_yi': round(cur_amt / 1e5, 2),
                        'ma5_yi': round(ma5 / 1e5, 2), 'ma20_yi': round(ma20 / 1e5, 2),
                        'vr5': round(cur_amt / ma5, 2) if ma5 else None,
                        'vr20': round(cur_amt / ma20, 2) if ma20 else None,
                        'hist': [{'d': x['TRADE_DT'], 'amt': round(float(x['S_DQ_AMOUNT'] or 0) / 1e5, 2),
                                  'close': float(x['S_DQ_CLOSE'] or 0)} for x in rs]})
    idx_out.sort(key=lambda x: -(x['vr20'] or 0))
    out['indexes'] = idx_out

    # ---- ETF ----
    etf_kw = ['半导体', '芯片', '通信', '计算机', '传媒', '游戏', '科技', '电子', '软件', '人工智能', '云计算', '5G', '消费电子', '光通信', '数据']
    cond = ' or '.join(["S_INFO_NAME like %s"] * len(etf_kw))
    cond = ' or '.join(["F_INFO_NAME like %s"] * len(etf_kw))
    funds = q(cur, f"""select F_INFO_WINDCODE,F_INFO_NAME from chinamutualfunddescription
        where ({cond}) and F_INFO_NAME like %s and (F_INFO_DELISTDATE is null or F_INFO_DELISTDATE='')""",
              tuple(f'%{k}%' for k in etf_kw) + ('%ETF%',))
    print("etf candidates:", len(funds))
    out['_etf_cand'] = len(funds)
    fmap = {f['F_INFO_WINDCODE']: f['F_INFO_NAME'] for f in funds}
    etf_out = []
    if fmap:
        fc = tuple(fmap)
        CH = 400
        erows = []
        for i in range(0, len(fc), CH):
            part = fc[i:i + CH]
            erows += q(cur, f"""select S_INFO_WINDCODE,TRADE_DT,S_DQ_CLOSE,S_DQ_PCTCHANGE,S_DQ_AMOUNT,S_DQ_VOLUME
                from chinaclosedfundeodprice where TRADE_DT>=%s and S_INFO_WINDCODE in ({','.join(['%s']*len(part))})""",
                       (d60,) + part)
        print("etf rows:", len(erows))
        eg = {}
        for r in erows:
            eg.setdefault(r['S_INFO_WINDCODE'], []).append(r)
        for c, rs in eg.items():
            rs.sort(key=lambda x: x['TRADE_DT'])
            amt = [float(x['S_DQ_AMOUNT'] or 0) for x in rs]
            if not amt or amt[-1] <= 0 or rs[-1]['TRADE_DT'] != dt:
                continue
            ma5 = sum(amt[-5:]) / min(5, len(amt)); ma20 = sum(amt[-20:]) / min(20, len(amt))
            etf_out.append({'code': c, 'name': fmap[c],
                            'close': float(rs[-1]['S_DQ_CLOSE'] or 0),
                            'pct': float(rs[-1]['S_DQ_PCTCHANGE'] or 0),
                            'amt_yi': round(amt[-1] / 1e5, 3),
                            'ma5_yi': round(ma5 / 1e5, 3), 'ma20_yi': round(ma20 / 1e5, 3),
                            'vr5': round(amt[-1] / ma5, 2) if ma5 else None,
                            'vr20': round(amt[-1] / ma20, 2) if ma20 else None})
        etf_out.sort(key=lambda x: -x['amt_yi'])
    out['etfs'] = etf_out[:40]

    # ---- 拥挤度 ----
    members = q(cur, "select S_INFO_WINDCODE, SW_IND_CODE from ashareswnindustriesclass where CUR_SIGN='1'")
    stocks = json.load(open(os.path.join(OUT, 'data_stocks.json')))
    # 全市场每日成交额（算行业成交额占比）
    cur.execute("select TRADE_DT, sum(S_DQ_AMOUNT) from ashareeodprices where TRADE_DT>=%s group by TRADE_DT", (d60,))
    mkt = {r[0]: float(r[1] or 0) for r in cur.fetchall()}

    crowd = {}
    for ind, pre in IND.items():
        cs = tuple(m['S_INFO_WINDCODE'] for m in members if m['SW_IND_CODE'].startswith(pre))
        rows2 = []
        for i in range(0, len(cs), 400):
            part = cs[i:i + 400]
            rows2 += q(cur, f"""select TRADE_DT, sum(S_DQ_AMOUNT) amt from ashareeodprices
                where TRADE_DT>=%s and S_INFO_WINDCODE in ({','.join(['%s']*len(part))}) group by TRADE_DT""",
                       (d60,) + part)
        agg = {}
        for r in rows2:
            agg[r['TRADE_DT']] = agg.get(r['TRADE_DT'], 0) + float(r['amt'] or 0)
        ser = [{'d': d, 'amt_yi': round(agg.get(d, 0) / 1e5, 2),
                'share': round(agg.get(d, 0) / mkt[d] * 100, 3) if mkt.get(d) else None}
               for d in days[::-1] if d in agg]
        shares = [s['share'] for s in ser if s['share'] is not None]
        cshare = shares[-1] if shares else None
        rank = round(sum(1 for s in shares if s <= cshare) / len(shares) * 100, 1) if shares else None
        # 换手率拥挤度
        turns = [r['turn'] for r in stocks['industries'][ind]['all'] if r.get('turn')]
        crowd[ind] = {'series': ser, 'share_now': cshare, 'share_pctile_60d': rank,
                      'share_ma20': round(sum(shares[-20:]) / min(20, len(shares)), 3) if shares else None,
                      'turn_med': round(sorted(turns)[len(turns) // 2], 2) if turns else None,
                      'turn_avg': round(sum(turns) / len(turns), 2) if turns else None}
        print(ind, 'share', cshare, 'pctile', rank)
    out['crowding'] = crowd

    json.dump(out, open(os.path.join(OUT, 'data_market.json'), 'w'), ensure_ascii=False, indent=1)
    conn.close(); print("saved data_market.json")


if __name__ == '__main__':
    main()
