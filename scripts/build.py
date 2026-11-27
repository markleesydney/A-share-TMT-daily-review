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
<title>TMT 每日复盘 · 2026-11-27（收盘）</title><style>{CSS}</style></head><body>
<header><div class="wrap"><h1>TMT 四行业收盘复盘 · 2026-11-27（数据日 11/26 收盘）</h1>
<div class="sub">电子 / 通信 / 计算机 / 传媒（申万一级） · 行情数据日 2026-11-26（Wind 最新 EOD） · 收盘复盘含 11/27 全天动态（沪指+3.73%报3606.49/创业板+11.61%/科创50+15.07%、成交近2万亿放量6824亿、超5300股上涨439家涨停、电子净流入452亿居首、银行煤炭逆势收跌） ·
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
             f'11/27（周五）A股在「午间国常会首提"国家队"稳市+华为自研HBM突破+广东省算力十五五规划+《新一代通信网建设实施方案》」多重催化下上演「全线爆发日」——收盘沪指+3.73%报3606.49（大涨百点收复3600）/深成+7.24%报10814.02/创业板+11.61%报2443.96/科创50+15.07%报1346.25/北证50+13.20%，两市成交19997.94亿放量6824亿（+51.8%）、超5300股上涨439家涨停（跌停仅1家）、涨幅超9%达1766只。申万一级31个行业29涨2跌：电子+13.19%/通信+12.65%/计算机+10.10%三行业均超10%领涨、传媒+6.06%，仅银行-1.75%/煤炭-1.41%逆势收跌。'
             f'数据日11/26（周四，Wind EOD）四行业成交额加权：通信 <b>{pct(comm["pct_w"])}</b> 领涨（128只70涨54跌）、计算机 <b>{pct(comp["pct_w"])}</b>、电子 <b>{pct(elec["pct_w"])}</b>、传媒 <b>{pct(media["pct_w"])}</b> 唯一下跌（半导体三级「封测+7.05%独强/设备-2.77%/制造-2.94%领跌」）。'
             f'11/27全天主线：①最强催化（午间盘中突变）——国务院常务会议首提「加力发挥"国家队"稳市作用、优化中央汇金类"平准基金"功能、提供充足流动性保障、完善中长期资金入市机制」，午后脉冲式放量（上午沪指仅+0.28%→收盘+3.73%、科创50由+4.43%→+15.07%）；②芯片产业链全线爆发——华为ISSCC 2027四篇论文（自研HBM 64通道/4096DQ位宽=HBM4两倍、五层晶圆对晶圆混合键合，昇腾950已搭载）+半导体设备首个质量管理标准发布，半导体设备/先进封装/HBM领涨（灿芯/京仪装备/华海诚科/长川科技/强一股份20cm，中证半导体+6.05%、设备弹性最强）；③国产算力再强化——广东省算力十五五规划（2028智算破1000EFlops）+英伟达暂停向东南亚发卡→算力租赁/华为链爆发（证通电子3连板、IT服务Ⅱ16股涨停）；④CPO/光通信——LightCounting上修数通TAM至2030年880亿美元（800G驱动、预测上修超75%）+1.6T试点（中际旭创成交333.97亿居首、净流入37.69亿）。'
             f'判断：11/25「费半暴跌→半导体情绪杀」→11/26「超跌修复」→11/27「国常会稳市+芯片产业链全面爆发」三天演绎完成「杀估值→磨底→重估」的闭环。资金高度集中科技（电子净流入452亿/通信158亿/计算机120亿，全市场净流入1048.75亿），银行煤炭逆势收跌，是「增量资金入场+存量再配置」共同推动的成长主导普涨。但科创50单日+15.07%、涨停439家、涨幅超9%达1766家均为罕见极端读数，持续性需量能验证。关键盯三点：①量能能否维持近2万亿（次日回落至1.5万亿以下则定性需修正）、②半导体设备/先进封装能否站稳、③国常会增量政策与中长期资金入市的后续落地。'
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
    p.append(f'<div class="dyn"><div class="d">半导体板块11/26「封测独强、设备制造仍弱」（申万电子半导体二级-0.321%、成交额加权口径189只54涨135跌、半导体三级7个细分「1涨6跌」），是11/25「全线溃退」后的「分化企稳」日——中证半导体-2.54%（仍弱于大盘）、科创50-1.36%，但集成电路封测+7.046%逆势领涨（14只10涨4跌、盛合晶微+18.94%领涨），先进封装/混合键合方向率先从超跌中反转。三级行业结构：'
             f'集成电路封测+7.046%（成交158亿，14只10涨4跌、领涨——华为自研HBM采用五层晶圆对晶圆混合键合催化，盛合晶微+18.94%/灿芯反弹）；'
             f'分立器件+0.850%（成交104亿，18只6涨12跌）；'
             f'模拟芯片设计+0.146%（成交87亿，36只11涨25跌）；'
             f'数字芯片设计-0.490%（成交636亿，57只12涨45跌、成交额最大——国产算力芯片仍承压）；'
             f'半导体材料-0.767%（成交164亿，30只10涨20跌）；'
             f'半导体设备-2.771%（成交306亿，27只6涨21跌——北方华创等设备权重仍弱）；'
             f'集成电路制造-2.937%（成交151亿，7只1涨6跌、领跌——中芯国际/华虹宏力随制造链回调）。'
             f'结构含义：11/26是「杀跌→企稳」的过渡日，半导体内部出现关键分化——「封测/先进封装涨、设备/制造跌」，正是华为自研HBM（64通道4096DQ位宽、晶圆对晶圆混合键合）技术突破的直接映射：混合键合是先进封装最前沿工艺，封测环节率先受益，而设备/制造链前期涨幅大、仍在消化11/25的估值杀。11/27收盘这一分化进一步强化为「半导体设备+先进封装全线领涨」的爆发日：半导体指数涨超10%、中证半导体上午+6.05%（设备弹性最强：长川科技+17.13%/中科飞测+14.92%/北方华创+8.04%/拓荆科技+7.91%/中微公司+6.07%），灿芯/京仪装备/华海诚科/长川科技/强一股份20CM涨停、海立股份/金海通涨停，华虹+9.63%/中芯国际+4.54%/寒武纪+5.09%——芯片产业链成为全场最强主线，半导体板块主力净流入238.24亿。'
             f'核心催化：①华为ISSCC 2027四篇论文（自研HBM 64通道/4096DQ/五层晶圆对晶圆混合键合，昇腾950已搭载）→ 先进封装/混合键合/HBM链；②我国半导体设备与零部件行业首个专属质量管理体系标准《半导体设备与零部件质量管理体系》发布；③英伟达通知戴尔/超微暂停向马来西亚/新加坡/泰国/印尼发运芯片服务器 → 国产替代强化（蓝宝书heat10）；④精测电子新签1.998亿量检测订单（前道量检测国产替代最紧迫环节，heat6）；⑤广东省算力十五五规划（2028智算破1000EFlops/优先国产算力芯片）。中长期国产替代（先进封装/设备/晶圆代工）仍是主线，封测的率先反转是「杀跌回踩检验通过」的信号，设备弹性（量检测/刻蚀/薄膜）是下一阶段核心。'
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
<b>解读：</b>11/26数据日拥挤度出现「计算机回升、其余中性偏低」的结构——计算机6.073%分位85.0%（偏拥挤、四行业最高，自11/25的66.7明显回升，对应国产算力/华为链资金回流）、通信7.587%分位65.0%（中性、自11/25的46.7回升，光模块CPO资金流入）、电子24.417%分位40.0%（中性、自11/25的48.3微降，但成交占比仍居四行业之首——半导体分化后资金未离场）、传媒3.176%分位36.7%（不拥挤、四行业最低，自11/25的46.7续降——题材退潮资金流出）。结构含义：这是「资金重新聚焦科技成长」的前兆——计算机（国产算力/华为链）与通信（光模块/CPO）拥挤度率先回升，精准预告了11/27「科技成长全线爆发」。11/27收盘验证：电子+13.19%/通信+12.65%/计算机+10.10%三行业均超10%领涨、传媒+6.06%，电子主力净流入452亿居首、通信158亿、计算机120亿，全市场净流入1048.75亿；而前期拥挤度最低、题材退潮的传媒今日弹性相对最弱（+6.06%），「出清越充分、拥挤越低」的板块在普涨日涨幅反而偏弱——说明11/27是「资金聚焦科技主线（电子/通信/计算机）」的普涨，而非「超跌传媒补涨」。两市成交19997.94亿放量6824亿（+51.8%）创近20日新高，是「缩量磨底→放量普涨」的确认；但需注意计算机已85.0偏拥挤、电子成交占比24.4%居首，单日极端放量后短线追高需防高位兑现。后续盯「量能能否维持近2万亿+半导体设备/先进封装能否站稳+银行煤炭红利资金是否持续流出」，科技从「超跌博弈」正式转向「国产算力+先进封装+光模块主线验证」。</div></div></div>''')
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
