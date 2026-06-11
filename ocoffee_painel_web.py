#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O'Coffee - Painel do Mercado | Versão Web (Render.com)"""
import os, sys, json, base64, time, re, socket, threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

try:
    import requests
except ImportError:
    print("Biblioteca requests não encontrada. Execute: pip install requests")
    sys.exit(1)

# ===== Configurações =====
LIBRAS_POR_SACA = 132.277
PORT = int(os.environ.get("PORT", "8080"))
CACHE_DURACAO = 120
INTERVALO_ATUALIZACAO = 300

# Autenticação via variáveis de ambiente do Render
PAINEL_USER = os.environ.get("PAINEL_USER", "ocoffee")
PAINEL_PASS = os.environ.get("PAINEL_PASS", "cafe2026")
AUTH_TOKEN = base64.b64encode(f"{PAINEL_USER}:{PAINEL_PASS}".encode()).decode()

# Pasta do app
PASTA_APP = os.path.dirname(os.path.abspath(__file__))

LABELS = [
    {"nome": "Agata 14/15+MK", "diferencial": 0},
    {"nome": "Agata 16/18", "diferencial": 15},
    {"nome": "Esmeralda 14/15+MK", "diferencial": 5},
    {"nome": "Esmeralda 16/18", "diferencial": 20},
    {"nome": "Ametista 14/15+MK", "diferencial": 15},
    {"nome": "Ametista 16/18", "diferencial": 35},
    {"nome": "Bourbon Amarelo 14/18+MK", "diferencial": 40},
]

