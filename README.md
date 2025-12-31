# Airdrop Discovery System

DeFilLama APIを活用して、将来エアドロップの可能性がある有望なプロジェクトを自動的に発見・ランキングするシステム。

## 機能

- 🪂 **トークン未発行プロジェクト検出** - まだトークンを発行していないプロジェクトを自動抽出
- 💰 **VC分析** - a16z、Paradigm等のTier-1 VCが投資しているプロジェクトを優先表示
- 📊 **スコアリング** - TVL成長率、調達額、VCの質を基にAirdrop可能性をスコア化
- 🎨 **HTMLダッシュボード** - 視覚的にランキングを確認できるWebページを生成

## セットアップ

```bash
# 依存関係をインストール
pip install -r requirements.txt
```

## 使い方

```bash
# ダッシュボードを生成してブラウザで開く
python main.py

# コンソールでトップ20を確認
python main.py --console --top 20

# API接続をテスト
python main.py --test-api

# キャッシュをクリアして最新データを取得
python main.py --clear-cache
```

## スコアリング基準

| 基準 | 最大点数 | 説明 |
|------|---------|------|
| トークン未発行 | +30 | まだ独自トークンがないプロジェクト |
| 資金調達額 | +25 | $10M以上の調達で高得点 |
| Tier-1 VC支援 | +20 | Paradigm, a16z等の参加 |
| TVL成長率 | +15 | 7日間でのTVL成長 |
| リスト新しさ | +10 | 6ヶ月以内にリストされた |

## ファイル構成

```
├── main.py              # エントリーポイント
├── defillama_client.py  # DeFilLama API クライアント
├── airdrop_scorer.py    # スコアリングエンジン
├── dashboard.py         # HTMLダッシュボード生成
├── requirements.txt     # Python依存関係
└── output/              # 生成されたダッシュボード
```

## データソース

- [DeFilLama](https://defillama.com/) - DeFiプロトコルのTVL・資金調達データ
