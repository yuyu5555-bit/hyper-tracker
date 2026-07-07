import feedparser
import google.generativeai as genai
from datetime import datetime, timezone, timedelta
import os

# ==========================================
# 0. AI (Gemini) のセットアップ
# ==========================================
# GitHub環境ならSecretsから、Colabテストなら直書きのキーを使用
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
JST = timezone(timedelta(hours=+9), 'JST')

# ==========================================
# 1. 監視メディア (全14媒体)
# ==========================================
MEDIA_FEEDS = [
    {"name": "ITmedia", "url": "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml"},
    {"name": "東洋経済", "url": "https://toyokeizai.net/list/feed/rss"},
    {"name": "日経xTECH", "url": "https://xtech.nikkei.com/rss/index.rdf"},
    {"name": "EE Times", "url": "https://eetimes.itmedia.co.jp/rss/2.0/ee_latest.xml"},
    {"name": "Reuters", "url": "https://assets.wor.jp/rss/rdf/reuters/technology.rdf"},
    {"name": "Bloomberg/WSJ等", "url": "https://news.yahoo.co.jp/rss/categories/business.xml"},
    {"name": "TrendForce", "url": "https://insights.trendforce.com/feed"},
    {"name": "DigiTimes", "url": "https://www.digitimes.com/rss/daily.xml"},
    {"name": "SemiEngineering", "url": "https://semiengineering.com/feed/"},
    {"name": "DataCenterDynamics", "url": "https://www.datacenterdynamics.com/en/rss.xml"},
    {"name": "ServeTheHome", "url": "https://www.servethehome.com/feed/"},
    {"name": "Wccftech", "url": "https://wccftech.com/feed/"}
]

