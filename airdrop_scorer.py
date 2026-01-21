"""
Airdrop Scorer (Refined v2.0)
Calculates airdrop potential scores for DeFi protocols based on research-backed criteria.

改善点:
- トークン未発行スコアを30→12に削減
- 高エアドロVC（Binance Labs/Dragonfly/Polychain）の検出とボーナス
- Hidden Gem発見アルゴリズム
- プロジェクトステージ検出（シード/シリーズA）
- 2025年VCリスト更新
"""

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re


# =============================================================================
# VC Classifications (Updated for 2025)
# =============================================================================

# High Airdrop VCs - 15%+ historical airdrop rate (研究データに基づく)
HIGH_AIRDROP_VCS: Set[str] = {
    "binance labs",      # 15.4%
    "dragonfly",         # 16.3%
    "dragonfly capital",
    "polychain capital", # 14%
    "polychain",
}

# Tier-1 VCs - Most reputable investors (2025年版)
TIER1_VCS: Set[str] = {
    # 大手
    "a16z",
    "a16z crypto",
    "andreessen horowitz",
    "paradigm",
    "polychain capital",
    "polychain",
    "sequoia capital",
    "sequoia",
    
    # トップパフォーマー
    "dragonfly",
    "dragonfly capital",
    "pantera capital",
    "pantera",
    "multicoin capital",
    "multicoin",
    "coinbase ventures",
    "binance labs",
    
    # 2024-2025年注目
    "haun ventures",
    "variant",
    "variant fund",
    "framework ventures",
    "electric capital",
    "1kx",
    "delphi ventures",
    "delphi digital",
    "hack vc",           # 新規 2024
    "robot ventures",    # 新規 2024
    "galaxy digital",
    "standard crypto",
    "blockchain capital",
    "lightspeed venture partners",
    "faction",
    "jump crypto",
}

# Tier-2 VCs - Still very reputable (2025年版)
TIER2_VCS: Set[str] = {
    # 取引所VC
    "hashkey capital",
    "okx ventures",
    "kraken ventures",
    "circle ventures",
    
    # エコシステムVC
    "solana ventures",
    "polygon ventures",
    "avalanche foundation",
    "aptos labs",
    "aptos ventures",
    
    # 2024-2025アクティブ
    "placeholder",
    "nascent",
    "maven 11",
    "cms holdings",
    "animoca brands",
    "spartan group",
    "mechanism capital",
    "shima capital",
    "hashed",
    "foresight ventures",
    "amber group",
    "wintermute ventures",
    "gsrv",
    "gsr",
    
    # 2025年新規
    "fabric ventures",
    "ngc ventures",
    "folius ventures",
    "sfermion",
    "north island ventures",
    "token bay capital",
}

# Hot categories for airdrops (2025年版)
HOT_CATEGORIES: Set[str] = {
    # 定番
    "dexs",
    "derivatives",
    "yield",
    "cdp",
    "perpetuals",
    "perps",
    "cross-chain",
    "privacy",
    "yield aggregator",
    "lending",
    
    # 2025年ホット
    "restaking",
    "liquid staking",
    "intent",
    "modular",
    "chain abstraction",
    "prediction market",
    "rwa",              # Real World Assets
    "btcfi",            # Bitcoin DeFi
}


@dataclass
class AirdropScore:
    """Airdrop potential score for a protocol."""
    protocol_name: str
    protocol_slug: str
    total_score: int
    tvl: float
    tvl_change_7d: Optional[float]
    category: str
    chains: List[str]
    is_tokenless: bool
    listed_at: Optional[datetime]
    
    # Score breakdown (新スコアリング)
    tokenless_score: int = 0           # 最大12点
    points_score: int = 0              # 最大15点
    high_airdrop_vc_score: int = 0     # 最大13点
    funding_score: int = 0             # 最大15点
    vc_score: int = 0                  # 最大12点 (Tier-1)
    tier2_vc_score: int = 0            # 最大8点 (Tier-2)
    recency_score: int = 0             # 最大10点
    stage_score: int = 0               # 最大10点
    tvl_growth_score: int = 0          # 最大8点 (ボーナス)
    category_score: int = 0            # 最大5点 (ボーナス)
    tvl_sweetspot_score: int = 0       # 最大7点 (ボーナス)
    hidden_gem_score: int = 0          # 最大10点 (ボーナス)
    
    # Additional info
    funding_amount: float = 0
    funding_rounds: List[Dict] = field(default_factory=list)
    tier1_vcs: List[str] = field(default_factory=list)
    tier2_vcs: List[str] = field(default_factory=list)
    high_airdrop_vcs: List[str] = field(default_factory=list)
    all_investors: List[str] = field(default_factory=list)
    
    # New metrics
    has_points: bool = False
    project_stage: str = "unknown"     # seed, series_a, growth, late
    is_hidden_gem: bool = False
    
    # Links
    url: Optional[str] = None
    twitter: Optional[str] = None


