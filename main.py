"""
Airdrop Discovery System - Main Entry Point
Orchestrates data fetching, scoring, and dashboard generation.
"""

import argparse
import webbrowser
import sys
from pathlib import Path
from datetime import datetime

from defillama_client import DeFilLamaClient
from airdrop_scorer import AirdropScorer
from dashboard import DashboardGenerator


def print_banner():
    """Print the application banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🪂  AIRDROP DISCOVERY SYSTEM  🪂                            ║
║                                                               ║
║   DeFilLama データを活用した有望プロジェクト発見ツール       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def test_api():
    """Test API connectivity."""
    print("\n[Test] API接続テスト...")
    client = DeFilLamaClient()
    
    try:
        protocols = client.get_protocols(use_cache=False)
        print(f"  ✓ Protocols エンドポイント: {len(protocols)} 件取得")
        
        raises = client.get_raises(use_cache=False)
        print(f"  ✓ Raises エンドポイント: {len(raises.get('raises', []))} 件取得")
        
        print("\n[Test] API接続テスト完了 ✓")
        return True
    except Exception as e:
        print(f"\n[Error] API接続エラー: {e}")
        return False


def test_scoring():
    """Test the scoring system."""
    print("\n[Test] スコアリングテスト...")
    client = DeFilLamaClient()
    
    protocols = client.get_protocols()
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    scorer = AirdropScorer(protocols, raises)
    
    # Score all protocols
    scores = scorer.score_all_protocols()
    
    print(f"\n  分析対象プロトコル: {len(scores)} 件")
    print(f"  トークン未発行: {len([s for s in scores if s.is_tokenless])} 件")
    print(f"  Tier-1 VC支援: {len([s for s in scores if s.tier1_vcs])} 件")
    print(f"  高スコア (50+): {len([s for s in scores if s.total_score >= 50])} 件")
    
    print("\n  トップ5プロジェクト:")
    for i, s in enumerate(scores[:5], 1):
        tokenless_mark = "🟢" if s.is_tokenless else "⚪"
        print(f"    {i}. {tokenless_mark} {s.protocol_name} (Score: {s.total_score})")
    
    print("\n[Test] スコアリングテスト完了 ✓")
    return True


def generate_dashboard(open_browser: bool = True, top_n: int = 100):
    """Generate the HTML dashboard."""
    print("\n[Dashboard] ダッシュボード生成中...")
    
    client = DeFilLamaClient()
    
    print("  - プロトコルデータ取得中...")
    protocols = client.get_protocols()
    
    print("  - 資金調達データ取得中...")
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    print("  - スコアリング実行中...")
    scorer = AirdropScorer(protocols, raises)
    scores = scorer.score_all_protocols()[:top_n]
    
    print("  - HTML生成中...")
    generator = DashboardGenerator()
    output_path = generator.save_dashboard(scores)
    
    print(f"\n[Dashboard] 生成完了: {output_path}")
    
    if open_browser:
        print("[Dashboard] ブラウザで開きます...")
        webbrowser.open(f"file://{output_path.absolute()}")
    
    return output_path


def print_console_report(limit: int = 20):
    """Print a console report of top airdrop candidates."""
    print("\n" + "=" * 70)
    print("  TOP AIRDROP CANDIDATES")
    print("=" * 70)
    
    client = DeFilLamaClient()
    protocols = client.get_protocols()
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    scorer = AirdropScorer(protocols, raises)
    scores = scorer.score_all_protocols()[:limit]
    
    for i, s in enumerate(scores, 1):
        tokenless = "🟢 NO TOKEN" if s.is_tokenless else "⚪ Has Token"
        
        if s.has_points:
            tokenless += " | 🎁 POINTS"
            
        # Format TVL
        if s.tvl >= 1_000_000_000:
            tvl_str = f"${s.tvl / 1_000_000_000:.2f}B"
        elif s.tvl >= 1_000_000:
            tvl_str = f"${s.tvl / 1_000_000:.2f}M"
        else:
            tvl_str = f"${s.tvl / 1_000:.0f}K"
        
        print(f"\n{i:2}. {s.protocol_name}")
        print(f"    Score: {s.total_score}/100 | TVL: {tvl_str} | {tokenless}")
        print(f"    Category: {s.category}")
        
        if s.funding_amount > 0:
            print(f"    Funding: ${s.funding_amount:.1f}M")
        
        if s.tier1_vcs:
            print(f"    Tier-1 VCs: {', '.join(s.tier1_vcs[:3])}")
        
        if s.chains:
            print(f"    Chains: {', '.join(s.chains[:5])}")
    
    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Airdrop Discovery System - 有望なエアドロップ候補を発見",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py                    # ダッシュボードを生成してブラウザで開く
  python main.py --console          # コンソールでレポートを表示
  python main.py --test-api         # API接続をテスト
  python main.py --test-scoring     # スコアリングをテスト
  python main.py --no-browser       # ダッシュボード生成のみ（ブラウザを開かない）
  python main.py --clear-cache      # キャッシュをクリア
        """
    )
    
    parser.add_argument("--test-api", action="store_true", 
                        help="API接続をテスト")
    parser.add_argument("--test-scoring", action="store_true",
                        help="スコアリングシステムをテスト")
    parser.add_argument("--generate-dashboard", action="store_true",
                        help="ダッシュボードを生成")
    parser.add_argument("--console", action="store_true",
                        help="コンソールにレポートを表示")
    parser.add_argument("--no-browser", action="store_true",
                        help="ブラウザを自動で開かない")
    parser.add_argument("--clear-cache", action="store_true",
                        help="キャッシュをクリア")
    parser.add_argument("--top", type=int, default=100,
                        help="表示するプロジェクト数 (default: 100)")
    
    args = parser.parse_args()
    
    print_banner()
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Handle cache clearing
    if args.clear_cache:
        client = DeFilLamaClient()
        client.clear_cache()
        print("\n[Cache] キャッシュをクリアしました")
        if not any([args.test_api, args.test_scoring, args.generate_dashboard, args.console]):
            return
    
    # Handle test modes
    if args.test_api:
        success = test_api()
        sys.exit(0 if success else 1)
    
    if args.test_scoring:
        success = test_scoring()
        sys.exit(0 if success else 1)
    
    # Handle console report
    if args.console:
        print_console_report(limit=args.top)
        return
    
    # Default action: generate dashboard
    generate_dashboard(
        open_browser=not args.no_browser,
        top_n=args.top
    )


if __name__ == "__main__":
    main()
