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
║   DeFilLama Data-Driven Airdrop Discovery Tool                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def test_api():
    """Test API connectivity."""
    print("\n[Test] Testing API connection...")
    client = DeFilLamaClient()
    
    try:
        protocols = client.get_protocols(use_cache=False)
        print(f"  ✓ Protocols Endpoint: {len(protocols)} items fetched")
        
        raises = client.get_raises(use_cache=False)
        print(f"  ✓ Raises Endpoint: {len(raises.get('raises', []))} items fetched")
        
        print("\n[Test] API Connection Test Passed ✓")
        return True
    except Exception as e:
        print(f"\n[Error] API Connection Error: {e}")
        return False


def test_scoring():
    """Test the scoring system."""
    print("\n[Test] Testing Scoring System...")
    client = DeFilLamaClient()
    
    protocols = client.get_protocols()
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    scorer = AirdropScorer(protocols, raises)
    
    # Score all protocols
    scores = scorer.score_all_protocols()
    
    print(f"\n  Analyzed Protocols: {len(scores)} items")
    print(f"  Tokenless: {len([s for s in scores if s.is_tokenless])} items")
    print(f"  Tier-1 VC Backed: {len([s for s in scores if s.tier1_vcs])} items")
    print(f"  High Score (50+): {len([s for s in scores if s.total_score >= 50])} items")
    
    print("\n  Top 5 Projects:")
    for i, s in enumerate(scores[:5], 1):
        tokenless_mark = "🟢" if s.is_tokenless else "⚪"
        print(f"    {i}. {tokenless_mark} {s.protocol_name} (Score: {s.total_score})")
    
    print("\n[Test] Scoring Test Passed ✓")
    return True


def generate_dashboard(open_browser: bool = True, top_n: int = 100):
    """Generate the HTML dashboard."""
    print("\n[Dashboard] Generating Dashboard...")
    
    client = DeFilLamaClient()
    
    print("  - Fetching Protocol Data...")
    protocols = client.get_protocols()
    
    print("  - Fetching Funding Data...")
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    print("  - Executing Scoring...")
    scorer = AirdropScorer(protocols, raises)
    scores = scorer.score_all_protocols()[:top_n]
    
    print("  - Generating HTML...")
    generator = DashboardGenerator()
    output_path = generator.save_dashboard(scores)
    
    print(f"\n[Dashboard] Generation Complete: {output_path}")
    
    if open_browser:
        print("[Dashboard] Opening in browser...")
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
        description="Airdrop Discovery System - Find Promising Airdrop Candidates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage:
  python main.py                    # Generate dashboard and open in browser
  python main.py --console          # Show report in console
  python main.py --test-api         # Test API connectivity
  python main.py --test-scoring     # Test scoring system
  python main.py --no-browser       # Generate dashboard only (do not open browser)
  python main.py --clear-cache      # Clear cache
        """
    )
    
    parser.add_argument("--test-api", action="store_true", 
                        help="Test API connectivity")
    parser.add_argument("--test-scoring", action="store_true",
                        help="Test scoring system")
    parser.add_argument("--generate-dashboard", action="store_true",
                        help="Generate dashboard")
    parser.add_argument("--console", action="store_true",
                        help="Show report in console")
    parser.add_argument("--no-browser", action="store_true",
                        help="Do not automatically open browser")
    parser.add_argument("--clear-cache", action="store_true",
                        help="Clear cache")
    parser.add_argument("--top", type=int, default=100,
                        help="Number of projects to display (default: 100)")
    
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
