"""
DeFilLama API Client
Handles communication with DeFilLama's public API endpoints.
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class DeFilLamaClient:
    """Client for DeFilLama API interactions."""
    
    BASE_URL = "https://api.llama.fi"
    CACHE_DIR = Path(__file__).parent / "cache"
    CACHE_DURATION_HOURS = 6  # Cache data for 6 hours
    
    def __init__(self):
        """Initialize the client and ensure cache directory exists."""
        self.CACHE_DIR.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "AirdropDiscoveryBot/1.0"
        })
    
    def _get_cache_path(self, endpoint: str) -> Path:
        """Get the cache file path for an endpoint."""
        safe_name = endpoint.replace("/", "_").strip("_") + ".json"
        return self.CACHE_DIR / safe_name
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached data is still valid."""
        if not cache_path.exists():
            return False
        
        modified_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - modified_time < timedelta(hours=self.CACHE_DURATION_HOURS)
    
    def _load_from_cache(self, endpoint: str) -> Optional[Dict]:
        """Load data from cache if valid."""
        cache_path = self._get_cache_path(endpoint)
        
        if self._is_cache_valid(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def _save_to_cache(self, endpoint: str, data: Any) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(endpoint)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _request(self, endpoint: str, use_cache: bool = True, max_retries: int = 3) -> Any:
        """
        Make a request to the API with caching and retry logic.
        
        Args:
            endpoint: API endpoint path
            use_cache: Whether to use cached data
            max_retries: Maximum number of retry attempts
            
        Returns:
            JSON response data
        """
        # Try cache first
        if use_cache:
            cached = self._load_from_cache(endpoint)
            if cached is not None:
                print(f"[Cache] Using cached data for {endpoint}")
                return cached
        
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                print(f"[API] Fetching {url}...")
                response = self.session.get(url, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                
                # Save to cache
                if use_cache:
                    self._save_to_cache(endpoint, data)
                
                return data
                
            except requests.exceptions.RequestException as e:
                print(f"[Error] Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"[Retry] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise
    
    def get_protocols(self, use_cache: bool = True) -> List[Dict]:
        """
        Get all DeFi protocols from DeFilLama.
        
        Returns:
            List of protocol dictionaries with TVL, category, chains, etc.
        """
        return self._request("/protocols", use_cache=use_cache)
    
    def get_raises(self, use_cache: bool = True) -> Dict:
        """
        Get all funding raises data.
        
        Returns:
            Dictionary containing 'raises' list
        """
        return self._request("/raises", use_cache=use_cache)
    
    def get_tokenless_protocols(self, use_cache: bool = True) -> List[Dict]:
        """
        Get protocols that don't have a token yet.
        These are prime candidates for future airdrops.
        
        Returns:
            List of tokenless protocol dictionaries
        """
        protocols = self.get_protocols(use_cache=use_cache)
        
        tokenless = []
        for p in protocols:
            # Check if protocol has no token
            # Symbol is "-" or null, and gecko_id/cmcId are null
            symbol = p.get("symbol", "-")
            gecko_id = p.get("gecko_id")
            cmc_id = p.get("cmcId")
            
            if symbol == "-" and gecko_id is None and cmc_id is None:
                tokenless.append(p)
        
        return tokenless
    
    def get_recent_raises(self, days: int = 180, use_cache: bool = True) -> List[Dict]:
        """
        Get funding raises from the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recent raise dictionaries
        """
        raises_data = self.get_raises(use_cache=use_cache)
        raises = raises_data.get("raises", [])
        
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        recent = []
        for r in raises:
            raise_date = r.get("date", 0)
            if raise_date >= cutoff:
                recent.append(r)
        
        return recent
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        for cache_file in self.CACHE_DIR.glob("*.json"):
            cache_file.unlink()
        print("[Cache] All cache files cleared")


if __name__ == "__main__":
    # Test the client
    client = DeFilLamaClient()
    
    print("\n=== Testing DeFilLama Client ===\n")
    
    # Test protocols endpoint
    protocols = client.get_protocols()
    print(f"Total protocols: {len(protocols)}")
    
    # Test tokenless detection
    tokenless = client.get_tokenless_protocols()
    print(f"Tokenless protocols: {len(tokenless)}")
    
    # Test raises endpoint
    raises = client.get_raises()
    print(f"Total raises: {len(raises.get('raises', []))}")
    
    # Test recent raises
    recent = client.get_recent_raises(days=90)
    print(f"Raises in last 90 days: {len(recent)}")
    
    print("\n=== Tests Complete ===")