# ==========================================
# 2. 厳格キーワード (超完全版：重複排除済)
# ==========================================
STRICT_KEYWORDS = [
    # --- 企業名（グローバル・国内・台湾・韓国） ---
    "KOKUSAI", "AMAT", "Applied Materials", "東京エレクトロン", "ディスコ", "ウシオ電機", "AIメカテック", 
    "アルバック", "Lam Research", "ラムリサーチ", "SUMCO", "AGC", "日本電気硝子", "HOYA", "JX金属", "日東紡", 
    "住友化学", "Intel", "インテル", "Samsung", "サムスン", "アドバンテスト", "Teradyne", "テラダイン", 
    "東京精密", "日本マイクロニクス", "FormFactor", "Camtek", "Onto Innovation", "TOWA", "芝浦メカトロニクス", 
    "ニコン", "ASML", "FUJI", "住友ベークライト", "デンカ", "日東電工", "信越化学", "イビデン", "京セラ", "味の素", 
    "レゾナック", "三菱ガス化学", "三井金属", "太陽HD", "メック", "JCU", "山一電機", "エンプラス", "日本電子材料", 
    "COHU", "テラプローブ", "三井ハイテック", "タカトリ", "リンテック", "湖北工業", "精工技研", "Broadcom", 
    "ブロードコム", "Marvell", "マーベル", "Lumentum", "ルーメンタム", "Coherent", "コヒレント", "TE Connectivity", 
    "Cisco", "POET", "AAOI", "デクセリアルズ", "MACOM", "サムコ", "santec", "QDレーザ", "住友電工", "ラサ工業", 
    "フジクラ", "古河電工", "OKI", "サンコール", "横河電機", "NEC", "アンリツ", "新東工業", "オキサイド", 
    "NVIDIA", "エヌビディア", "AMD", "Micron", "マイクロン", "SK Hynix", "Supermicro", "スーパーマイクロ", 
    "オン・セミコンダクター", "ウルフスピード", "インフィニオン", "STM", "高砂熱学工業", "ダイキン", "三櫻工業", 
    "テクニスコ", "キャリア・グローバル", "バーティブ", "ニデック", "オルガノ", "栗田工業", "関電工", "きんでん", 
    "三機工業", "大林組", "鹿島", "清水建設", "太平洋セメント", "住友大阪セメント", "中国電力", "ブルーム・エナジー",
    "Microsoft", "Amazon", "Google", "Meta", "TSMC", "台積電", "Foxconn", "鴻海", "Quanta", "広達", "Wistron", 
    "緯創", "AWS", "ASE", "SPIL", "Powertech", "Unimicron", "長興", "三福化学", "中華化学", "盛毅", 
    "Walsin Technology", "華新科技",

    # --- アーキテクチャ・AIインフラ・トレンド ---
    "GB300", "Blackwell", "Vera Rubin", "Rubin", "Hopper", "NVLシリーズ", "NVIDIAプラットフォーム", "Kyber",
    "Spectrum-X", "Trainium", "AIインフラ", "AIファクトリー", "AI Factory", "計算資源不足", "トークン生成需要", 
    "エージェントAI", "Agent AI", "フィジカルAI", "Physical AI", "Capex", "Hyperscalers", "AIサーバー", "Inference",
    "推論", "訓練需要", "資本市場依存", "GIGAファブ", "規模優位性", "歩留まり", "技術力", "受注殺到", "成長加速", 
    "生産能力不足", "波及効果", "異次元成長", "出荷急増", "認証通過", "代替検証", "供給逼迫", "値上げ",

    # --- 工程・製造技術（前・中・後工程） ---
    "前工程", "後工程", "中工程", "ファウンドリー", "テスト工程", "パッケージング", "先進パッケージング", 
    "先端プロセス", "成熟プロセス", "3nm", "2nm", "垂直統合", "国内化", "設計不備", "シリコンインゴット", "切断", 
    "研磨", "ウェハ表面の酸化", "薄膜形成", "フォトレジスト塗布", "露光", "EUV露光", "現像", "エッチング", 
    "フォトレジスト除去", "イオン注入", "平坦化", "CMP", "電極形成", "検査", "最終検査", "ダイシング", 
    "ワイヤーボンディング", "モールディング", "封止", "モールド", "ハイブリッド接合",

    # --- 装置・コンポーネント・部品 ---
    "CVD装置", "ALD", "バッチ式", "ウエットエッチング装置", "コーターデベロッパー", "塗布現像装置", "スクラバー", 
    "バッチ式洗浄装置", "フラッシュランプアニール", "枚葉式洗浄装置", "レジスト剥離装置", "露光装置", 
    "SoCテスタ", "プローバ", "プローブカード", "光学式外観検査装置", "直接描画装置", "リニアコータ", 
    "インクジェット印刷機", "デジタル印刷機", "UVインクジェット印刷機", "テラファブ", "PILLAR",
    "ウエハー", "シリコンウェハ", "ICチップ", "IC", "フォトマスク", "レジスト", "パワーデバイス", "ロジック", 
    "イメージセンサー", "CCDセンサー", "CMOSセンサー", "IoT", "MEMS", "SAWデバイス", "タッチパネル", 
    "フラットパネルディスプレー", "有機ELディスプレー", "TFT LCD", "プリント基板", "プリント配線板", 
    "バックプレーン", "受動部品", "MLCC", "電源", "液冷", "水冷", "チラー", "CDU", "光通信", "光エンジン", 
    "外部レーザー光源", "海底ケーブル", "NVLink", "UBB",

    # --- パッケージング規格・メモリ・化学材料 ---
    "CoPoS", "CoWoS", "FOPLP", "PLP", "HBM", "ガラス基板", "RDL", "インターポーザ", "TSV", "TGV", "FC-BGA", 
    "ABF", "CPO", "Co-Packaged Optics", "AIヘテロジニアス統合", "メモリ中心シフト", "SRAM", "DRAM", "NAND", 
    "Flash", "フラッシュメモリー", "高帯域メモリ", "HBF", "DDR5", "LPDDR5X", "scratchpad", "300層", "SSD", 
    "KVキャッシュ", "NANDブラックホール", "SRAM爆盛り", "Flashスタック", "CCL", "銅箔", "高周波基材", 
    "液体封止材", "TMAH", "硫酸", "化学品"
]

print(">> 超・完全版フィルターでニュースを抽出中...")
all_news = []

# ==========================================
# 3. ニュース抽出プロセス
# ==========================================
for feed in MEDIA_FEEDS:
    try:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            title = entry.title
            summary = entry.get('summary', '')
            text_to_check = (title + " " + summary).lower()
            matched_tags = [kw for kw in STRICT_KEYWORDS if kw.lower() in text_to_check]
            
            if matched_tags:
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        dt = datetime(*entry.published_parsed[:6]).replace(tzinfo=timezone.utc).astimezone(JST)
                    else:
                        dt = datetime.now(JST)
                except:
                    dt = datetime.now(JST)
                    
                all_news.append({
                    "source": feed["name"], "title": title, "link": entry.link,
                    "summary_raw": summary, "date": f"{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}", 
                    "timestamp": dt.timestamp(), "matched": list(set(matched_tags))
                })
    except Exception as e:
        pass