HTML = '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>O\'Coffee | Painel do Mercado</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">\n<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>\n<style>\n:root{\n  --green-900:#0B3D1B; --green-800:#11551F; --green-700:#166528; --green-600:#1F7A34;\n  --brown-800:#4E342E; --brown-700:#654238; --gold-500:#D9A441; --gold-300:#F2D391;\n  --red-600:#B42318; --red-50:#FFF1F0; --green-50:#ECFDF3;\n  --bg:#F6F4EE; --card:#FFFFFF; --text:#17211B; --muted:#667085; --line:#E6E1D7;\n  --shadow:0 18px 45px rgba(16,24,40,.08); --shadow-soft:0 8px 24px rgba(16,24,40,.06);\n}\n*{box-sizing:border-box;margin:0;padding:0}\nbody{font-family:Inter,Arial,sans-serif;background:radial-gradient(circle at top left,#FDF8E8 0,#F6F4EE 35%,#F2F0EA 100%);color:var(--text);min-height:100vh}\n.topbar{height:6px;background:linear-gradient(90deg,var(--green-900),var(--green-600),var(--gold-500))}\n.hero{background:linear-gradient(135deg,var(--green-900),var(--green-700));color:#fff;padding:28px 38px 34px;position:relative;overflow:hidden}\n.hero:after{content:"";position:absolute;right:-90px;top:-120px;width:380px;height:380px;border-radius:50%;background:radial-gradient(circle,rgba(217,164,65,.35),rgba(217,164,65,0) 65%)}\n.hero-inner{max-width:1440px;margin:0 auto;position:relative;z-index:1;display:flex;align-items:center;justify-content:space-between;gap:22px}\n.brand{display:flex;align-items:center;gap:18px}\n.brand-logo{height:78px;max-width:190px;object-fit:contain;background:#fff;border-radius:18px;padding:10px;box-shadow:0 12px 32px rgba(0,0,0,.18)}\n.brand-mark{width:70px;height:70px;border-radius:18px;background:rgba(255,255,255,.12);display:grid;place-items:center;font-size:38px;border:1px solid rgba(255,255,255,.15)}\nh1{font-size:34px;line-height:1.08;font-weight:800;letter-spacing:-.04em}\n.subtitle{margin-top:8px;color:rgba(255,255,255,.78);font-size:15px}\n.hero-meta{display:flex;align-items:center;gap:10px;margin-top:14px;flex-wrap:wrap}\n.pill{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:7px 12px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.16);font-size:12px;font-weight:700;color:#fff}\n.dot{width:8px;height:8px;border-radius:50%;background:#32D583;box-shadow:0 0 0 5px rgba(50,213,131,.16)}\n.actions{display:flex;align-items:center;gap:10px}\n.btn{border:0;border-radius:12px;padding:11px 14px;font-weight:800;cursor:pointer;font-family:Inter}\n.btn-primary{background:var(--gold-500);color:#20180A}\n.btn-primary:hover{filter:brightness(1.04)}\n.statusText{font-size:12px;color:rgba(255,255,255,.78);text-align:right;margin-top:8px}\n.wrap{max-width:1440px;margin:0 auto;padding:28px 38px 38px}\n.section-title{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin:8px 0 16px}\n.section-title h2{font-size:22px;letter-spacing:-.03em}\n.section-title p{color:var(--muted);font-size:13px;margin-top:5px}\n.updated{color:var(--muted);font-size:12px}\n.kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-bottom:24px}\n.kpi{background:var(--card);border:1px solid rgba(230,225,215,.7);border-radius:22px;padding:22px;box-shadow:var(--shadow-soft);position:relative;overflow:hidden}\n.kpi:before{content:"";position:absolute;inset:0 0 auto 0;height:5px;background:linear-gradient(90deg,var(--green-700),var(--gold-500))}\n.kpi-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:18px}\n.kpi-title{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-weight:800}\n.kpi-icon{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;background:#F6F4EE;font-size:21px}\n.kpi-value{font-size:32px;font-weight:800;letter-spacing:-.04em;color:var(--green-800)}\n.kpi-detail{font-size:13px;color:var(--muted);margin-top:7px}\n.var{font-size:13px;font-weight:800;margin-top:8px}\n.var.up{color:var(--green-600)}.var.down{color:var(--red-600)}\n.main-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:22px;align-items:start}\n.panel{background:var(--card);border:1px solid rgba(230,225,215,.75);border-radius:22px;padding:24px;box-shadow:var(--shadow);margin-bottom:22px}\n.panel h3{font-size:20px;letter-spacing:-.03em;margin-bottom:6px}\n.panel-sub{font-size:13px;color:var(--muted);margin-bottom:18px}\n.chart-wrap{height:335px}\n.basis-hero{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:16px}\n.basis-card{border-radius:18px;padding:18px;background:#F9FAF7;border:1px solid #ECE7DD}\n.basis-card small{display:block;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}\n.basis-card strong{display:block;margin-top:10px;font-size:28px;letter-spacing:-.04em}\n.basis-card.physical strong{color:var(--brown-800)}\n.basis-card.exchange strong{color:var(--green-800)}\n.basis-card.basis.negative{background:var(--red-50);border-color:#F7C9C5}\n.basis-card.basis.positive{background:var(--green-50);border-color:#BFE6CC}\n.basis-card.basis.negative strong{color:var(--red-600)}\n.basis-card.basis.positive strong{color:var(--green-600)}\n.explain{display:grid;grid-template-columns:44px 1fr;gap:12px;background:#FFFAEB;border:1px solid #F7DDA0;border-radius:18px;padding:14px 16px;margin:14px 0 18px}\n.explain .i{width:44px;height:44px;border-radius:14px;background:#FFF3C4;display:grid;place-items:center;font-size:22px}\n.explain b{color:#7A4A00}\n.explain p{font-size:13px;color:#5C4630;line-height:1.45}\n.formula{margin-top:7px;font-size:12px;color:#7A4A00;font-weight:800}\n.refline{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}\n.refchip{font-size:12px;border-radius:999px;background:#F3F6F0;color:#344236;padding:7px 10px;border:1px solid #E3E9DE;font-weight:700}\ntable{width:100%;border-collapse:collapse}\nth{text-align:left;color:var(--muted);font-size:11px;letter-spacing:.08em;text-transform:uppercase;padding:12px 10px;border-bottom:1px solid var(--line)}\ntd{padding:13px 10px;border-bottom:1px solid #F0EDE6;font-size:14px}\ntbody tr:hover{background:#FBFAF6}\n.fw{font-weight:800}\n.badge{display:inline-flex;border-radius:999px;padding:4px 9px;font-size:12px;font-weight:800}\n.badge.pos{background:var(--green-50);color:var(--green-600)}\n.badge.neg{background:var(--red-50);color:var(--red-600)}\n.calc{background:linear-gradient(145deg,var(--brown-800),#3B241F);color:#fff}\n.calc h3{color:#fff}.calc .panel-sub{color:rgba(255,255,255,.68)}\n.form-row{display:grid;grid-template-columns:1fr 150px;gap:12px;margin-bottom:14px}\n.field label{display:block;font-size:12px;color:rgba(255,255,255,.7);font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-bottom:7px}\n.field select,.field input{width:100%;height:45px;border-radius:13px;border:1px solid rgba(255,255,255,.25);background:rgba(255,255,255,.10);color:#fff;padding:0 12px;font:600 14px Inter}\n.field option{color:#111}\n.calc-break{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}\n.mini{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.12);border-radius:15px;padding:13px;text-align:center}\n.mini small{display:block;color:rgba(255,255,255,.58);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}\n.mini strong{display:block;margin-top:6px;color:var(--gold-300);font-size:18px}\n.total{display:flex;justify-content:space-between;align-items:center;margin:15px 0 18px;padding:15px;border-radius:16px;border:1px solid rgba(217,164,65,.55);background:rgba(217,164,65,.16)}\n.total span{font-weight:700}\n.total strong{font-size:24px;color:var(--gold-300)}\n.calc table th{border-color:rgba(255,255,255,.16);color:rgba(255,255,255,.62)}\n.calc table td{border-color:rgba(255,255,255,.10);color:#fff}\n.calc tbody tr:hover{background:rgba(255,255,255,.05)}\n.news-list{display:grid;gap:12px}\n.news-item{padding:14px;border-radius:16px;background:#F9FAF7;border:1px solid #ECE7DD}\n.news-item a{color:var(--green-800);font-weight:800;text-decoration:none}\n.news-item a:hover{text-decoration:underline}\n.news-meta{margin-top:6px;font-size:12px;color:var(--muted);display:flex;gap:10px;flex-wrap:wrap}\n.footer{padding:28px 38px 40px;text-align:center;color:var(--muted);font-size:13px}\n.footer b{color:var(--green-800)}\n.footer a{color:var(--muted);text-decoration:none;border-bottom:1px dashed var(--muted)}\n.empty{color:var(--muted);font-style:italic}\n@media(max-width:1100px){\n  .main-grid{grid-template-columns:1fr}\n  .kpi-grid,.basis-hero{grid-template-columns:1fr}\n  .hero-inner{align-items:flex-start;flex-direction:column}\n  .actions{width:100%;justify-content:space-between}\n  .statusText{text-align:left}\n  .wrap,.hero{padding-left:20px;padding-right:20px}\n  .form-row{grid-template-columns:1fr}\n  .calc-break{grid-template-columns:1fr}\n}\n</style>\n</head>\n<body>\n<div class="topbar"></div>\n<header class="hero">\n  <div class="hero-inner">\n    <div class="brand">\n      {{LOGO}}\n      <div id="fallbackMark" class="brand-mark">☕</div>\n      <div>\n        <h1>O\'Coffee<br>Painel do Mercado</h1>\n        <p class="subtitle">Café NY, dólar PTAX, mercado físico, basis, diferenciais e notícias em uma visão única.</p>\n        <div class="hero-meta"><span class="pill"><span class="dot"></span> AO VIVO</span><span class="pill" id="lastUpdate">Carregando...</span></div>\n      </div>\n    </div>\n    <div>\n      <div class="actions"><button class="btn btn-primary" onclick="forceRefresh()">Atualizar agora</button></div>\n      <div class="statusText"><span id="statusText">Conectando...</span> • <span id="countdown">Próxima: --:--</span></div>\n    </div>\n  </div>\n</header>\n<main class="wrap">\n  <div class="section-title"><div><h2>Resumo executivo</h2><p>Os três indicadores principais para leitura rápida do mercado.</p></div><span class="updated" id="sourceLine">Fontes carregando...</span></div>\n  <section class="kpi-grid">\n    <article class="kpi" id="kpiCoffee"><div class="kpi-head"><div class="kpi-title">Café Arábica NY</div><div class="kpi-icon">☕</div></div><div id="coffeeValue" class="kpi-value">--</div><div id="coffeeVar" class="var"></div><div class="kpi-detail">Cotação em centavos por libra-peso (¢/lb)</div></article>\n    <article class="kpi" id="kpiDollar"><div class="kpi-head"><div class="kpi-title">Dólar PTAX Venda</div><div class="kpi-icon">💵</div></div><div id="dollarValue" class="kpi-value">--</div><div id="dollarVar" class="var"></div><div class="kpi-detail">Referência do Banco Central do Brasil</div></article>\n    <article class="kpi" id="kpiSaca"><div class="kpi-head"><div class="kpi-title">Saca Base 60 kg</div><div class="kpi-icon">📦</div></div><div id="sacaValue" class="kpi-value">--</div><div id="sacaDetail" class="kpi-detail">--</div></article>\n  </section>\n  <section class="main-grid">\n    <div>\n      <section class="panel"><h3>📊 Mercado físico vs. bolsa</h3><p class="panel-sub">Comparação direta entre a referência Cocapec e a referência de bolsa publicada pelo Notícias Agrícolas.</p><div class="basis-hero"><div class="basis-card physical"><small>Físico Cocapec</small><strong id="physVal">--</strong></div><div class="basis-card exchange"><small>Bolsa NY</small><strong id="nyVal">--</strong></div><div id="basisCard" class="basis-card basis"><small>Basis</small><strong id="basisVal">--</strong></div></div><div class="explain"><div class="i">ℹ️</div><div><p><b>Legenda do basis:</b> nesta tela, o basis é a diferença entre o valor físico da Cocapec e o valor de referência da bolsa. O valor de referência da bolsa usado no cálculo é o <b>valor do contrato indicado na linha "Referência"</b>, já convertido em R$/saca pelo Notícias Agrícolas.</p><div class="formula">Basis = Físico Cocapec − Bolsa NY do contrato de referência</div></div></div><div class="refline" id="physInfo"><span class="refchip">Carregando referência...</span></div><table><thead><tr><th>Data</th><th>Cocapec</th><th>Variação</th></tr></thead><tbody id="physBody"><tr><td colspan="3" class="empty">Carregando histórico...</td></tr></tbody></table></section>\n      <section class="panel"><h3>📈 Evolução recente</h3><p class="panel-sub">Histórico visual do café e da saca base.</p><div class="chart-wrap"><canvas id="priceChart"></canvas></div></section>\n    </div>\n    <aside>\n      <section class="panel calc"><h3>🧮 Calculadora por label</h3><p class="panel-sub">Selecione o label e informe a quantidade de sacas para ver o valor estimado.</p><div class="form-row"><div class="field"><label>Label</label><select id="labelSelect" onchange="calculateLabel()"></select></div><div class="field"><label>Sacas</label><input type="number" id="bagQty" value="100" min="0" oninput="calculateLabel()"></div></div><div class="calc-break"><div class="mini"><small>C-Price</small><strong id="calcC">--</strong></div><div class="mini"><small>Diferencial</small><strong id="calcD">--</strong></div><div class="mini"><small>FOB</small><strong id="calcF">--</strong></div></div><div class="calc-break" style="grid-template-columns:1fr 1fr"><div class="mini"><small>Saca USD</small><strong id="calcUsd">--</strong></div><div class="mini"><small>Saca BRL</small><strong id="calcBrl">--</strong></div></div><div class="total"><span>Total estimado</span><strong id="calcTotal">--</strong></div><table><thead><tr><th>Label</th><th>Dif.</th><th>Saca R$</th></tr></thead><tbody id="labelTable"></tbody></table></section>\n      <section class="panel"><h3>📰 Notícias do mercado</h3><p class="panel-sub">Principais atualizações capturadas automaticamente.</p><div id="newsBox" class="news-list"><div class="empty">Carregando notícias...</div></div></section>\n    </aside>\n  </section>\n</main>\n<footer class="footer">Desenvolvido para <b>Fazenda O\'Coffee</b> • Pedregulho — Alta Mogiana, SP<br><a href="/logout">Sair</a></footer>\n<script>\nlet chart=null, countdownTimer=null, interval=300, remaining=300, loading=false, coffee=0, dollar=0, labels=[];\nfunction brl(v,d=2,p=\'R$ \'){if(v===null||v===undefined||isNaN(v))return\'--\';return p+Number(v).toLocaleString(\'pt-BR\',{minimumFractionDigits:d,maximumFractionDigits:d})}\nfunction usd(v){return v==null||isNaN(v)?\'--\':\'US$ \'+Number(v).toLocaleString(\'pt-BR\',{minimumFractionDigits:2,maximumFractionDigits:2})}\nfunction pct(v){if(v===null||v===undefined||isNaN(v))return\'<span class="var">--</span>\';let c=v>0?\'up\':v<0?\'down\':\'\';let s=v>0?\'+\':\'\';return `<span class="var ${c}">${s}${Number(v).toFixed(2)}%</span>`}\nasync function loadData(){if(loading)return;loading=true;document.getElementById(\'statusText\').textContent=\'Atualizando...\';try{let r=await fetch(\'/api/dados\',{cache:\'no-store\'});if(!r.ok)throw new Error(\'HTTP \'+r.status);let d=await r.json();render(d);document.getElementById(\'statusText\').textContent=\'Conectado\';}catch(e){document.getElementById(\'statusText\').textContent=\'Erro de conexão\';}loading=false;startCountdown();}\nfunction render(d){labels=d.labels||[];if(d.cafe&&d.cafe.sucesso){coffee=d.cafe.preco;document.getElementById(\'coffeeValue\').textContent=Number(coffee).toLocaleString(\'pt-BR\',{minimumFractionDigits:2})+\' ¢/lb\';document.getElementById(\'coffeeVar\').innerHTML=pct(d.cafe.variacao)}if(d.dolar&&d.dolar.sucesso){dollar=d.dolar.preco;document.getElementById(\'dollarValue\').textContent=brl(dollar,4);document.getElementById(\'dollarVar\').innerHTML=pct(d.dolar.variacao)}if(d.saca&&d.saca.brl){document.getElementById(\'sacaValue\').textContent=brl(d.saca.brl);document.getElementById(\'sacaDetail\').textContent=usd(d.saca.usd)+\' • 132,277 lbs\'}renderPhysical(d.fisico||{});renderChart(d.historico||{});renderLabels();renderNews(d.noticias||[]);document.getElementById(\'lastUpdate\').textContent=\'Última atualização: \'+d.timestamp;document.getElementById(\'sourceLine\').textContent=\'Yahoo Finance • BCB PTAX • Notícias Agrícolas\';interval=d.intervalo||300;calculateLabel();}\nfunction renderPhysical(f){let h=f.hoje;if(!h){document.getElementById(\'physInfo\').innerHTML=\'<span class="refchip">Dados indisponíveis</span>\';return}document.getElementById(\'physVal\').textContent=brl(h.fisico_preco);document.getElementById(\'nyVal\').textContent=brl(h.bolsa_saca_brl);let bc=document.getElementById(\'basisCard\'),bv=document.getElementById(\'basisVal\'),diff=h.diferenca;bc.className=\'basis-card basis \'+(diff>=0?\'positive\':\'negative\');if(diff!==null&&diff!==undefined){let s=diff>=0?\'+\':\'\';bv.textContent=s+brl(diff,0,\'R$ \')+\' (\'+s+Number(h.diferenca_pct||0).toFixed(1)+\'%)\'}else{bv.textContent=\'--\'}document.getElementById(\'physInfo\').innerHTML=`<span class="refchip">Contrato: ${h.contrato||\'--\'}</span><span class="refchip">Bolsa: ${h.cents_lb||\'--\'} ¢/lb</span><span class="refchip">Dólar NA: ${h.dolar_usado||\'--\'}</span><span class="refchip">Data: ${h.data||\'--\'}</span>`;let rows=(f.historico||[]).map(r=>{let v=parseFloat(String(r.variacao||\'0\').replace(\',\',\'.\'));let cls=v>=0?\'pos\':\'neg\';let txt=(v>0?\'+\':\'\')+(r.variacao||\'0,00\')+\'%\';return `<tr><td class="fw">${r.data}</td><td class="fw">${brl(r.preco)}</td><td><span class="badge ${cls}">${txt}</span></td></tr>`}).join(\'\');document.getElementById(\'physBody\').innerHTML=rows||\'<tr><td colspan="3" class="empty">Histórico indisponível.</td></tr>\'}\nfunction renderLabels(){let sel=document.getElementById(\'labelSelect\'),cur=sel.value;sel.innerHTML=\'\';labels.forEach(l=>{let o=document.createElement(\'option\');o.value=l.nome;o.textContent=l.nome+(l.diferencial===0?\' • base\':` • +${l.diferencial} ¢/lb`);sel.appendChild(o)});if(cur)sel.value=cur;document.getElementById(\'labelTable\').innerHTML=labels.map(l=>{let f=coffee+l.diferencial,u=f/100*132.277,b=u*dollar;return `<tr><td>${l.nome}</td><td>${l.diferencial===0?\'Base\':\'+\'+l.diferencial}</td><td class="fw">${brl(b)}</td></tr>`}).join(\'\')}\nfunction calculateLabel(){let l=labels.find(x=>x.nome===document.getElementById(\'labelSelect\').value);if(!l||!coffee||!dollar)return;let f=coffee+l.diferencial,u=f/100*132.277,b=u*dollar,q=parseFloat(document.getElementById(\'bagQty\').value)||0;document.getElementById(\'calcC\').textContent=coffee.toFixed(2)+\' ¢\';document.getElementById(\'calcD\').textContent=l.diferencial===0?\'0\':`+${l.diferencial} ¢`;document.getElementById(\'calcF\').textContent=f.toFixed(2)+\' ¢\';document.getElementById(\'calcUsd\').textContent=usd(u);document.getElementById(\'calcBrl\').textContent=brl(b);document.getElementById(\'calcTotal\').textContent=brl(q*b)}\nfunction renderChart(h){let labs=(h.labels||[]).map(d=>{let p=d.split(\'-\');return p.length===3?p[2]+\'/\'+p[1]:d});let ctx=document.getElementById(\'priceChart\');if(chart){chart.data.labels=labs;chart.data.datasets[0].data=h.cafe_precos||[];chart.data.datasets[1].data=h.saca_valores||[];chart.update(\'none\');return}chart=new Chart(ctx,{type:\'line\',data:{labels:labs,datasets:[{label:\'Café (¢/lb)\',data:h.cafe_precos||[],borderColor:\'#4E342E\',backgroundColor:\'rgba(78,52,46,.10)\',fill:true,tension:.35,pointRadius:2,yAxisID:\'y\'},{label:\'Saca base (R$)\',data:h.saca_valores||[],borderColor:\'#D9A441\',backgroundColor:\'rgba(217,164,65,.12)\',fill:true,tension:.35,pointRadius:2,yAxisID:\'y1\'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{usePointStyle:true,boxWidth:8,font:{family:\'Inter\'}}}},interaction:{mode:\'index\',intersect:false},scales:{x:{grid:{display:false}},y:{position:\'left\',grid:{color:\'rgba(16,24,40,.06)\'}},y1:{position:\'right\',grid:{drawOnChartArea:false}}}}})}\nfunction renderNews(ns){let box=document.getElementById(\'newsBox\');box.innerHTML=ns.length?ns.map(n=>`<article class="news-item"><a href="${n.link}" target="_blank">${n.titulo}</a><div class="news-meta"><span>${n.fonte}</span><span>${n.data}</span></div></article>`).join(\'\'):\'<div class="empty">Sem notícias disponíveis.</div>\'}\nfunction startCountdown(){remaining=interval;if(countdownTimer)clearInterval(countdownTimer);countdownTimer=setInterval(()=>{remaining--;let m=Math.floor(remaining/60),s=remaining%60;document.getElementById(\'countdown\').textContent=`Próxima: ${m}:${String(s).padStart(2,\'0\')}`;if(remaining<=0){clearInterval(countdownTimer);loadData()}},1000)}\nfunction forceRefresh(){if(countdownTimer)clearInterval(countdownTimer);loadData()}\nwindow.addEventListener(\'load\',()=>{if(document.querySelector(\'.brand-logo\'))document.getElementById(\'fallbackMark\').style.display=\'none\';loadData()});\n</script>\n</body>\n</html>\n'

