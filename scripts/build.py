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
<header><div class="wrap"><h1>TMT 四行业收盘复盘 · {DTF}（11/12 收盘）</h1>
<div class="sub">电子 / 通信 / 计算机 / 传媒（申万一级） · 行情数据日 2026-11-11（Wind 最新 EOD） · 收盘复盘含 11/12 全天动态 ·
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
             f'11/11 数据日 TMT 全线大涨、「光通信CPO逼空+算力硬件」共振，11/12 冲高回落、英伟达黄仁勋危机引爆AI算力链获利了结。'
             f'11/11：通信 <b>{pct(comm["pct_w"])}</b> 领涨四行业（112涨16跌，申万通信+7.99%、通信设备+11.602%——中际旭创+15.07%成交312亿全市场第一/新易盛+16.98%/天孚通信+13.96%/太辰光+17.05%/仕佳光子+13.98%/宇特光电+29.99%/蘅东光+26.45%），'
             f'电子 <b>{pct(elec["pct_w"])}</b>（438涨70跌，元件+7.428%PCB/CCL涨停潮——东山精密/深南电路/景旺电子/沪电股份/胜宏科技涨停，半导体+4.678%——源杰科技/利扬芯片20cm/燧原科技+11.27%/长光华芯+12.05%），'
             f'传媒 <b>{pct(media["pct_w"])}</b>（89涨39跌、出版+3.187%/游戏+3.075%——果麦文化20cm/文投控股/凯撒文化/电魂网络涨停/上海电影创新高），'
             f'计算机 <b>{pct(comp["pct_w"])}</b>（242涨104跌、四行业最弱——智微智能/汉王科技涨停/海天瑞声+6.82%）。'
             f'11/12 收盘冲高回落、三大指数收跌：沪指-0.67%报3655.83/深成指-1.68%/创业板指-2.44%守住2500点/科创50+0.73%，成交1.93万亿放量2558亿、全市场仅875涨4635跌。'
             f'午后英伟达董事会拟紧急会议/黄仁勋风波引爆拥挤的AI算力链：CPO跳水（中际旭创尾盘跌超6%/新易盛-4.38%/天孚-2.17%）、机器人崩塌（奥比中光-12.7%/福莱新材跌停）、AI漫剧重灾（上海电影跌停/华策影视-13.97%）；'
             f'国产芯片逆势（寒武纪+8.11%报973元重回千元/主力净流入14.52亿），申万收盘通信-3.01%/传媒-3.28%/计算机-2.34%/电子-0.63%（相对抗跌）。'
             f'核心催化（Alpha派 PaiPai + Web Search 研判）：①光通信——微软游说叫停光模块禁令「逼空」11/11暴涨后11/12获利了结（通信净流出64.02亿居首、中际旭创净卖出24.99亿居全市场第一）；②国产算力——英伟达黄仁勋任职危机+字节AI芯片负责人施云峰离职（自研ASIC流片性能未达预期）→国产替代「预期窗口」，寒武纪/源杰科技/通富微电获净流入；③存储/半导体——闪迪/美光隔夜大涨+长鑫存储拟2027Q1科创板IPO募资330亿，半导体逆势净流入33亿。'
             f'风格上「一天从进攻AI切换到防守红利」：资金从极度拥挤的传媒/短剧与光模块流出，午后回流银行（工商银行领涨）/白酒（皇台酒业涨停）/燃气，主力单日净流出459亿、连续三日净流入终结。'
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
    p.append(f'<div class="dyn"><div class="d">半导体板块11/11全线大涨（申万电子半导体二级+4.678%、成交额加权口径175涨13跌、成交2119亿）：分立器件+12.47%（18只17涨1跌，源杰科技20cm/长光华芯+12.05%/炬光科技+10.14%领涨，光芯片/激光方向）；'
             f'数字芯片设计+4.91%（57只50涨7跌，燧原科技+11.27%/普冉股份+9.73%领涨，国产GPU/存储）；'
             f'集成电路封测+4.204%（14涨0跌、唯一全线飘红，利扬芯片+20.01%领涨）；'
             f'半导体材料+4.066%（30只29涨1跌）；'
             f'模拟芯片设计+3.003%（36只32涨3跌）；'
             f'半导体设备+2.697%（27只27涨0跌、全线飘红）；'
             f'集成电路制造+0.995%（7只6涨1跌）。'
             f'驱动：11/11半导体「光芯片+国产算力+存储」三线共振——微软游说叫停光模块禁令点燃光芯片（源杰/长光华芯），英伟达黄仁勋危机+字节AI芯片负责人离职催化国产算力芯片，闪迪/美光隔夜大涨点燃存储涨价。'
             f'11/12半导体逆势抗跌、国产GPU/算力芯片接棒：寒武纪收涨8.11%报973元（盘中重回千元、成交201.72亿、主力净流入14.52亿居半导体之首）、源杰科技+9.85亿/通富微电+8.42亿/北方华创+5.52亿获净流入，半导体板块全天逆势净流入33亿；申万电子仅-0.63%四行业相对抗跌。'
             f'核心催化：①长鑫存储拟2027Q1科创板IPO募资330亿+阿里平头哥赴港+沐曦优必选曦选创智融资——国产芯片资产密集资本化；②存储涨价预期再点燃（隔夜闪迪+13%/美光+11%/海力士+9%）；③国产算力「超节点+互连」三线共振（东吴电子强call，昇腾超节点搭载NPO方案、运营商RoCE集采自主可控比例抬升至80%）。'
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
<b>解读：</b>11/11数据日拥挤度——传媒6.028%分位100%（极度拥挤、四行业最高，成交占比自20日均值4.245%大幅抬升、申万传媒vr20达1.45显著放量，换手中位数5.82%/均值9.26%四行业最高，AI短剧/游戏/影视主线吸金但已现高低切、引力传媒/世纪华通领跌）、通信8.95%分位86.7%（偏拥挤，成交占比自20日均值6.993%大幅抬升、申万通信vr20=1.31放量，光模块CPO逼空、主力净流入107亿居首）、电子25.219%分位56.7%（中性、中位，成交占比自20日均值24.078%微升，绝对成交额最大）、计算机4.665%分位28.3%（不拥挤、历史低位，成交占比自20日均值5.545%回落、申万计算机vr20仅0.86缩量、主力净流出11.28亿）。11/11拥挤度出现关键切换——资金从「应用极致拥挤（传媒/短剧）」大幅迁徙至「通信光模块+电子算力硬件」：通信拥挤度自18.3分位快速修复至86.7分位、传媒则冲上100分位。11/12拥挤度的兑现验证了这一判断：光模块/传媒两大极致拥挤方向当日集体踩踏（通信-3.01%/传媒-3.28%、主力净流出64.02亿+21.38亿），电子（56.7分位中性）相对抗跌、半导体逆势净流入33亿——拥挤度越高、兑现越剧烈。判断：本轮反弹本质是「光模块政策缓和（微软游说）+英伟达黄仁勋危机/字节芯片收缩催化的国产替代预期窗口+存储涨价/长鑫IPO」驱动的硬件修复与AI应用扩散，产业向上逻辑未变；但传媒100分位、通信86.7分位的高拥挤已触发11/12的高位获利兑现，短期需等待筹码消化与新的订单/业绩催化，切忌追高拥挤方向，电子/半导体（中性分位）的安全边际相对更优。</div></div></div>''')
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