seen_links = set()
unique_news = []
for news in sorted(all_news, key=lambda x: x["timestamp"], reverse=True):
    if news["link"] not in seen_links:
        seen_links.add(news["link"])
        unique_news.append(news)

# ==========================================
# 4. AI要約生成 (上位10件)
# ==========================================
print(">> AIが相場への影響を分析中...")
for i, news in enumerate(unique_news[:30]):
    if i < 10: 
        prompt = f"""
        あなたは冷徹な機関投資家のアナリストです。以下の半導体関連ニュースから、
        相場やサプライチェーンへの影響（誰が得をして誰が損をするか、どの工程に影響するか）を分析し、
        感情を交えず、客観的な事実に基づいた箇条書き3行のみで出力してください。
        
        【タイトル】: {news['title']}
        【本文】: {news['summary_raw']}
        """
        try:
            response = model.generate_content(prompt)
            ai_text = response.text.replace('\n', '<br>').replace('*', '•')
            news['ai_summary'] = f'<div style="background: #1a202c; padding: 10px; border-left: 3px solid #63b3ed; font-size: 0.8rem; color: #cbd5e0; margin-top: 8px; line-height: 1.5;">{ai_text}</div>'
            print(f"[{i+1}/10] {news['title'][:15]}... の要約完了")
        except Exception as e:
            news['ai_summary'] = '<div style="font-size:0.75rem; color:#94a3b8;">(AI要約をスキップしました)</div>'
    else:
        news['ai_summary'] = ''

# ==========================================
# 5. HTMLダッシュボード生成
# ==========================================
news_html_content = ""
for news in unique_news[:30]:
    tags_string = " ".join([f"#{t}" for t in news["matched"]])
    
    source_style = "color: #e2b973; border: 1px solid #e2b973;"
    if "Yahoo" in news["source"] or "国内" in news["source"]:
        source_style = "color: #a0aec0; border: 1px solid #a0aec0;"
    elif news["source"] in ["TrendForce", "DigiTimes", "SemiEngineering", "DataCenterDynamics", "ServeTheHome"]:
        source_style = "color: #63b3ed; border: 1px solid #63b3ed; background: rgba(99,179,237,0.1);"

    news_html_content += f"""
    <div class="news-item" style="padding: 16px 0; border-bottom: 1px solid #232a3b;">
        <div style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
            <span class="source" style="font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: bold; {source_style}">{news['source']}</span>
            <span class="date" style="font-size: 0.75rem; color: #94a3b8;">{news['date']}</span>
        </div>
        <h3 class="title" style="font-size: 0.95rem; margin: 6px 0; line-height: 1.45;"><a href="{news['link']}" target="_blank" style="color: #e2e8f0; text-decoration: none; font-weight: 600;">{news['title']} ↗</a></h3>
        <div class="matched-tags" style="font-size: 0.7rem; color: #4fd1c5; font-weight: 500; letter-spacing: 0.05em; margin-bottom: 4px; line-height: 1.4;">検知材料: {tags_string}</div>
        {news.get('ai_summary', '')}
    </div>
    """

if not unique_news:
    news_html_content = '<div style="padding: 30px; color: #f56565; text-align: center;">現在、指定されたキーワードに一致する新着ニュースはありません。</div>'

full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>半導体ニューストラッカー (AI搭載版)</title>
</head>
<body style="background: #0a0d14; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 16px;">
<div style="max-width: 650px; margin: 0 auto; padding-bottom: 60px;">

    <div style="border-bottom: 1px solid #232a3b; padding-bottom: 14px; margin-bottom: 20px;">
        <div style="font-size: 0.65rem; color: #94a3b8; letter-spacing: 0.1em; font-weight: bold;">AI ANALYZER & HIGH-PRECISION FILTER</div>
        <h1 style="margin: 4px 0; font-size: 1.4rem; font-weight: 700;">半導体ニュース<span style="color: #e2b973;">トラッカー</span></h1>
        <div style="font-size: 0.75rem; color: #94a3b8;">データ更新時刻: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #232a3b; padding-bottom: 6px; margin-bottom: 10px;">
        <h2 style="font-size: 1.05rem; font-weight: 600; margin: 0;">自動ヘッドライン (AI相場分析)</h2>
        <span style="font-size: 0.7rem; color: #94a3b8;">上位10件を自動要約</span>
    </div>
    
    <div>
        {news_html_content}
    </div>

</div>
</body>
</html>
"""

with open('ai_tracker.html', 'w', encoding='utf-8') as f:
    f.write(full_html)
print(">> 完了！ 'ai_tracker.html' をダウンロードして開いてください。")