cache = {"dados": None, "timestamp": 0, "logo_base64": ""}

def log(msg):
    print(msg, flush=True)

def get_text(url, timeout=15):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    r.raise_for_status()
    return r.text

def get_json(url, params=None, timeout=15):
    r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    r.raise_for_status()
    return r.json()

def parse_money(s):
    try:
        return float(str(s).replace('.', '').replace(',', '.'))
    except Exception:
        return None

def carregar_logo():
    for nome in ['logo.png', 'logo.jpg', 'logo.jpeg', 'logo.svg', 'logo.webp']:
        p = os.path.join(PASTA_APP, nome)
        if os.path.exists(p):
            ext = os.path.splitext(p)[1].lower()
            mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp'}.get(ext, 'image/png')
            data = base64.b64encode(open(p, 'rb').read()).decode('utf-8')
            log('Logo encontrada: ' + p)
            return f'<img src="data:{mime};base64,{data}" alt="Logo O Coffee" class="brand-logo">'
    log('Logo não encontrada (opcional).')
    return ''

def buscar_cafe():
    try:
        data = get_json('https://query1.finance.yahoo.com/v8/finance/chart/KC=F', {'range': '1mo', 'interval': '1d', 'includePrePost': 'false'})
        res = data['chart']['result'][0]
        meta = res['meta']
        ts = res['timestamp']
        closes = res['indicators']['quote'][0]['close']
        hist = []
        for t, c in zip(ts, closes):
            if c is not None:
                hist.append({'data': datetime.fromtimestamp(t).strftime('%Y-%m-%d'), 'preco': round(float(c), 2)})
        atual = float(meta.get('regularMarketPrice') or closes[-1])
        ant = float(meta.get('previousClose') or closes[-2] or atual)
        var = ((atual - ant) / ant * 100) if ant else 0
        return {'preco': round(atual, 2), 'variacao': round(var, 2), 'historico': hist, 'sucesso': True}
    except Exception as e:
        log('Erro café: ' + str(e))
        return {'preco': None, 'variacao': None, 'historico': [], 'sucesso': False}