class AirdropScorer:
    """Calculates airdrop potential scores for protocols (v2.0)."""
    
    def __init__(self, protocols: List[Dict], raises: List[Dict]):
        """
        Initialize the scorer with protocol and raise data.
        
        Args:
            protocols: List of protocol data from DeFilLama
            raises: List of funding raise data from DeFilLama
        """
        self.protocols = protocols
        self.raises = raises
        
        # Build lookup tables
        self._build_raise_lookup()
    
    def _build_raise_lookup(self) -> None:
        """Build a lookup table for raises by protocol name."""
        self.raise_lookup: Dict[str, List[Dict]] = {}
        
        for raise_data in self.raises:
            name = raise_data.get("name", "").lower().strip()
            if name:
                if name not in self.raise_lookup:
                    self.raise_lookup[name] = []
                self.raise_lookup[name].append(raise_data)
            
            # Also index by defillamaId if available
            defillama_id = raise_data.get("defillamaId")
            if defillama_id:
                key = f"id:{defillama_id}"
                if key not in self.raise_lookup:
                    self.raise_lookup[key] = []
                self.raise_lookup[key].append(raise_data)
    
    def _normalize_name(self, name: str) -> str:
        """Normalize protocol name for matching."""
        name = name.lower().strip()
        name = re.sub(r'\s+(v\d+|protocol|finance|labs?)$', '', name)
        name = re.sub(r'[^a-z0-9\s]', '', name)
        return name.strip()
    
    def _find_raises_for_protocol(self, protocol: Dict) -> List[Dict]:
        """Find all funding raises for a protocol."""
        matches = []
        
        # Try by name
        name = self._normalize_name(protocol.get("name", ""))
        if name in self.raise_lookup:
            matches.extend(self.raise_lookup[name])
        
        # Try by slug
        slug = protocol.get("slug", "").lower()
        if slug in self.raise_lookup:
            matches.extend(self.raise_lookup[slug])
        
        # Try by DeFilLama ID
        protocol_id = protocol.get("id")
        if protocol_id:
            key = f"id:{protocol_id}"
            if key in self.raise_lookup:
                matches.extend(self.raise_lookup[key])
        
        # Try parent protocol
        parent_slug = protocol.get("parentProtocol", "").replace("parent#", "")
        if parent_slug:
            for raise_data in self.raises:
                raise_defillama_id = raise_data.get("defillamaId", "")
                if isinstance(raise_defillama_id, str) and parent_slug in raise_defillama_id.lower():
                    matches.append(raise_data)
        
        # Deduplicate
        seen = set()
        unique = []
        for r in matches:
            key = (r.get("name"), r.get("date"), r.get("amount"))
            if key not in seen:
                seen.add(key)
                unique.append(r)
        
        return unique
    
    def _extract_investors(self, raises: List[Dict]) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Extract and categorize investors from raises."""
        tier1 = []
        tier2 = []
        high_airdrop = []
        all_investors = []
        
        for raise_data in raises:
            lead = raise_data.get("leadInvestors", []) or []
            other = raise_data.get("otherInvestors", []) or []
            
            for investor in lead + other:
                if not investor:
                    continue
                    
                investor_lower = investor.lower().strip()
                all_investors.append(investor)
                
                # Check high airdrop VCs first (highest priority)
                if any(vc in investor_lower for vc in HIGH_AIRDROP_VCS):
                    if investor not in high_airdrop:
                        high_airdrop.append(investor)
                
                # Then check tier classifications
                if any(vc in investor_lower for vc in TIER1_VCS):
                    if investor not in tier1:
                        tier1.append(investor)
                elif any(vc in investor_lower for vc in TIER2_VCS):
                    if investor not in tier2:
                        tier2.append(investor)
        
        return tier1, tier2, high_airdrop, list(set(all_investors))
    
    def _is_tokenless(self, protocol: Dict) -> bool:
        """Check if a protocol doesn't have a token yet."""
        symbol = protocol.get("symbol", "-")
        gecko_id = protocol.get("gecko_id")
        cmc_id = protocol.get("cmcId")
        
        return symbol == "-" and gecko_id is None and cmc_id is None
    
    def _detect_project_stage(self, raises: List[Dict], total_funding: float) -> str:
        """
        Detect the project stage based on funding rounds.
        
        Returns:
            str: 'seed', 'series_a', 'growth', 'late', or 'unknown'
        """
        if not raises or total_funding == 0:
            return "unknown"
        
        rounds = []
        for r in raises:
            round_name = r.get("round") or ""
            if round_name:
                rounds.append(round_name.lower())
        
        # Check for late stage indicators
        if any("series b" in r or "series c" in r or "series d" in r for r in rounds):
            return "late"
        
        # Check for Series A
        if any("series a" in r for r in rounds):
            return "series_a"
        
        # Check for seed indicators
        if any("seed" in r or "pre-seed" in r or "angel" in r for r in rounds):
            return "seed"
        
        # Infer from funding amount
        if total_funding <= 5:  # $5M or less
            return "seed"
        elif total_funding <= 20:  # $20M or less
            return "series_a"
        elif total_funding <= 50:
            return "growth"
        else:
            return "late"
    
    def _is_hidden_gem(
        self, 
        listed_at: Optional[datetime],
        project_stage: str,
        has_tier1_or_tier2: bool,
        tvl: float,
        is_tokenless: bool
    ) -> bool:
        """
        Check if a project qualifies as a "Hidden Gem".
        
        Criteria:
        1. Recent listing (≤90 days)
        2. Early stage (seed or series_a)
        3. Has VC backing
        4. Small TVL ($100K - $10M)
        5. No token yet
        """
        if not is_tokenless:
            return False
            
        if not listed_at:
            return False
            
        days_since_listing = (datetime.now() - listed_at).days
        if days_since_listing > 90:
            return False
            
        if project_stage not in ("seed", "series_a"):
            return False
            
        if not has_tier1_or_tier2:
            return False
            
        if tvl < 100_000 or tvl > 10_000_000:
            return False
            
        return True
    
    def score_protocol(self, protocol: Dict) -> AirdropScore:
        """
        Calculate the airdrop potential score for a protocol.
        
        新スコアリングシステム (base 100 + bonus 30):
        
        Tier 1 - Core Signals (40点):
        - トークン未発行: +12点
        - ポイント制度: +15点
        - 高エアドロVC: +13点
        
        Tier 2 - Quality (35点):
        - 資金調達額: 最大+15点
        - Tier-1 VC: 最大+12点
        - Tier-2 VC: 最大+8点
        
        Tier 3 - Timing (25点):
        - 新規性: 最大+10点
        - ステージ: 最大+10点
        
        Tier 4 - Bonus (30点):
        - TVL成長: 最大+8点
        - カテゴリ: 最大+5点
        - TVLスイートスポット: +7点
        - Hidden Gem: +10点
        """
        # Basic info
        name = protocol.get("name", "Unknown")
        slug = protocol.get("slug", "")
        tvl = protocol.get("tvl", 0) or 0
        tvl_change_7d = protocol.get("change_7d")
        category = protocol.get("category", "Unknown")
        chains = protocol.get("chains", [])
        listed_at_ts = protocol.get("listedAt")
        listed_at = datetime.fromtimestamp(listed_at_ts) if listed_at_ts else None
        url = protocol.get("url")
        twitter = protocol.get("twitter")
        description = protocol.get("description", "") or ""
        
        # Check for points/loyalty program
        has_points = any(kw in description.lower() for kw in [
            "points", "airdrop program", "loyalty", "rewards program",
            "ポイント", "エアドロップ"
        ])
        
        # Find funding info
        raises = self._find_raises_for_protocol(protocol)
        tier1_vcs, tier2_vcs, high_airdrop_vcs, all_investors = self._extract_investors(raises)
        total_funding = sum(r.get("amount", 0) or 0 for r in raises)
        
        # Check if tokenless
        is_tokenless = self._is_tokenless(protocol)
        
        # Detect project stage
        project_stage = self._detect_project_stage(raises, total_funding)
        
        # Check hidden gem status
        has_tier1_or_tier2 = bool(tier1_vcs or tier2_vcs)
        is_hidden_gem = self._is_hidden_gem(
            listed_at, project_stage, has_tier1_or_tier2, tvl, is_tokenless
        )
        
        # Calculate scores
        scores = {
            "tokenless": 0,
            "points": 0,
            "high_airdrop_vc": 0,
            "funding": 0,
            "vc": 0,
            "tier2_vc": 0,
            "recency": 0,
            "stage": 0,
            "tvl_growth": 0,
            "category": 0,
            "tvl_sweetspot": 0,
            "hidden_gem": 0,
        }
        
        # ===== Tier 1: Core Signals (40 points) =====
        
        # Tokenless (12 points) - Reduced from 30
        if is_tokenless:
            scores["tokenless"] = 12
        
        # Points/Loyalty Program (15 points)
        if has_points:
            scores["points"] = 15
        
        # High Airdrop VC backing (13 points)
        if high_airdrop_vcs:
            scores["high_airdrop_vc"] = 13
        
        # ===== Tier 2: Project Quality (35 points) =====
        
        # Funding score (up to 15 points)
        if total_funding >= 50:
            scores["funding"] = 15
        elif total_funding >= 20:
            scores["funding"] = 12
        elif total_funding >= 10:
            scores["funding"] = 9
        elif total_funding >= 5:
            scores["funding"] = 6
        elif total_funding >= 1:
            scores["funding"] = 3
        
        # Tier-1 VC score (up to 12 points)
        if len(tier1_vcs) >= 3:
            scores["vc"] = 12
        elif len(tier1_vcs) >= 2:
            scores["vc"] = 8
        elif len(tier1_vcs) >= 1:
            scores["vc"] = 5
        
        # Tier-2 VC score (up to 8 points) - only if no Tier-1
        if not tier1_vcs:
            if len(tier2_vcs) >= 3:
                scores["tier2_vc"] = 8
            elif len(tier2_vcs) >= 2:
                scores["tier2_vc"] = 5
            elif len(tier2_vcs) >= 1:
                scores["tier2_vc"] = 3
        
        # ===== Tier 3: Timing & Discovery (25 points) =====
        
        # Recency score (up to 10 points)
        if listed_at:
            days_since_listing = (datetime.now() - listed_at).days
            if days_since_listing <= 30:
                scores["recency"] = 10
            elif days_since_listing <= 90:
                scores["recency"] = 7
            elif days_since_listing <= 180:
                scores["recency"] = 4
            elif days_since_listing <= 365:
                scores["recency"] = 2
        
        # Stage score (up to 10 points)
        if project_stage == "seed":
            scores["stage"] = 10
        elif project_stage == "series_a":
            scores["stage"] = 5
        
        # ===== Tier 4: Bonus Signals (up to 30 points) =====
        
        # TVL growth (up to 8 points)
        if tvl_change_7d is not None:
            if tvl_change_7d >= 50:
                scores["tvl_growth"] = 8
            elif tvl_change_7d >= 20:
                scores["tvl_growth"] = 5
            elif tvl_change_7d >= 10:
                scores["tvl_growth"] = 3
        
        # Category bonus (5 points)
        if category and category.lower() in HOT_CATEGORIES:
            scores["category"] = 5
        
        # TVL Sweet Spot bonus (7 points) - $10M to $100M
        if 10_000_000 <= tvl <= 100_000_000:
            scores["tvl_sweetspot"] = 7
        
        # Hidden Gem bonus (10 points)
        if is_hidden_gem:
            scores["hidden_gem"] = 10
        
        total_score = sum(scores.values())
        
        return AirdropScore(
            protocol_name=name,
            protocol_slug=slug,
            total_score=total_score,
            tvl=tvl,
            tvl_change_7d=tvl_change_7d,
            category=category,
            chains=chains,
            is_tokenless=is_tokenless,
            listed_at=listed_at,
            tokenless_score=scores["tokenless"],
            points_score=scores["points"],
            high_airdrop_vc_score=scores["high_airdrop_vc"],
            funding_score=scores["funding"],
            vc_score=scores["vc"],
            tier2_vc_score=scores["tier2_vc"],
            recency_score=scores["recency"],
            stage_score=scores["stage"],
            tvl_growth_score=scores["tvl_growth"],
            category_score=scores["category"],
            tvl_sweetspot_score=scores["tvl_sweetspot"],
            hidden_gem_score=scores["hidden_gem"],
            funding_amount=total_funding,
            funding_rounds=raises,
            tier1_vcs=tier1_vcs,
            tier2_vcs=tier2_vcs,
            high_airdrop_vcs=high_airdrop_vcs,
            all_investors=all_investors,
            has_points=has_points,
            project_stage=project_stage,
            is_hidden_gem=is_hidden_gem,
            url=url,
            twitter=twitter,
        )
    
    def score_all_protocols(self, min_tvl: float = 100_000) -> List[AirdropScore]:
        """
        Score all protocols and return sorted by score.
        
        Args:
            min_tvl: Minimum TVL to consider
            
        Returns:
            List of AirdropScore objects sorted by total_score descending
        """
        scores = []
        
        for protocol in self.protocols:
            tvl = protocol.get("tvl", 0) or 0
            
            # Skip tiny protocols
            if tvl < min_tvl:
                continue
            
            # Skip centralized exchanges
            category = protocol.get("category", "")
            if category and "cex" in category.lower():
                continue
            
            score = self.score_protocol(protocol)
            scores.append(score)
        
        # Sort by total score descending, then by TVL
        scores.sort(key=lambda x: (x.total_score, x.tvl), reverse=True)
        
        return scores
    
    def get_top_tokenless(self, limit: int = 50, min_tvl: float = 100_000) -> List[AirdropScore]:
        """Get top tokenless protocols by score."""
        all_scores = self.score_all_protocols(min_tvl=min_tvl)
        tokenless = [s for s in all_scores if s.is_tokenless]
        return tokenless[:limit]
    
    def get_vc_backed_projects(self, limit: int = 50, min_tvl: float = 100_000) -> List[AirdropScore]:
        """Get top VC-backed projects (with Tier-1 or Tier-2 VCs)."""
        all_scores = self.score_all_protocols(min_tvl=min_tvl)
        vc_backed = [s for s in all_scores if s.tier1_vcs or s.tier2_vcs]
        return vc_backed[:limit]
    
    def get_hidden_gems(self, limit: int = 20, min_tvl: float = 100_000) -> List[AirdropScore]:
        """Get hidden gem projects (new, early-stage, VC-backed, low TVL)."""
        all_scores = self.score_all_protocols(min_tvl=min_tvl)
        hidden_gems = [s for s in all_scores if s.is_hidden_gem]
        return hidden_gems[:limit]
    
    def get_high_airdrop_vc_projects(self, limit: int = 30, min_tvl: float = 100_000) -> List[AirdropScore]:
        """Get projects backed by high-airdrop VCs (Binance Labs, Dragonfly, Polychain)."""
        all_scores = self.score_all_protocols(min_tvl=min_tvl)
        high_airdrop = [s for s in all_scores if s.high_airdrop_vcs]
        return high_airdrop[:limit]


