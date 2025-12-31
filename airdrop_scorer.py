"""
Airdrop Scorer
Calculates airdrop potential scores for DeFi protocols based on various criteria.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re


# Tier-1 VCs - These are the most reputable investors in crypto
TIER1_VCS: Set[str] = {
    "a16z",
    "a16z crypto",
    "andreessen horowitz",
    "paradigm",
    "polychain capital",
    "polychain",
    "multicoin capital",
    "multicoin",
    "pantera capital",
    "pantera",
    "dragonfly capital",
    "dragonfly",
    "sequoia capital",
    "sequoia",
    "coinbase ventures",
    "binance labs",
    "framework ventures",
    "electric capital",
    "variant",
    "variant fund",
    "haun ventures",
    "jump crypto",
    "paradigm shift",
    "galaxy digital",
    "delphi ventures",
    "delphi digital",
    "1kx",
    "standard crypto",
    "blockchain capital",
    "lightspeed venture partners",
}

# Tier-2 VCs - Still very reputable
TIER2_VCS: Set[str] = {
    "hashkey capital",
    "okx ventures",
    "kraken ventures",
    "circle ventures",
    "solana ventures",
    "polygon ventures",
    "robot ventures",
    "placeholder",
    "nascent",
    "maven 11",
    "cms holdings",
    "animoca brands",
    "spartan group",
    "mechanism capital",
    "hack vc",
    "shima capital",
    "hashed",
    "foresight ventures",
    "amber group",
    "gsrv",
    "gsr",
    "wintermute ventures",
    "alameda research",  # Historical significance
}

# Hot categories for airdrops
HOT_CATEGORIES: Set[str] = {
    "dexs",
    "derivatives",
    "yield",
    "cdp",
    "perpetuals",
    "perps",
    "cross-chain",
    "privacy",
    "yield aggregator",
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
    
    # Score breakdown
    tokenless_score: int = 0
    funding_score: int = 0
    vc_score: int = 0
    tvl_growth_score: int = 0
    recency_score: int = 0
    category_score: int = 0
    tvl_size_score: int = 0
    
    # Additional info
    funding_amount: float = 0
    funding_rounds: List[Dict] = field(default_factory=list)
    tier1_vcs: List[str] = field(default_factory=list)
    tier2_vcs: List[str] = field(default_factory=list)
    all_investors: List[str] = field(default_factory=list)
    
    # Links
    url: Optional[str] = None
    twitter: Optional[str] = None


class AirdropScorer:
    """Calculates airdrop potential scores for protocols."""
    
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
        # Remove common suffixes and clean up
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
    
    def _extract_investors(self, raises: List[Dict]) -> tuple:
        """Extract and categorize investors from raises."""
        tier1 = []
        tier2 = []
        all_investors = []
        
        for raise_data in raises:
            lead = raise_data.get("leadInvestors", []) or []
            other = raise_data.get("otherInvestors", []) or []
            
            for investor in lead + other:
                if not investor:
                    continue
                    
                investor_lower = investor.lower().strip()
                all_investors.append(investor)
                
                if any(vc in investor_lower for vc in TIER1_VCS):
                    if investor not in tier1:
                        tier1.append(investor)
                elif any(vc in investor_lower for vc in TIER2_VCS):
                    if investor not in tier2:
                        tier2.append(investor)
        
        return tier1, tier2, list(set(all_investors))
    
    def _is_tokenless(self, protocol: Dict) -> bool:
        """Check if a protocol doesn't have a token yet."""
        symbol = protocol.get("symbol", "-")
        gecko_id = protocol.get("gecko_id")
        cmc_id = protocol.get("cmcId")
        
        return symbol == "-" and gecko_id is None and cmc_id is None
    
    def score_protocol(self, protocol: Dict) -> AirdropScore:
        """
        Calculate the airdrop potential score for a protocol.
        
        Scoring criteria (100 points max):
        - No token yet: +30 points
        - High funding amount: up to +25 points
        - Tier-1 VC backing: up to +20 points
        - TVL growth: up to +15 points
        - Recent listing: up to +10 points
        - Hot category: up to +5 points (bonus)
        - Large TVL: up to +5 points (bonus)
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
        
        # Find funding info
        raises = self._find_raises_for_protocol(protocol)
        tier1_vcs, tier2_vcs, all_investors = self._extract_investors(raises)
        total_funding = sum(r.get("amount", 0) or 0 for r in raises)
        
        # Check if tokenless
        is_tokenless = self._is_tokenless(protocol)
        
        # Calculate scores
        scores = {
            "tokenless": 0,
            "funding": 0,
            "vc": 0,
            "tvl_growth": 0,
            "recency": 0,
            "category": 0,
            "tvl_size": 0,
        }
        
        # Tokenless bonus (30 points)
        if is_tokenless:
            scores["tokenless"] = 30
        
        # Funding score (up to 25 points)
        if total_funding >= 100:
            scores["funding"] = 25
        elif total_funding >= 50:
            scores["funding"] = 22
        elif total_funding >= 20:
            scores["funding"] = 18
        elif total_funding >= 10:
            scores["funding"] = 15
        elif total_funding >= 5:
            scores["funding"] = 10
        elif total_funding > 0:
            scores["funding"] = 5
        
        # VC score (up to 20 points)
        if len(tier1_vcs) >= 3:
            scores["vc"] = 20
        elif len(tier1_vcs) >= 2:
            scores["vc"] = 16
        elif len(tier1_vcs) >= 1:
            scores["vc"] = 12
        elif len(tier2_vcs) >= 2:
            scores["vc"] = 8
        elif len(tier2_vcs) >= 1:
            scores["vc"] = 4
        
        # TVL growth score (up to 15 points)
        if tvl_change_7d is not None:
            if tvl_change_7d >= 50:
                scores["tvl_growth"] = 15
            elif tvl_change_7d >= 20:
                scores["tvl_growth"] = 12
            elif tvl_change_7d >= 10:
                scores["tvl_growth"] = 9
            elif tvl_change_7d >= 5:
                scores["tvl_growth"] = 6
            elif tvl_change_7d >= 0:
                scores["tvl_growth"] = 3
        
        # Recency score (up to 10 points)
        if listed_at:
            days_since_listing = (datetime.now() - listed_at).days
            if days_since_listing <= 30:
                scores["recency"] = 10
            elif days_since_listing <= 90:
                scores["recency"] = 8
            elif days_since_listing <= 180:
                scores["recency"] = 6
            elif days_since_listing <= 365:
                scores["recency"] = 4
        
        # Category bonus (up to 5 points)
        if category and category.lower() in HOT_CATEGORIES:
            scores["category"] = 5
        
        # TVL size bonus (up to 5 points)
        if tvl >= 1_000_000_000:  # $1B+
            scores["tvl_size"] = 5
        elif tvl >= 100_000_000:  # $100M+
            scores["tvl_size"] = 4
        elif tvl >= 10_000_000:  # $10M+
            scores["tvl_size"] = 3
        elif tvl >= 1_000_000:  # $1M+
            scores["tvl_size"] = 2
        
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
            funding_score=scores["funding"],
            vc_score=scores["vc"],
            tvl_growth_score=scores["tvl_growth"],
            recency_score=scores["recency"],
            category_score=scores["category"],
            tvl_size_score=scores["tvl_size"],
            funding_amount=total_funding,
            funding_rounds=raises,
            tier1_vcs=tier1_vcs,
            tier2_vcs=tier2_vcs,
            all_investors=all_investors,
            url=url,
            twitter=twitter,
        )
    
    def score_all_protocols(self, min_tvl: float = 100_000) -> List[AirdropScore]:
        """
        Score all protocols and return sorted by score.
        
        Args:
            min_tvl: Minimum TVL to consider (filter out tiny protocols)
            
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
        """
        Get top tokenless protocols by score.
        
        Args:
            limit: Maximum number of results
            min_tvl: Minimum TVL threshold
            
        Returns:
            Top tokenless protocols sorted by score
        """
        all_scores = self.score_all_protocols(min_tvl=min_tvl)
        tokenless = [s for s in all_scores if s.is_tokenless]
        return tokenless[:limit]
    
    def get_vc_backed_projects(self, limit: int = 50, min_tvl: float = 100_000) -> List[AirdropScore]:
        """
        Get top VC-backed projects (with Tier-1 or Tier-2 VCs).
        
        Args:
            limit: Maximum number of results
            min_tvl: Minimum TVL threshold
            
        Returns:
            Top VC-backed protocols sorted by score
        """
        all_scores = self.score_all_protocols(min_tvl=min_tvl)
        vc_backed = [s for s in all_scores if s.tier1_vcs or s.tier2_vcs]
        return vc_backed[:limit]


if __name__ == "__main__":
    # Test the scorer
    from defillama_client import DeFilLamaClient
    
    client = DeFilLamaClient()
    protocols = client.get_protocols()
    raises_data = client.get_raises()
    raises = raises_data.get("raises", [])
    
    scorer = AirdropScorer(protocols, raises)
    
    print("\n=== Top 10 Airdrop Candidates ===\n")
    
    top_scores = scorer.score_all_protocols()[:10]
    
    for i, score in enumerate(top_scores, 1):
        print(f"{i}. {score.protocol_name}")
        print(f"   Score: {score.total_score}/100")
        print(f"   TVL: ${score.tvl:,.0f}")
        print(f"   Tokenless: {'Yes' if score.is_tokenless else 'No'}")
        print(f"   Category: {score.category}")
        print(f"   Funding: ${score.funding_amount}M")
        if score.tier1_vcs:
            print(f"   Tier-1 VCs: {', '.join(score.tier1_vcs[:3])}")
        print()