def ptax_dia(dt):
    try:
        ds = dt.strftime('%m-%d-%Y')
        data = get_json('https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@d)', {'@d': "'" + ds + "'", '$format': 'json'}, 10)
        vals = data.get('value', [])
        if vals:
            u = vals[-1]
            return {'venda': round(float(u['cotacaoVenda']), 4), 'compra': round(float(u['cotacaoCompra']), 4)}
    except Exception:
        pass
    return None

def buscar_ptax():
    hoje = datetime.now()
    atual = None
    ant = None
    for i in range(10):
        r = ptax_dia(hoje - timedelta(days=i))
        if r and atual is None:
            atual = r
        elif r and ant is None:
            ant = r
            break
    if not atual:
        return {'preco': None, 'variacao': None, 'sucesso': False}
    var = ((atual['venda'] - ant['venda']) / ant['venda'] * 100) if ant else 0
    return {'preco': atual['venda'], 'compra': atual['compra'], 'variacao': round(var, 2), 'sucesso': True}

def mercado_fisico():
    result = {'hoje': None, 'historico': []}
    bolsa = {'saca': None, 'contrato': None, 'cents': None, 'dolar': None, 'data': None}
    try:
        html = get_text('https://www.noticiasagricolas.com.br/cotacoes/cafe/cafe-bolsa-de-nova-iorque-nybot')
        m = re.search(r'Fechamento:\s*(\d{2}/\d{2}/\d{4})', html)
        bolsa['data'] = m.group(1) if m else None
        m = re.search(r'D.lar:\s*([\d,.]+)', html)
        bolsa['dolar'] = m.group(1) if m else None
        rows = re.findall(r'((?:Janeiro|Fevereiro|Mar.o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)/\d{2})\s*</td>\s*<td[^>]*>\s*([\d.,]+)\s*</td>\s*<td[^>]*>\s*([\d.,]+)', html, re.I)
        if not rows:
            rows = re.findall(r'((?:Janeiro|Fevereiro|Mar.o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)/\d{2})\s+([\d.,]+)\s+([\d.,]+)', re.sub(r'<[^>]+>', ' ', html), re.I)
        if rows:
            ref = rows[1] if len(rows) >= 2 else rows[0]
            bolsa.update({'contrato': ref[0], 'cents': ref[1], 'saca': parse_money(ref[2])})
    except Exception as e:
        log('Erro bolsa NA: ' + str(e))
    fisico = None
    try:
        html = get_text('https://www.noticiasagricolas.com.br/cotacoes/cafe/cafe-arabica-mercado-fisico-tipo-6-duro')
        blocks = re.split(r'Fechamento:\s*', html)
        for block in blocks[1:]:
            dm = re.search(r'(\d{2}/\d{2}/\d{4})', block)
            if not dm:
                continue
            date = dm.group(1)
            fm = re.search(r'Franca/SP.*?(\d{1,2}\.?\d{3},\d{2}).*?([+-]?\d+[,.]\d+|0,00|-)', block, re.S)
            if fm:
                price = parse_money(fm.group(1))
                var = fm.group(2) if fm.group(2) else '-'
                if price is not None:
                    result['historico'].append({'data': date, 'preco': price, 'variacao': var.replace('.', ',')})
                    if fisico is None:
                        fisico = price
            if len(result['historico']) >= 7:
                break
    except Exception as e:
        log('Erro físico NA: ' + str(e))
    if fisico is not None:
        diff = pct = None
        if bolsa['saca']:
            diff = round(fisico - bolsa['saca'], 2)
            pct = round(diff / bolsa['saca'] * 100, 1)
        result['hoje'] = {'data': bolsa['data'] or (result['historico'][0]['data'] if result['historico'] else ''), 'fisico_preco': fisico, 'bolsa_saca_brl': bolsa['saca'], 'contrato': bolsa['contrato'], 'cents_lb': bolsa['cents'], 'dolar_usado': bolsa['dolar'], 'diferenca': diff, 'diferenca_pct': pct}
    return result

