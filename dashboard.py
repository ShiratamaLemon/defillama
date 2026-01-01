"""
Dashboard Generator
Creates an HTML dashboard for visualizing airdrop candidates.
"""

from pathlib import Path
from typing import List
from datetime import datetime
from airdrop_scorer import AirdropScore


class DashboardGenerator:
    """Generates HTML dashboard for airdrop candidates."""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize the dashboard generator.
        
        Args:
            output_dir: Directory to save the dashboard HTML
        """
        if output_dir is None:
            output_dir = Path(__file__).parent / "output"
        
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def _format_tvl(self, tvl: float) -> str:
        """Format TVL for display."""
        if tvl >= 1_000_000_000:
            return f"${tvl / 1_000_000_000:.2f}B"
        elif tvl >= 1_000_000:
            return f"${tvl / 1_000_000:.2f}M"
        elif tvl >= 1_000:
            return f"${tvl / 1_000:.2f}K"
        else:
            return f"${tvl:.0f}"
    
    def _format_change(self, change: float) -> str:
        """Format percentage change with color indicator."""
        if change is None:
            return '<span class="neutral">N/A</span>'
        
        if change >= 0:
            return f'<span class="positive">+{change:.1f}%</span>'
        else:
            return f'<span class="negative">{change:.1f}%</span>'
    
    def _get_score_class(self, score: int) -> str:
        """Get CSS class based on score."""
        if score >= 70:
            return "score-high"
        elif score >= 50:
            return "score-medium"
        else:
            return "score-low"
    
    def generate_html(self, scores: List[AirdropScore], title: str = "Airdrop Discovery Dashboard") -> str:
        """
        Generate the HTML dashboard.
        
        Args:
            scores: List of AirdropScore objects
            title: Dashboard title
            
        Returns:
            HTML content string
        """
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Dark Mode (Default) */
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a24;
            --border-color: #2a2a3c;
            --text-primary: #f0f0f5;
            --text-secondary: #9898a8;
            --accent-purple: #8b5cf6;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --header-gradient-start: #12121a;
            --header-gradient-end: #1a1a24;
        }}
        
        /* Light Mode */
        [data-theme="light"] {{
            --bg-primary: #f8f9fc;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f1f3f8;
            --border-color: #e2e5eb;
            --text-primary: #1a1a2e;
            --text-secondary: #6b7280;
            --accent-purple: #7c3aed;
            --accent-blue: #2563eb;
            --accent-green: #059669;
            --accent-red: #dc2626;
            --accent-yellow: #d97706;
            --header-gradient-start: #ffffff;
            --header-gradient-end: #f1f3f8;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            transition: background 0.3s, color 0.3s;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--header-gradient-start) 0%, var(--header-gradient-end) 100%);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            position: relative;
        }}
        
        .theme-toggle {{
            position: absolute;
            top: 1.5rem;
            right: 1.5rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            color: var(--text-primary);
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s;
        }}
        
        .theme-toggle:hover {{
            background: var(--accent-purple);
            border-color: var(--accent-purple);
            color: white;
        }}
        
        .theme-toggle .icon {{
            font-size: 1.2rem;
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, var(--accent-purple), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: background 0.3s, border-color 0.3s;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-purple);
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        
        .filters {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
        }}
        
        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent-purple);
            border-color: var(--accent-purple);
            color: white;
        }}
        
        .search-box {{
            flex: 1;
            min-width: 200px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            transition: background 0.3s, border-color 0.3s;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: var(--accent-purple);
        }}
        
        .table-container {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            transition: background 0.3s, border-color 0.3s;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: var(--bg-tertiary);
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
        }}
        
        td {{
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            vertical-align: middle;
            height: 60px;
        }}
        
        tr:hover {{
            background: var(--bg-tertiary);
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        .rank {{
            font-weight: 700;
            color: var(--text-secondary);
            width: 50px;
        }}
        
        .protocol-cell {{
            vertical-align: middle;
        }}
        
        .protocol-content {{
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
        }}
        
        .protocol-content a {{
            color: var(--text-primary);
            text-decoration: none;
        }}
        
        .protocol-content a:hover {{
            color: var(--accent-purple);
        }}
        
        .token-badge {{
            font-size: 0.7rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: 500;
            white-space: nowrap;
        }}
        
        .badge-tokenless {{
            background: var(--accent-green);
            color: #000;
        }}
        
        .badge-token {{
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }}
        
        .score-badge {{
            font-weight: 700;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            display: inline-block;
            min-width: 60px;
            text-align: center;
        }}
        
        .score-high {{
            background: linear-gradient(135deg, var(--accent-green), #059669);
            color: #000;
        }}
        
        .score-medium {{
            background: linear-gradient(135deg, var(--accent-yellow), #d97706);
            color: #000;
        }}
        
        .score-low {{
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }}
        
        /* New Styles for Phase 2 */
        .points-badge {{
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #000;
            font-size: 0.65rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-weight: 700;
            margin-left: 0.5rem;
            white-space: nowrap;
        }}
        
        .score-high {{
            background: linear-gradient(135deg, var(--accent-green), #059669);
            color: #000;
        }}
        
        .score-medium {{
            background: linear-gradient(135deg, var(--accent-yellow), #d97706);
            color: #000;
        }}
        
        .score-low {{
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }}
        
        .tvl {{
            font-weight: 600;
            font-family: 'SF Mono', 'Monaco', monospace;
        }}
        
        .positive {{
            color: var(--accent-green);
        }}
        
        .negative {{
            color: var(--accent-red);
        }}
        
        .neutral {{
            color: var(--text-secondary);
        }}
        
        .category-badge {{
            background: var(--bg-tertiary);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        
        .vc-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            align-items: center;
        }}
        
        .vc-badge {{
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 500;
        }}
        
        .vc-badge.tier2 {{
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }}
        
        [data-theme="light"] .vc-badge.tier2 {{
            background: #e5e7eb;
            color: #4b5563;
        }}
        
        .chains {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
        }}
        
        .chain-badge {{
            background: var(--bg-tertiary);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            color: var(--text-secondary);
        }}
        
        .links {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }}
        
        .link-btn {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
            text-decoration: none;
            padding: 0.4rem 0.75rem;
            border-radius: 6px;
            font-size: 0.8rem;
            transition: all 0.2s;
        }}
        
        .link-btn:hover {{
            background: var(--accent-purple);
            color: white;
        }}
        
        .score-breakdown {{
            display: none;
            background: var(--bg-tertiary);
            padding: 1rem;
            margin-top: 0.5rem;
            border-radius: 8px;
            font-size: 0.85rem;
        }}
        
        .score-breakdown.active {{
            display: block;
        }}
        
        .breakdown-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.25rem 0;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .breakdown-item:last-child {{
            border-bottom: none;
        }}
        
        footer {{
            text-align: center;
            margin-top: 2rem;
            padding: 1rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        footer a {{
            color: var(--accent-purple);
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            h1 {{
                font-size: 1.75rem;
            }}
            
            .theme-toggle {{
                position: static;
                margin: 1rem auto 0;
            }}
            
            .table-container {{
                overflow-x: auto;
            }}
            
            table {{
                min-width: 800px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <button class="theme-toggle" onclick="toggleTheme()">
                <span class="icon" id="theme-icon">🌙</span>
                <span id="theme-text">Dark</span>
            </button>
            <h1>🪂 Airdrop Discovery Dashboard</h1>
            <p class="subtitle">DeFilLama データに基づく有望プロジェクト分析 | 最終更新: {generated_at}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(scores)}</div>
                <div class="stat-label">分析対象プロジェクト</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([s for s in scores if s.is_tokenless])}</div>
                <div class="stat-label">トークン未発行</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([s for s in scores if s.tier1_vcs])}</div>
                <div class="stat-label">Tier-1 VC支援</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([s for s in scores if s.total_score >= 50])}</div>
                <div class="stat-label">高スコア (50+)</div>
            </div>
        </div>
        
        <div class="filters">
            <button class="filter-btn active" onclick="filterTable('all')">すべて</button>
            <button class="filter-btn" onclick="filterTable('tokenless')">トークン未発行のみ</button>
            <button class="filter-btn" onclick="filterTable('points')">Pointsあり</button>
            <button class="filter-btn" onclick="filterTable('vc')">Tier-1 VC支援</button>
            <button class="filter-btn" onclick="filterTable('high-score')">高スコア (50+)</button>
            <input type="text" class="search-box" placeholder="🔍 プロジェクト名で検索..." oninput="searchTable(this.value)">
        </div>
        
        <div class="table-container">
            <table id="projects-table">
                <thead>
                    <tr>
                        <th>順位</th>
                        <th>プロジェクト</th>
                        <th>スコア</th>
                        <th>TVL</th>
                        <th>7日変動</th>
                        <th>カテゴリ</th>
                        <th>調達額</th>
                        <th>主要VC</th>
                        <th>リンク</th>
                    </tr>
                </thead>
                <tbody>
'''
        
        for i, score in enumerate(scores, 1):
            tokenless_badge = '<span class="token-badge badge-tokenless">No Token</span>' if score.is_tokenless else ''
            
            vc_html = ""
            for vc in score.tier1_vcs[:3]:
                vc_html += f'<span class="vc-badge">{vc}</span>'
            for vc in score.tier2_vcs[:2]:
                vc_html += f'<span class="vc-badge tier2">{vc}</span>'
            
            chains_html = ""
            for chain in score.chains[:4]:
                chains_html += f'<span class="chain-badge">{chain}</span>'
            if len(score.chains) > 4:
                chains_html += f'<span class="chain-badge">+{len(score.chains) - 4}</span>'
            
            links_html = ""
            if score.url:
                links_html += f'<a href="{score.url}" target="_blank" class="link-btn">Web</a>'
            if score.twitter:
                links_html += f'<a href="https://twitter.com/{score.twitter}" target="_blank" class="link-btn">𝕏</a>'
            links_html += f'<a href="https://defillama.com/protocol/{score.protocol_slug}" target="_blank" class="link-btn">DeFi</a>'
            
            funding_display = f"${score.funding_amount:.1f}M" if score.funding_amount > 0 else "-"
            
            html += f'''
                    <tr data-tokenless="{str(score.is_tokenless).lower()}" 
                        data-vc="{str(bool(score.tier1_vcs)).lower()}"
                        data-points="{str(score.has_points).lower()}"
                        data-score="{score.total_score}"
                        data-name="{score.protocol_name.lower()}">
                        <td class="rank">{i}</td>
                        <td>
                            <span class="protocol-content">
                                <a href="https://defillama.com/protocol/{score.protocol_slug}" target="_blank">
                                    {score.protocol_name}
                                </a>
                                {tokenless_badge}
                                {'<span class="points-badge">Points</span>' if score.has_points else ''}
                            </span>
                        </td>
                        <td>
                            <span class="score-badge {self._get_score_class(score.total_score)}">
                                {score.total_score}
                            </span>
                        </td>
                        <td class="tvl">{self._format_tvl(score.tvl)}</td>
                        <td>{self._format_change(score.tvl_change_7d)}</td>
                        <td><span class="category-badge">{score.category}</span></td>
                        <td>{funding_display}</td>
                        <td><div class="vc-list">{vc_html if vc_html else "-"}</div></td>
                        <td><div class="links">{links_html}</div></td>
                    </tr>
'''
        
        html += '''
                </tbody>
            </table>
        </div>
        
        <footer>
            <p>データソース: <a href="https://defillama.com" target="_blank" style="color: var(--accent-purple);">DeFilLama</a> | 
               Airdrop Discovery System v1.0</p>
        </footer>
    </div>
    
    <script>
        // Theme toggle functionality
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeUI(newTheme);
        }
        
        function updateThemeUI(theme) {
            const icon = document.getElementById('theme-icon');
            const text = document.getElementById('theme-text');
            
            if (theme === 'light') {
                icon.textContent = '☀️';
                text.textContent = 'Light';
            } else {
                icon.textContent = '🌙';
                text.textContent = 'Dark';
            }
        }
        
        // Initialize theme from localStorage
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            if (savedTheme === 'light') {
                document.documentElement.setAttribute('data-theme', 'light');
            }
            // Update UI after DOM is ready
            document.addEventListener('DOMContentLoaded', function() {
                updateThemeUI(savedTheme);
            });
        })();
        
        function filterTable(filter) {
            const rows = document.querySelectorAll('#projects-table tbody tr');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            rows.forEach(row => {
                let show = true;
                
                switch(filter) {
                    case 'tokenless':
                        show = row.dataset.tokenless === 'true';
                        break;
                    case 'points':
                        show = row.dataset.points === 'true';
                        break;
                    case 'vc':
                        show = row.dataset.vc === 'true';
                        break;
                    case 'high-score':
                        show = parseInt(row.dataset.score) >= 50;
                        break;
                    default:
                        show = true;
                }
                
                row.style.display = show ? '' : 'none';
            });
            
            updateRanks();
        }
        
        function searchTable(query) {
            const rows = document.querySelectorAll('#projects-table tbody tr');
            const lowerQuery = query.toLowerCase();
            
            rows.forEach(row => {
                const name = row.dataset.name;
                row.style.display = name.includes(lowerQuery) ? '' : 'none';
            });
            
            updateRanks();
        }
        
        function updateRanks() {
            const rows = document.querySelectorAll('#projects-table tbody tr');
            let visibleRank = 1;
            
            rows.forEach(row => {
                if (row.style.display !== 'none') {
                    row.querySelector('.rank').textContent = visibleRank++;
                }
            });
        }
    </script>
</body>
</html>'''
        
        return html
    
    def save_dashboard(self, scores: List[AirdropScore], filename: str = "index.html") -> Path:
        """
        Generate and save the dashboard HTML.
        
        Args:
            scores: List of AirdropScore objects
            filename: Output filename
            
        Returns:
            Path to the saved file
        """
        html = self.generate_html(scores)
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"[Dashboard] Saved to {output_path}")
        return output_path


if __name__ == "__main__":
    # Test the dashboard generator
    from defillama_client import DeFilLamaClient
    from airdrop_scorer import AirdropScorer
    
    client = DeFilLamaClient()
    protocols = client.get_protocols()
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    scorer = AirdropScorer(protocols, raises)
    scores = scorer.score_all_protocols()[:100]
    
    generator = DashboardGenerator()
    path = generator.save_dashboard(scores)
    
    print(f"\nDashboard generated: {path}")
