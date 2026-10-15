#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成每日复盘 HTML（浅色主题，涨红跌绿）"""
import json, os, html

OUT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(OUT, 'site')
os.makedirs(SITE, exist_ok=True)

S = json.load(open(os.path.join(OUT, 'data_stocks.json')))
M = json.load(open(os.path.join(OUT, 'data_market.json')))
N = json.load(open(os.path.join(OUT, 'news.json')))

SRC = {s['id']: s for s in N['sources']}
DT = S['trade_dt']
DTF = f"{DT[:4]}-{DT[4:6]}-{DT[6:]}"
e = lambda x: html.escape(str(x if x is not None else '—'))


def cls(v):
    """涨红跌绿"""
    if v is None: return 'flat'
    return 'up' if v > 0 else ('down' if v < 0 else 'flat')


def pct(v, d=2):
    if v is None: return '—'
    return f"{v:+.{d}f}%"


def num(v, d=2):
    if v is None: return '—'
    return f"{v:,.{d}f}"


def links(ids):
    if not ids: return '<span class="nosrc">无直接对应新闻</span>'
    return ' '.join(
        f'<a class="src" href="{e(SRC[i]["url"])}" target="_blank" rel="noopener" '
        f'title="{e(SRC[i]["title"])}">{e(SRC[i]["media"])}↗</a>'
        for i in ids if i in SRC)


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#f5f6f8;color:#1a1d23;font:14px/1.65 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:0 0 60px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
header{background:linear-gradient(135deg,#fff 0%,#eef2f7 100%);border-bottom:1px solid #dfe3e8;padding:32px 0 26px;margin-bottom:24px}
h1{font-size:26px;font-weight:700;letter-spacing:-.3px}
.sub{color:#6b7280;font-size:13px;margin-top:8px}
h2{font-size:19px;margin:34px 0 14px;padding-left:11px;border-left:4px solid #c9302c;font-weight:650}
h3{font-size:15px;margin:20px 0 10px;color:#374151;font-weight:650}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:18px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f3f4f6;color:#4b5563;font-weight:600;text-align:right;padding:9px 8px;border-bottom:2px solid #e5e7eb;white-space:nowrap;font-size:12px}
th:nth-child(-n+3),td:nth-child(-n+3){text-align:left}
td{padding:8px;border-bottom:1px solid #f1f2f4;text-align:right;white-space:nowrap}
tr:hover td{background:#fafbfc}
.up{color:#c0392b;font-weight:600}
.down{color:#18874a;font-weight:600}
.flat{color:#6b7280}
.rk{color:#9ca3af;font-size:12px;width:30px}
.nm{font-weight:600}
.cd{color:#9ca3af;font-size:11.5px;font-family:ui-monospace,Menlo,monospace}
.tag{display:inline-block;background:#eef2f7;color:#4b5563;border-radius:4px;padding:1px 7px;font-size:11.5px;margin-left:4px}
.src{display:inline-block;background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;border-radius:4px;padding:1px 7px;font-size:11.5px;text-decoration:none;margin:2px 3px 2px 0}
.src:hover{background:#c0392b;color:#fff;border-color:#c0392b}
.nosrc{color:#9ca3af;font-size:11.5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.kpi{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:15px}
.kpi .lb{color:#6b7280;font-size:12px;margin-bottom:6px}
.kpi .vl{font-size:23px;font-weight:700;letter-spacing:-.5px}
.kpi .ex{color:#9ca3af;font-size:11.5px;margin-top:5px}
.dyn{border-left:3px solid #e5e7eb;padding:11px 0 11px 14px;margin-bottom:13px}
.dyn .t{font-weight:650;margin-bottom:5px;font-size:14.5px}
.dyn .d{color:#4b5563;font-size:13px;margin-bottom:7px}
.bar{height:7px;background:#eef2f7;border-radius:4px;overflow:hidden;min-width:60px;display:inline-block;vertical-align:middle;width:70px}
.bar i{display:block;height:100%;border-radius:4px}
.note{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:13px;font-size:13px;color:#78350f;margin-bottom:16px}
.crowd{font-weight:700}
.c-hi{color:#c0392b}.c-mid{color:#d97706}.c-lo{color:#18874a}
footer{color:#9ca3af;font-size:12px;text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid #e5e7eb}
.tabs{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:15px}
.tab{background:#fff;border:1px solid #dfe3e8;border-radius:20px;padding:6px 16px;cursor:pointer;font-size:13px;font-weight:600;color:#4b5563}
.tab.on{background:#c0392b;color:#fff;border-color:#c0392b}
.pane{display:none}.pane.on{display:block}
@media(max-width:640px){table{font-size:12px}td,th{padding:6px 4px}h1{font-size:21px}}
"""


def stock_table(rows, title, show_l3=False):
    sub_col = '<th>申万三级</th>' if show_l3 else ''
    h = [f'<h3>{e(title)}</h3><table><thead><tr><th>#</th><th>名称</th><th>申万二级</th>{sub_col}'
         '<th>涨跌幅</th><th>收盘</th><th>成交额(亿)</th><th>换手率</th><th>自由换手</th>'
         '<th>总市值(亿)</th><th>PE(TTM)</th><th>驱动因素 / 新闻来源</th></tr></thead><tbody>']
    for i, r in enumerate(rows, 1):
        info = N['stocks'].get(r['code'])
        why = (f'<div class="d">{e(info["why"])}</div>{links(info["src"])}'
               if info else '<span class="nosrc">未检索到该股专项新闻，归因见行业级驱动</span>')
        sub3_col = f'<td><span class="tag">{e(r["sub3"])}</span></td>' if show_l3 and r.get('sub3') else ('<td></td>' if show_l3 else '')
        h.append(
            f'<tr><td class="rk">{i}</td>'
            f'<td class="nm">{e(r["name"])}<div class="cd">{e(r["code"])}</div></td>'
            f'<td><span class="tag">{e(r["sub"])}</span></td>{sub3_col}'
            f'<td class="{cls(r["pct"])}">{pct(r["pct"])}</td>'
            f'<td>{num(r["close"])}</td>'
            f'<td>{num((r["amount"] or 0)/1e5)}</td>'
            f'<td>{num(r["turn"])}</td><td>{num(r["freeturn"])}</td>'
            f'<td>{num((r["mv"] or 0)/1e4,1)}</td><td>{num(r["pe"],1)}</td>'
            f'<td style="text-align:left;white-space:normal;min-width:300px;max-width:460px">{why}</td></tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def index_table():
    h = ['<table><thead><tr><th>指数</th><th>代码</th><th>涨跌幅</th><th>收盘</th>'
         '<th>成交额(亿)</th><th>5日均量(亿)</th><th>20日均量(亿)</th>'
         '<th>量比(5日)</th><th>量比(20日)</th></tr></thead><tbody>']
    for i in M['indexes']:
        v = i['vr20']
        vc = 'up' if v and v > 1.1 else ('down' if v and v < 0.9 else 'flat')
        h.append(f'<tr><td class="nm">{e(i["name"])}</td><td class="cd">{e(i["code"])}</td>'
                 f'<td class="{cls(i["pct"])}">{pct(i["pct"])}</td><td>{num(i["close"])}</td>'
                 f'<td>{num(i["amt_yi"],1)}</td><td>{num(i["ma5_yi"],1)}</td>'
                 f'<td>{num(i["ma20_yi"],1)}</td><td>{num(i["vr5"])}</td>'
                 f'<td class="{vc}">{num(v)}</td></tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def etf_table():
    h = ['<table><thead><tr><th>#</th><th>ETF 名称</th><th>代码</th><th>涨跌幅</th>'
         '<th>收盘</th><th>成交额(亿)</th><th>5日均量(亿)</th><th>20日均量(亿)</th>'
         '<th>量比(20日)</th></tr></thead><tbody>']
    for i, f in enumerate(M['etfs'][:30], 1):
        v = f['vr20']
        vc = 'up' if v and v > 1.1 else ('down' if v and v < 0.9 else 'flat')
        h.append(f'<tr><td class="rk">{i}</td><td class="nm">{e(f["name"])}</td>'
                 f'<td class="cd">{e(f["code"])}</td>'
                 f'<td class="{cls(f["pct"])}">{pct(f["pct"])}</td><td>{num(f["close"],3)}</td>'
                 f'<td>{num(f["amt_yi"])}</td><td>{num(f["ma5_yi"])}</td>'
                 f'<td>{num(f["ma20_yi"])}</td><td class="{vc}">{num(v)}</td></tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def crowd_table():
    h = ['<table><thead><tr><th>行业</th><th>今日成交占比</th><th>20日均值</th>'
         '<th>60日分位</th><th>拥挤状态</th><th>换手中位数</th><th>换手均值</th>'
         '<th>加权涨跌幅</th></tr></thead><tbody>']
    for ind, c in M['crowding'].items():
        p = c['share_pctile_60d'] or 0
        st, sc = ('极度拥挤', 'c-hi') if p >= 90 else \
                 (('偏拥挤', 'c-mid') if p >= 70 else
                  (('中性', 'c-mid') if p >= 40 else ('不拥挤', 'c-lo')))
        iv = S['industries'][ind]
        h.append(f'<tr><td class="nm">{e(ind)}</td><td>{num(c["share_now"],2)}%</td>'
                 f'<td>{num(c["share_ma20"],2)}%</td>'
                 f'<td class="crowd {sc}">{num(p,1)}%</td>'
                 f'<td class="crowd {sc}">{st}</td>'
                 f'<td>{num(c["turn_med"])}%</td><td>{num(c["turn_avg"])}%</td>'
                 f'<td class="{cls(iv["pct_w"])}">{pct(iv["pct_w"])}</td></tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def leader_crowd():
    """龙头股拥挤度：按成交额取各行业前8"""
    h = ['<table><thead><tr><th>行业</th><th>龙头股</th><th>涨跌幅</th>'
         '<th>成交额(亿)</th><th>换手率</th><th>自由流通换手</th><th>行业成交占比</th>'
         '<th>拥挤信号</th></tr></thead><tbody>']
    for ind, iv in S['industries'].items():
        rows = sorted(iv['all'], key=lambda x: -(x['amount'] or 0))[:8]
        tot = sum(r['amount'] or 0 for r in iv['all']) or 1
        for j, r in enumerate(rows):
            ft = r['freeturn'] or 0
            sig, sc = ('过热', 'c-hi') if ft >= 15 else \
                      (('偏热', 'c-mid') if ft >= 8 else ('正常', 'c-lo'))
            h.append(f'<tr>{"<td class=nm>" + e(ind) + "</td>" if j == 0 else "<td></td>"}'
                     f'<td class="nm">{e(r["name"])}<div class="cd">{e(r["code"])}</div></td>'
                     f'<td class="{cls(r["pct"])}">{pct(r["pct"])}</td>'
                     f'<td>{num((r["amount"] or 0)/1e5,1)}</td>'
                     f'<td>{num(r["turn"])}%</td><td>{num(r["freeturn"])}%</td>'
                     f'<td>{num((r["amount"] or 0)/tot*100)}%</td>'
                     f'<td class="crowd {sc}">{sig}</td></tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def sub_table(subs):
    return _sub_table_impl(subs)


def semi_l3_table():
    """半导体申万三级行业排名"""
    sl = S.get('semiconductor_l3', [])
    if not sl: return '<p>暂无半导体三级数据</p>'
    return _sub_table_impl(sl, key='sub3', title='半导体申万三级行业涨跌幅排名（成交额加权）')


def _sub_table_impl(subs, key='sub', title='申万二级行业涨跌幅排名（成交额加权）'):
    mx = max((abs(s['pct']) for s in subs), default=1) or 1
    h = [f'<h3>{title}</h3><table><thead><tr><th>#</th>'
         f'<th>{("申万二级行业" if key=="sub" else "申万三级行业")}</th><th></th><th>加权涨跌幅</th><th>成交额(亿)</th>'
         '<th>成分数</th><th>上涨</th><th>下跌</th></tr></thead><tbody>']
    for i, s in enumerate(subs, 1):
        col = '#c0392b' if s['pct'] > 0 else '#18874a'
        w = abs(s['pct']) / mx * 100
        h.append(f'<tr><td class="rk">{i}</td><td class="nm">{e(s[key])}</td>'
                 f'<td><span class="bar"><i style="width:{w:.0f}%;background:{col}"></i></span></td>'
                 f'<td class="{cls(s["pct"])}">{pct(s["pct"])}</td>'
                 f'<td>{num(s["amt_yi"])}</td><td>{s["n"]}</td>'
                 f'<td class="up">{s["up"]}</td><td class="down">{s["down"]}</td></tr>')
    h.append('</tbody></table>')
    return ''.join(h)


def build():
    p = []
    p.append(f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TMT 每日复盘 · {DTF}</title><style>{CSS}</style></head><body>
<header><div class="wrap"><h1>TMT 四行业收盘复盘 · {DTF}（10/14 收盘）</h1>
<div class="sub">电子 / 通信 / 计算机 / 传媒（申万一级） · 行情数据日 2026-10-14（Wind 最新 EOD） ·
数据源 Wind 金融数据库 + Alpha派投研 · 生成时间 {e(S["generated_at"][:19])}</div></div></header><div class="wrap">''')

    # KPI
    p.append('<div class="grid">')
    for ind, iv in S['industries'].items():
        c = M['crowding'][ind]
        p.append(f'''<div class="kpi"><div class="lb">{e(ind)}（申万）成交额加权涨跌幅</div>
<div class="vl {cls(iv["pct_w"])}">{pct(iv["pct_w"])}</div>
<div class="ex">{iv["count"]} 只成分 · <span class="up">{iv["up"]}涨</span> /
<span class="down">{iv["down"]}跌</span> · 成交 {num(iv["amt_yi"],0)} 亿 ·
占全市场 {num(c["share_now"],2)}%（60日 {num(c["share_pctile_60d"],1)} 分位）</div></div>''')
    p.append('</div>')

    # 全景解读
    p.append('<h2>一、当日市场全景与驱动</h2>')
    elec = S["industries"]["电子"]
    comm = S["industries"]["通信"]
    comp = S["industries"]["计算机"]
    media = S["industries"]["传媒"]
    top_g = max(elec["gainers"][:3], key=lambda x: x["pct"])
    top_l = max(elec["losers"][:3] + comm["losers"][:3], key=lambda x: abs(x["pct"]))
    total_amt = sum(S["industries"][ind]["amt_yi"] for ind in ["电子","通信","计算机","传媒"])
    p.append(f'<div class="note"><b>一句话概括：</b>'
             f'10/14 数据日 TMT 出现「应用强、硬件弱」的极致分化：传媒 <b>{pct(media["pct_w"])}</b> 唯一领涨（90涨38跌，出版+4.532%创8个月新高，富春股份/果麦文化20cm、慈文传媒/新经典4连板、掌阅科技7天4板——AI短剧/漫剧第三轮行情从「概念炒作」切换「业绩兑现」），'
             f'电子 <b>{pct(elec["pct_w"])}</b>（半导体-3.24%领跌、C粤芯-U新股次日-11.7%/有研新材跌停，但元件-0.102%抗跌、PCB/CCL涨价链逆势——满坤科技+18.3%/超声电子+10%/宝鼎科技+10%），'
             f'计算机 <b>{pct(comp["pct_w"])}</b>（博汇科技-12.73%风险提示退潮、网安/AI算力集体回撤），'
             f'通信 <b>{pct(comm["pct_w"])}</b> 领跌四行业（14涨113跌，光模块CPO中际旭创/新易盛/天孚通信跌超5%、主力净流出17.14/14.8亿）。'
             f'指数全线走弱：沪指-0.88%报3767.23、深成-1.97%、创业板指-3.10%（领跌）、科创50-3.29%、国证通信-4.08%，成交1.43万亿缩量2625亿、超4400股下跌。'
             f'核心三重共振（Alpha派 PaiPai 研判）：①外部——盘后美国9月CPI核心通胀超预期（核心同比2.56%/环比0.33%）+美债10Y高位5.21%，全球科技硬件风险偏好下行（韩KOSPI盘中-7%）；②产业——OCP大会无超预期、存储竞争担忧（CXMT DDR5）+HBM4设备延期、ASML 2027 EUV产能低于预期；③资金——存量博弈（9月融资净流出950亿）+低波红利占优，电子主力净流出89亿最狠、传媒净流入67.87亿唯一正值。'
             f'结构亮点（产业向上逻辑未变）：PCB/CCL涨价链（建滔/松下/南亚涨价+沪电前三季净利+100%-110%+NV OCP确认PTFE方案）+AI应用（PineDrama出海破亿+AI短剧降本80%）。券商共识「三季报定高低」。'
             f'数据源：Wind金融数据库 + Alpha派投研 + Web Search。</div>')
    p.append('<div class="card">')
    for m in N['macro']:
        p.append(f'<div class="dyn"><div class="t">{e(m["t"])}</div>'
                 f'<div class="d">{e(m["d"])}</div>{links(m["src"])}</div>')
    p.append('</div>')

    # 分行业
    p.append('<h2>二、分行业涨跌幅榜与归因</h2>')
    p.append('<div class="tabs">')
    for i, ind in enumerate(S['industries']):
        p.append(f'<div class="tab{" on" if i == 0 else ""}" data-t="{i}">{e(ind)}</div>')
    p.append('</div>')
    for i, (ind, iv) in enumerate(S['industries'].items()):
        p.append(f'<div class="pane{" on" if i == 0 else ""}" id="p{i}"><div class="card">')
        p.append(f'<h3>{e(ind)}（申万一级）行业解读</h3>'
                 f'<div class="dyn"><div class="d">{e(N["industry_view"][ind])}</div></div>')
        p.append(sub_table(iv['subs']))
        p.append('</div><div class="card">')
        p.append(stock_table(iv['gainers'], f'{ind} · 涨幅前 {iv["topn"]}'))
        p.append('</div><div class="card">')
        p.append(stock_table(iv['losers'], f'{ind} · 跌幅前 {iv["topn"]}'))
        p.append('</div></div>')

    # 半导体三级行业明细
    p.append('<h2>三、半导体细分赛道全景</h2>')
    p.append('<div class="card">')
    sl3 = S.get("semiconductor_l3", [])
    top_l3 = sl3[0] if sl3 else {}
    bot_l3 = sl3[-1] if sl3 else {}
    p.append(f'<div class="dyn"><div class="d">半导体板块10/14全线下跌、领跌电子（申万半导体-2.86%、中证半导体-3.37%，成交额加权口径半导体二级-3.24%）：集成电路制造-6.115%领跌（0涨7跌全绿，C粤芯-U上市次日-11.7%拖累）；'
             f'半导体材料-4.837%（1涨29跌，有研新材跌停）；'
             f'集成电路封测-3.532%（0涨14跌全绿）；'
             f'半导体设备-3.398%（1涨26跌，金海通-8.42%/强一股份-7.32%）；'
             f'分立器件-3.215%（2涨16跌）；'
             f'数字芯片设计-2.675%（7涨50跌，乐鑫科技+14%逆势——SoC/AIoT、晶晨/燧原相对抗跌）；'
             f'模拟芯片设计-0.627%相对最抗跌（4涨32跌）。'
             f'驱动：本轮半导体/通信/光模块回调主因是「AI硬件高位兑现+外部利率冲击+存量博弈高切低」，而非景气拐点——存储端南亚科技DRAM合约价Q3均价环比+60%（供给紧张贯穿2027）、ASML上调全年营收指引至440-450亿欧元（客户讨论2029/2030订单）等产业向上硬事实仍在；但短线被CXMT DDR5竞争担忧、HBM4设备延期、ASML 2027 EUV产能低于预期、美国CPI超预期四重利空压制。'
             f'关注：PCB/CCL涨价链（沪电/兴森/崇达/宝鼎业绩兑现）+国产设备替代（ASML产能紧张映射）+先进封装为结构亮点，等待三季报龙头环比兑现与量能回归确认企稳。'
             f'数据源：Wind金融数据库 + Alpha派投研。</div></div>')
    p.append(semi_l3_table())
    p.append('</div>')

    # 半导体整体涨幅前20 / 跌幅前20
    semi_rows = [r for r in S['industries']['电子']['all'] if r.get('sub3')]
    semi_by_pct_asc = sorted(semi_rows, key=lambda x: x['pct'])
    semi_by_pct_desc = sorted(semi_rows, key=lambda x: -x['pct'])
    p.append('<div class="card">')
    p.append(stock_table(semi_by_pct_desc[:20], '半导体 · 涨幅前 20', show_l3=True))
    p.append('</div><div class="card">')
    p.append(stock_table(semi_by_pct_asc[:20], '半导体 · 跌幅前 20', show_l3=True))
    p.append('</div>')

    # 各三级细分行业涨跌幅前五
    p.append('<div class="card"><h3>半导体三级细分行业涨跌幅前五</h3>')
    sub3_list = ['分立器件','半导体材料','数字芯片设计','模拟芯片设计','集成电路制造','集成电路封测','半导体设备']
    p.append('<div class="tabs">')
    for i, s3 in enumerate(sub3_list):
        p.append(f'<div class="tab{" on" if i == 0 else ""}" data-st="{i}">{e(s3)}</div>')
    p.append('</div>')
    for i, s3 in enumerate(sub3_list):
        ss = [r for r in semi_rows if r['sub3'] == s3]
        ss_d = sorted(ss, key=lambda x: -x['pct'])
        ss_a = sorted(ss, key=lambda x: x['pct'])
        p.append(f'<div class="pane{" on" if i == 0 else ""}" id="s{i}">')
        p.append(f'<div style="margin-bottom:16px">{stock_table(ss_d[:5], f"{s3} · 涨幅前五", show_l3=False)}</div>')
        p.append(stock_table(ss_a[:5], f"{s3} · 跌幅前五", show_l3=False))
        p.append('</div>')
    p.append('</div>')

    p.append('<h2>四、相关指数与 ETF 成交量</h2>')
    p.append('<div class="card"><h3>主要指数（按 20 日量比降序）</h3>'
             '<div class="d" style="color:#6b7280;font-size:12.5px;margin-bottom:10px">'
             '量比 = 当日成交额 / N 日均成交额。&gt;1.1 视为放量（红），&lt;0.9 视为缩量（绿）。</div>'
             + index_table() + '</div>')
    p.append('<div class="card"><h3>相关主题 ETF（按当日成交额降序 Top30）</h3>'
             + etf_table() + '</div>')

    # 拥挤度
    p.append('<h2>五、交易拥挤度</h2>')
    p.append('''<div class="note"><b>口径说明：</b>行业拥挤度以「该行业成交额占全市场成交额比重」
为核心指标，并给出该比重在最近 60 个交易日中的分位数。分位 ≥90% 记为极度拥挤，70%-90% 偏拥挤，
40%-70% 中性，&lt;40% 不拥挤。个股层面用自由流通换手率：≥15% 过热，8%-15% 偏热。</div>''')
    p.append('<div class="card"><h3>行业层面拥挤度</h3>' + crowd_table() + '''
<div class="dyn" style="margin-top:14px"><div class="d">
<b>解读：</b>10/14数据日拥挤度——传媒5.862%分位100.0%（极度拥挤、四行业最高，成交占比自20日均值明显抬升，AI短剧/出版/游戏主线吸金，申万传媒vr20达1.81显著放量）、计算机5.044%分位45.0%（中性，成交占比小幅抬升但资金净流出58.81亿、网安/AI算力退潮）、电子22.52%分位8.3%（不拥挤，成交占比自20日均值明显回落，AI硬件融资盘出清、主力净流出89亿最狠）、通信6.169%分位3.3%（不拥挤、历史极低位，光模块缩量vr20仅0.63、主力净流出64亿）。整体看，10/14 TMT 拥挤度延续并强化「硬件出清、应用过热」的极致分化：电子/通信/计算机均处不拥挤至中性区间（电子8.3分位、通信3.3分位、计算机45分位），仅传媒极度拥挤（100分位）。这印证本轮本质是「AI硬件→AI应用/内容」的高低切换而非趋势反转——9月融资净流出950.3亿、外资三季度净流出约1044亿，电子为主要减持方向；传媒成四行业唯一资金净流入(+67.87亿)。判断：电子/通信拥挤度处历史极低位意味着AI硬件抛压已较充分释放，产业面PCB/CCL涨价（建滔/松下/南亚）+光模块订单（FCC未列光模块议题、NV PTFE路径确认）逻辑未变，关键看三季报龙头环比兑现与量能回归；传媒已极度拥挤、短线博弈色彩浓（果麦文化换手46%、新华文轩13天9板），需防AI短剧/并购题材事件节奏差异带来的高位波动，但「AI内容商业化+出海」中期主线清晰。</div></div></div>''')
    p.append('<div class="card"><h3>行业龙头股拥挤度（各行业成交额前 8）</h3>'
             + leader_crowd() + '</div>')

    # 来源
    p.append('<h2>六、新闻来源汇总</h2><div class="card">')
    for s in N['sources']:
        p.append(f'<div class="dyn"><div class="t"><a class="src" href="{e(s["url"])}" '
                 f'target="_blank" rel="noopener">{e(s["media"])}↗</a> {e(s["title"])}</div>'
                 f'<div class="cd">{e(s["url"])}</div></div>')
    p.append('</div>')

    p.append('''<footer>数据来源：Wind 金融数据库（行情/申万分类/指数/ETF）与公开财经媒体报道。
本页面为量化复盘工具输出，所有内容仅供研究参考，不构成任何投资建议。</footer></div>
<script>
(function(){
function tabs(sel,prefix){
 document.querySelectorAll(sel).forEach(function(t){
  t.addEventListener('click',function(){
   document.querySelectorAll(sel).forEach(function(x){x.classList.remove('on')});
   t.classList.add('on');
   var id=prefix+(t.dataset.t||t.dataset.st);
   document.querySelectorAll('[id^="'+prefix+'"]').forEach(function(x){x.classList.remove('on')});
   document.getElementById(id).classList.add('on');
  });
 });
}
tabs('[data-t]','p');
tabs('[data-st]','s');
})();
</script></body></html>''')

    f = os.path.join(SITE, 'index.html')
    open(f, 'w').write(''.join(p))
    print('generated', f, os.path.getsize(f), 'bytes')


if __name__ == '__main__':
    build()