def noticias():
    try:
        txt = get_text('https://news.google.com/rss/search?q=caf%C3%A9+ar%C3%A1bica+mercado&hl=pt-BR&gl=BR&ceid=BR:pt-419', 10)
        root = ET.fromstring(txt)
        out = []
        for item in root.findall('.//item')[:8]:
            out.append({'titulo': item.findtext('title') or '', 'link': item.findtext('link') or '#', 'data': item.findtext('pubDate') or '', 'fonte': item.findtext('source') or 'Fonte'})
        return out
    except Exception as e:
        log('Erro notícias: ' + str(e))
        return []

def coletar():
    now = time.time()
    if cache['dados'] and now - cache['timestamp'] < CACHE_DURACAO:
        return cache['dados']
    cafe = buscar_cafe()
    dolar = buscar_ptax()
    fis = mercado_fisico()
    news = noticias()
    su = sb = None
    if cafe.get('sucesso') and dolar.get('sucesso'):
        su = round(cafe['preco'] / 100 * LIBRAS_POR_SACA, 2)
        sb = round(su * dolar['preco'], 2)
    hist = cafe.get('historico', [])
    svals = []
    for h in hist:
        rate = dolar.get('preco') if dolar.get('sucesso') else 5.5
        svals.append(round(h['preco'] / 100 * LIBRAS_POR_SACA * rate, 2))
    dados = {'cafe': cafe, 'dolar': dolar, 'saca': {'usd': su, 'brl': sb}, 'historico': {'labels': [h['data'] for h in hist], 'cafe_precos': [h['preco'] for h in hist], 'saca_valores': svals}, 'labels': LABELS, 'fisico': fis, 'noticias': news, 'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'), 'intervalo': INTERVALO_ATUALIZACAO}
    cache['dados'] = dados
    cache['timestamp'] = now
    return dados