if __name__ == "__main__":
    # Test the scorer
    from defillama_client import DeFilLamaClient
    
    client = DeFilLamaClient()
    protocols = client.get_protocols()
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    scorer = AirdropScorer(protocols, raises)
    
    print("\n=== Top 10 Airdrop Candidates (v2.0) ===\n")
    
    top_scores = scorer.score_all_protocols()[:10]
    
    for i, score in enumerate(top_scores, 1):
        gem_mark = "💎" if score.is_hidden_gem else ""
        tokenless_mark = "🟢" if score.is_tokenless else "⚪"
        points_mark = "🎁" if score.has_points else ""
        
        print(f"{i}. {tokenless_mark} {gem_mark} {score.protocol_name} {points_mark}")
        print(f"   Score: {score.total_score}/130 | Stage: {score.project_stage}")
        print(f"   TVL: ${score.tvl:,.0f}")
        print(f"   Category: {score.category}")
        if score.funding_amount > 0:
            print(f"   Funding: ${score.funding_amount}M")
        if score.high_airdrop_vcs:
            print(f"   🔥 High Airdrop VCs: {', '.join(score.high_airdrop_vcs[:3])}")
        if score.tier1_vcs:
            print(f"   Tier-1 VCs: {', '.join(score.tier1_vcs[:3])}")
        print()
    
    # Show hidden gems
    print("\n=== Hidden Gems ===\n")
    hidden_gems = scorer.get_hidden_gems(limit=5)
    for i, gem in enumerate(hidden_gems, 1):
        print(f"{i}. 💎 {gem.protocol_name} (Score: {gem.total_score})")
        print(f"   TVL: ${gem.tvl:,.0f} | Stage: {gem.project_stage}")
        if gem.tier1_vcs or gem.tier2_vcs:
            vcs = gem.tier1_vcs[:2] + gem.tier2_vcs[:2]
            print(f"   VCs: {', '.join(vcs)}")
        print()
