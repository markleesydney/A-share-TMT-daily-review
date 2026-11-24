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
<header><div class="wrap"><h1>TMT 四行业收盘复盘 · 2026-11-24（数据日 11/23 收盘）</h1>
<div class="sub">电子 / 通信 / 计算机 / 传媒（申万一级） · 行情数据日 2026-11-23（Wind 最新 EOD） · 收盘复盘含 11/24 全天收盘动态（沪指+0.27%/深成指-0.29%/创业板-0.05%/科创50+1.81%、成交1.66万亿放量1022亿） ·
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
             f'11/24（周二）TMT四行业在「隔夜黄仁勋复职引爆美股科技（英伟达+31.48%创2003年来最大单日涨幅）」下集体大幅高开，但AI硬件侧短线获利盘兑现、全天高开低走——收盘沪指+0.27%报3548.37/深成指-0.29%报10423.60/创业板指-0.05%报2278.99（翻绿）/科创50+1.81%报1250.09（半导体相对强），两市成交1.66万亿放量1022亿、1952涨3496跌、64涨停4跌停。申万TMT：电子 <b>+1.51%</b> 逆势领涨、通信 <b>-0.05%</b>、传媒 <b>-0.27%</b>、计算机 <b>-0.51%</b> 最弱。'
             f'数据日11/23（周一，Wind EOD）四行业成交额加权：传媒 <b>{pct(media["pct_w"])}</b> 领涨（121涨8跌）、通信 <b>{pct(comm["pct_w"])}</b>、计算机 <b>{pct(comp["pct_w"])}</b>、电子 <b>{pct(elec["pct_w"])}</b> 最温和（半导体「高低切」反转：设计/材料涨、制造/设备回调，北方华创-6.55%领跌）。'
             f'11/24收盘核心：①光模块/CPO「易中天」高开兑现——中际旭创盘中+12%收-0.05%（成交285.83亿两市第一）/新易盛盘中+11%收-0.74%（249.75亿）/天孚盘中+11%回落，通信净流出104亿、光通信净流出106亿；②电子逆势领涨、主力净流入85.7亿居全市场第一（寒武纪+6.03%报970元/华虹+7.43%/工业富联+6.97%净流入22.93亿居首/中芯+2.86%），元件净流入30.47亿、消费电子全涨（奥尼电子20cm/中京电子4连板）；③人形机器人/具身智能净流入49亿+国防军工走强（华东重机近8日6涨停）；④传媒影视院线涨停潮（文投控股/浙文影业/横店影视涨停/上海电影+5.04%）；⑤6G发展大会11/24-25催化射频/基站。'
             f'判断：11/24是「外围AI逼空高开→AI硬件侧（光模块/CPO）兑现、资金切向电子(半导体/消费电子/元件)+国防军工+人形机器人+传媒影视」的典型结构分化日，行情本质仍是「情绪修复+结构轮动」而非趋势反转——进攻看半导体/国产算力（寒武纪/华虹/工业富联）、元件/PCB、人形机器人/AIGC短剧「有订单/有交付/有数据验证」方向；光模块中期逻辑（1.6T订单到2027年）未坏但短线「一致高点兑现」已兑现，需以「订单-交付-扩产」择优、防情绪反复；关键盯「电子资金流入能否延续 + 光模块能否止跌企稳 + 大盘能否站稳3500-3600」三点。'
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
    p.append(f'<div class="dyn"><div class="d">半导体板块11/23「设计涨、制造跌」较11/19完全反转（申万电子半导体二级+2.144%、成交额加权口径165涨23跌、半导体三级5涨2跌），是「功率半导体海外大厂调价→国产设计替代加速+海力士HBM4扩产」驱动设计/材料链、前期国产替代大涨的制造/设备高位获利兑现的集中体现——模拟芯片设计+5.095%领涨、半导体材料30涨0跌全涨，而半导体设备-1.569%、集成电路制造-0.775%领跌；科创50收绿（-0.26%）正是半导体制造/设备权重回调的映射。11/24隔夜美股半导体设备指数+18%、存储芯片指数+14.9%（黄仁勋复职）驱动A股半导体全线修复——收盘半导体+1.53%、主力净流入居前，寒武纪+6.03%报970元/华虹宏力+7.43%/工业富联+6.97%（净流入22.93亿居首）/中芯国际+2.86%，制造/设备（北方华创/中微）止跌企稳，是「AI硬件(光模块)兑现→半导体/国产算力承接」的轮动核心：'
             f'模拟芯片设计+5.095%（成交117亿，33涨2跌、领涨——功率半导体海外大厂调价国产替代加速，敏芯股份+19.99%MEMS传感器/峰岹科技+10.76%电机驱动IC）；'
             f'半导体材料+3.835%（成交230亿，30涨0跌全涨——海力士扩大HBM4产能规划+国产材料替代，江丰电子/阿石创领涨）；'
             f'数字芯片设计+3.667%（成交844亿，53涨4跌、成交额最大——炬芯科技+15.68%/富瀚微+11.80%/恒玄科技+10.79%/乐鑫科技+10.02%，端侧SoC/国产算力芯片反弹）；'
             f'分立器件+3.612%（成交138亿，17涨1跌——功率器件受益海外涨价替代）；'
             f'集成电路封测+0.703%（成交177亿，12涨2跌——相对温和）；'
             f'集成电路制造-0.775%（成交190亿，4涨3跌、回调——晶合集成-4.57%/燕东微-4.32%/中芯国际-3.08%，前期晶圆代工涨价大涨后获利兑现）；'
             f'半导体设备-1.569%（成交381亿，16涨11跌领跌——北方华创-6.55%成交61.6亿/中科飞测-5.79%/拓荆科技-3.73%/华海清科-3.57%，前期国产替代「先杀后立」大涨后高位兑现）。'
             f'结构含义：11/19「制造涨设计跌」与11/23「设计涨制造跌」构成一组完整的「高低切」轮回——资金在半导体内部由前期涨幅最大的制造/设备，切向超跌且受益海外涨价替代的设计（模拟/数字/材料）；中长期看国产替代（设备/材料/晶圆代工/先进封装）仍是主线，制造/设备短期兑现后反而是回踩布局窗口。'
             f'核心催化：①功率半导体海外大厂调价、国产替代加速；②海力士扩大HBM4产能规划；③11/24黄仁勋复职（隔夜英伟达+31.48%、美股半导体设备指数+18%/存储+14.9%）→A股半导体/国产算力全线承接（寒武纪/华虹/工业富联/中芯领涨），制造/设备情绪修复；④全球电子协会PCB缺货预警（缺货延至2027H1）。'
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
<b>解读：</b>11/23数据日拥挤度——计算机5.941%分位83.3%（偏拥挤、四行业最高，自11/19的100.0极度拥挤回落，成交占比仍高于20日均值5.535%、算力租赁/AI应用高位抱团后拥挤度仍偏高）、电子25.968%分位68.3%（中性、自11/19的88.3回落至中性——制造/设备高位兑现、资金切向光模块/传媒）、传媒3.831%分位63.3%（中性、自11/19的46.7回升——AI漫剧/影视院线超跌反弹带动资金回流）、通信7.411%分位55.0%（中性、自11/19的38.3回升——光模块「易中天」V型反转资金明显回流）。本轮「拥挤度越低、弹性越大」再次验证：11/19深度出清的传媒（46.7分位）/通信（38.3分位）在11/23弹性最强（成交额加权+7.419%/+6.286%），而拥挤度偏高的计算机（83.3分位）涨幅最温和（+3.786%）——「出清充分的方向反弹空间更大」。11/24收盘验证：隔夜美股科技暴涨（纳指+6.51%/费半+14%+）带动A股科技线大幅高开，但全天高开低走——AI硬件侧（光模块/CPO）「一致高点兑现」（通信净流出104亿/光通信净流出106亿、中际旭创盘中+12%收-0.05%），资金切向拥挤度中性偏低的电子（68.3分位、主力净流入85.7亿居首、半导体/消费电子/元件承接）与前期出清的传媒（影视院线涨停潮）；拥挤度偏高的计算机（83.3分位）当日-0.51%最弱、兑现压力显现——再次印证「拥挤度越高、一致兑现越剧烈、出清方向抗跌性更强」。后续盯「电子资金流入能否延续 + 光模块能否止跌企稳 + 大盘能否站稳3500-3600」，缩量冲高先当反抽看、防情绪反复。</div></div></div>''')
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