def verificar_auth(self):
    """Retorna True se autenticado, False se não."""
    auth = self.headers.get('Authorization', '')
    if auth.startswith('Basic '):
        token = auth[6:].strip()
        if token == AUTH_TOKEN:
            return True
    return False

def pedir_login(self, mensagem="Painel O'Coffee"):
    self.send_response(401)
    self.send_header('WWW-Authenticate', f'Basic realm="{mensagem}"')
    self.send_header('Content-Type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write('<h1>Acesso restrito</h1><p>É necessário fazer login para acessar o painel.</p>'.encode('utf-8'))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlparse(self.path).path

        # Endpoint de logout
        if path == '/logout':
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Saindo..."')
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write('<h1>Sessão encerrada</h1><p>Você saiu do painel. <a href="/">Entrar novamente</a></p>'.encode('utf-8'))
            return

        # Verificar autenticação
        if not verificar_auth(self):
            pedir_login(self)
            return

        if path in ('/', '/index.html'):
            html = HTML.replace('{{LOGO}}', cache.get('logo_base64') or '')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif path == '/api/dados':
            data = json.dumps(coletar(), ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(data.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def main():
    log('=' * 60)
    log("O'COFFEE - PAINEL DO MERCADO | VERSÃO WEB")
    log('=' * 60)
    log(f'Usuário: {PAINEL_USER}')
    log(f'Porta: {PORT}')
    log(f'Pasta: {PASTA_APP}')
    cache['logo_base64'] = carregar_logo()
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    log(f'Servidor rodando em http://0.0.0.0:{PORT}')
    log('Pressione Ctrl+C para parar.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log('Encerrado.')

if __name__ == '__main__':
    main()
