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
<header><div class="wrap"><h1>TMT 四行业收盘复盘 · {DTF}（11/10 收盘）</h1>
<div class="sub">电子 / 通信 / 计算机 / 传媒（申万一级） · 行情数据日 2026-11-09（Wind 最新 EOD） · 收盘复盘含 11/10 全天动态 ·
数据源 Wind 金融数据库 + Alpha派投研 + Web Search · 生成时间 {e(S["generated_at"][:19])}</div></div></header><div class="wrap">''')

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
             f'11/09 数据日 TMT 全面反弹、「国产算力+消费电子+光通信+AI应用」共振：通信 <b>{pct(comm["pct_w"])}</b> 领涨四行业（76涨52跌，通信设备+2.192%、通则康威20cm/东方通信涨停/烽火通信+6.78%/长飞光纤+5.83%），'
             f'电子 <b>{pct(elec["pct_w"])}</b>（311涨197跌，消费电子+3.311%/元件+3.0%领涨——PCB/CCL涨价链世运电路2连板/奥士康/超声电子涨停，燧原科技+17.26%领涨半导体、信维通信+12.77%、翰博高新+14.79%），'
             f'计算机 <b>{pct(comp["pct_w"])}</b>（115涨238跌、权重股经纬恒润-W+10.38%/苏州科达+9.98%带动加权转正），'
             f'传媒 <b>{pct(media["pct_w"])}</b>（31涨95跌、内部高切低——影视院线上海电影/东方明珠/文投控股补涨、AI短剧果麦文化/华策影视退潮）。'
             f'11/10 收盘高开低走、题材分化：沪指+0.08%报3663.72、深成指+0.86%、创业板指+1.46%、科创50+0.64%，两市成交1.5万亿（放量223亿），超4200股上涨、95股涨停——指数磨洋工、个股在狂欢。'
             f'核心催化（Alpha派 PaiPai + Web Search 研判）：①外部——隔夜费半+6.85%（AMD+13%/应用材料+11%）但英伟达-4.27%创近七个月新低（黄仁勋风波），「去英伟达化」交易直接给国产算力链定调，燧原重返2000亿/寒武纪+5%/瑞芯微涨停，而光模块出口链高开低走；②应用——AI短剧/漫剧海外爆火（付费前十中国占九席、活跃用户超1.5亿），传媒涨停潮领涨（文投控股2连板/上海电影3天2板/数字媒体+9.8%）；③风格——油价跌创8月新低+10月CPI+0.7%/PPI+5.7%创52个月新高，存量资金从煤炭/红利切向成长题材；④物理AI——苹果HALO机器人91%成功率+马斯克Optimus量产传闻，人形机器人十余股涨停。'
             f'高开低走原因：量能不足（仅1.5万亿）+获利盘兑现+轮动过快（多而不强）+煤炭/航运权重拖累。'
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
    p.append(f'<div class="dyn"><div class="d">半导体板块11/09止跌反弹、电子内部结构切换（中证半导体-1.199%、成交额加权口径半导体二级+0.633%、94涨93跌）：分立器件+3.487%（9涨9跌）；'
             f'模拟芯片设计+1.77%（24涨11跌）；'
             f'数字芯片设计+1.31%（32涨24跌，燧原科技+17.26%领涨）；'
             f'半导体材料+0.783%（14涨16跌）；'
             f'集成电路封测-0.822%（4涨10跌）；'
             f'半导体设备-1.247%（9涨18跌）；'
             f'集成电路制造-2.212%（2涨5跌，华虹宏力-3.64%）。'
             f'驱动：半导体从10月中旬「全线下跌」切换到「设计强、制造/设备弱」的结构性反弹——设计端（分立/模拟/数字芯片）领涨，受益于国产算力（英伟达被查→国产替代预期强化）+AIoT/消费电子需求回暖；制造端与设备端相对承压，反映「设计先于制造反应需求、制造/设备仍在消化前期高位筹码」。国元证券：国内AI芯片指数近一周+2.8%（海外-9.2%）、国产半导体制造链相对走强；东海证券判断Q4及2027年半导体高景气延续，关注AI算力、存储、光模块光芯片、算力PCB及半导体设备/材料国产替代。'
             f'11/10收盘半导体主力净流入40.62亿居两市首位，AI算力芯片延续涨势（燧原科技总市值重返2000亿、寒武纪+5%、瑞芯微涨停），端侧AI富瀚微/视涯科技20cm涨停；Alpha派点评提示「电子材料自主可控逻辑强化」（光刻胶/光刻机，雅克科技/鼎龙/安集/广钢气体），蓝宝书专家交流指出射频电源国产化率不足20%、静电卡盘/真空泵仍是量产瓶颈，长存四五厂+HBM产线推动2027存储设备交付高峰。'
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
<b>解读：</b>11/09数据日拥挤度——传媒5.285%分位98.3%（极度拥挤、四行业最高，成交占比自20日均值4.141%显著抬升，申万传媒vr20达1.16显著放量，AI影视/短剧/游戏主线持续吸金）、计算机4.997%分位45.0%（中性，成交占比自20日均值5.558%回落，纯软件/信创退潮但国产算力链承接）、电子23.341%分位23.3%（不拥挤，成交占比自20日均值23.933%微降，硬件筹码仍在出清但已处历史低位）、通信6.831%分位26.7%（不拥挤、历史低位，成交占比6.873%附近，光模块vr20仅0.90仍缩量）。整体看，11/09 TMT 拥挤度延续「应用极致拥挤、硬件低位不拥挤」的格局：电子/通信分位仍处20%-30%历史低位，意味着AI硬件（光模块/半导体设备制造）筹码已较充分出清、抛压释放充分；而传媒98.3分位极度拥挤、短线博弈色彩浓（换手中位数4.03%为四行业最高，上海电影/东方明珠/文投控股等影视股连板加速）。11/10收盘验证这一判断并放大分化：传媒涨停潮再度把短线博弈推向极致（数字媒体+9.8%/文字媒体+9.03%，AI短剧/漫剧海外爆火点燃），半导体主力净流入40.62亿居两市首位、电子/通信承接资金回流，但两市成交仅1.5万亿（缩量）、指数高开低走——「应用极致拥挤+硬件低位不拥挤」叠加缩量，意味着行情高度依赖资金情绪、次日易现分歧兑现。判断：本轮反弹本质是「国产算力替代（英伟达被查）+隔夜费半/光通信大涨+AI应用商业化」驱动的硬件修复与AI应用扩散，而非全面泡沫化；电子/通信低位拥挤度+产业向上逻辑（PCB/CCL涨价、光模块订单、国产算力放量）未变，关键看三季报龙头环比兑现与量能能否放大确认反转；传媒极度拥挤、AI影视/短剧题材需防高位波动与节奏切换（11/09已现果麦文化/华策影视退潮、11/10影视院线补涨的轮动）。</div></div></div>''')
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
