#!/usr/bin/env python3
"""
Feed Discovery Module for awesome-rss-feeds integration
Parses OPML files and provides searchable feed database
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class FeedDiscovery:
    def __init__(self, awesome_feeds_path: str = "awesome-rss-feeds"):
        self.awesome_feeds_path = Path(awesome_feeds_path)
        self.feeds_cache = {}
        self.repo_available = False
        self._load_all_feeds()
    
    def _load_all_feeds(self):
        """Load and parse all OPML files"""
        if not self.awesome_feeds_path.exists():
            logger.warning(f"awesome-rss-feeds directory not found at {self.awesome_feeds_path}")
            logger.info("Run setup script to automatically clone the feed discovery database")
            self.repo_available = False
            return
        
        self.repo_available = True
        
        # Load recommended feeds by category
        recommended_path = self.awesome_feeds_path / "recommended" / "with_category"
        if recommended_path.exists():
            for opml_file in recommended_path.glob("*.opml"):
                category = opml_file.stem
                feeds = self._parse_opml_file(opml_file)
                if feeds:
                    self.feeds_cache[f"recommended_{category}"] = {
                        "type": "recommended",
                        "category": category,
                        "display_name": f"Recommended: {category}",
                        "feeds": feeds
                    }
        
        # Load country-based feeds
        countries_path = self.awesome_feeds_path / "countries" / "with_category"
        if countries_path.exists():
            for opml_file in countries_path.glob("*.opml"):
                country = opml_file.stem
                feeds = self._parse_opml_file(opml_file)
                if feeds:
                    self.feeds_cache[f"country_{country}"] = {
                        "type": "country",
                        "category": country,
                        "display_name": f"Country: {country}",
                        "feeds": feeds
                    }
        
        logger.info(f"Loaded {len(self.feeds_cache)} feed collections")
    
    def _parse_opml_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse an OPML file and extract feed information"""
        try:
            # Read and preprocess the file to handle unescaped characters
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to fix common XML issues in descriptions
            import html
            import re
            
            # Find description attributes and escape their content
            def escape_description(match):
                desc = match.group(1)
                # Unescape any existing HTML entities first, then re-escape properly
                desc = html.unescape(desc)
                desc = html.escape(desc, quote=True)
                return f'description="{desc}"'
            
            # Fix unescaped ampersands and quotes in description attributes
            content = re.sub(r'description="([^"]*)"', escape_description, content)
            
            # Parse the cleaned content
            root = ET.fromstring(content)
            
            feeds = []
            
            # Find all outline elements with xmlUrl (RSS feeds)
            for outline in root.findall(".//outline[@xmlUrl]"):
                feed_info = {
                    "title": outline.get("title", "").strip(),
                    "text": outline.get("text", "").strip(),
                    "description": outline.get("description", "").strip(),
                    "url": outline.get("xmlUrl", "").strip(),
                    "type": outline.get("type", "rss").strip()
                }
                
                # Use title if text is empty, or vice versa
                if not feed_info["title"] and feed_info["text"]:
                    feed_info["title"] = feed_info["text"]
                elif not feed_info["text"] and feed_info["title"]:
                    feed_info["text"] = feed_info["title"]
                
                if feed_info["url"] and feed_info["title"]:
                    feeds.append(feed_info)
            
            return feeds
            
        except ET.ParseError as e:
            logger.warning(f"XML parsing error in {file_path}: {e}")
            # Try alternative parsing method for problematic files
            return self._parse_opml_fallback(file_path)
        except Exception as e:
            logger.error(f"Unexpected error parsing {file_path}: {e}")
            return []
    
    def _parse_opml_fallback(self, file_path: Path) -> List[Dict[str, Any]]:
        """Fallback parser using regex for problematic OPML files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re
            feeds = []
            
            # Use regex to find outline elements with xmlUrl
            pattern = r'<outline[^>]*xmlUrl="([^"]+)"[^>]*(?:text="([^"]*)")?[^>]*(?:title="([^"]*)")?[^>]*/?>'
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                url, text, title = match
                
                # Clean up the extracted data
                feed_info = {
                    "title": (title or text or "").strip(),
                    "text": (text or title or "").strip(),
                    "description": "",
                    "url": url.strip(),
                    "type": "rss"
                }
                
                if feed_info["url"] and feed_info["title"]:
                    feeds.append(feed_info)
            
            logger.info(f"Fallback parser found {len(feeds)} feeds in {file_path}")
            return feeds
            
        except Exception as e:
            logger.error(f"Fallback parsing also failed for {file_path}: {e}")
            return []
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all available categories"""
        categories = []
        for key, data in self.feeds_cache.items():
            categories.append({
                "key": key,
                "type": data["type"],
                "category": data["category"],
                "display_name": data["display_name"],
                "feed_count": len(data["feeds"])
            })
        
        # Sort by type and then by category name
        categories.sort(key=lambda x: (x["type"], x["category"]))
        return categories
    
    def get_feeds_by_category(self, category_key: str) -> List[Dict[str, Any]]:
        """Get all feeds for a specific category"""
        return self.feeds_cache.get(category_key, {}).get("feeds", [])
    
    def search_feeds(self, query: str, category_filter: str = None) -> List[Dict[str, Any]]:
        """Search feeds by title, description, or URL"""
        query = query.lower().strip()
        results = []
        
        categories_to_search = [category_filter] if category_filter else self.feeds_cache.keys()
        
        for category_key in categories_to_search:
            if category_key not in self.feeds_cache:
                continue
                
            category_data = self.feeds_cache[category_key]
            for feed in category_data["feeds"]:
                # Search in title, description, and URL
                searchable_text = " ".join([
                    feed.get("title", ""),
                    feed.get("description", ""),
                    feed.get("url", ""),
                    feed.get("text", "")
                ]).lower()
                
                if query in searchable_text:
                    result = feed.copy()
                    result["category_key"] = category_key
                    result["category_display"] = category_data["display_name"]
                    results.append(result)
        
        return results
    
    def get_popular_feeds(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular/recommended feeds"""
        popular = []
        
        # Get available categories and prioritize them
        available_categories = list(self.feeds_cache.keys())
        
        # Prioritize certain categories that exist
        priority_order = [
            # Look for country-based feeds first
            "country_United States",
            "country_United Kingdom",
            "country_Canada",
            # Then look for any recommended categories
        ]
        
        # Add any available recommended categories
        recommended_cats = [cat for cat in available_categories if cat.startswith("recommended_")]
        priority_order.extend(recommended_cats)
        
        # Add any other country categories
        country_cats = [cat for cat in available_categories if cat.startswith("country_") and cat not in priority_order]
        priority_order.extend(country_cats)
        
        for category_key in priority_order:
            if category_key in self.feeds_cache:
                category_data = self.feeds_cache[category_key]
                feeds_to_take = min(3, len(category_data["feeds"]))  # Take up to 3 from each
                
                for feed in category_data["feeds"][:feeds_to_take]:
                    result = feed.copy()
                    result["category_key"] = category_key
                    result["category_display"] = category_data["display_name"]
                    popular.append(result)
                    
                    if len(popular) >= limit:
                        return popular[:limit]
        
        return popular
    
    def get_english_categories(self) -> List[Dict[str, Any]]:
        """Get categories that are likely to contain English-language feeds"""
        english_countries = [
            "United States", "United Kingdom", "Canada",
            "Australia", "Ireland", "Hong Kong SAR China"
        ]
        
        categories = []
        for key, data in self.feeds_cache.items():
            # Include all recommended categories (usually English)
            if data["type"] == "recommended":
                categories.append({
                    "key": key,
                    "type": data["type"],
                    "category": data["category"],
                    "display_name": data["display_name"],
                    "feed_count": len(data["feeds"])
                })
            # Include English-speaking countries
            elif data["type"] == "country" and any(country in data["category"] for country in english_countries):
                categories.append({
                    "key": key,
                    "type": data["type"],
                    "category": data["category"],
                    "display_name": data["display_name"],
                    "feed_count": len(data["feeds"])
                })
        
        categories.sort(key=lambda x: (x["type"], x["category"]))
        return categories
    
    def get_english_feeds(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get feeds from English-speaking sources"""
        english_feeds = []
        english_categories = self.get_english_categories()
        
        for cat_info in english_categories:
            category_data = self.feeds_cache.get(cat_info["key"], {})
            for feed in category_data.get("feeds", []):
                result = feed.copy()
                result["category_key"] = cat_info["key"]
                result["category_display"] = cat_info["display_name"]
                english_feeds.append(result)
                
                if len(english_feeds) >= limit:
                    return english_feeds[:limit]
        
        return english_feeds

    def is_available(self) -> bool:
        """Check if feed discovery database is available"""
        return self.repo_available and len(self.feeds_cache) > 0

    def get_feed_stats(self) -> Dict[str, Any]:
        """Get statistics about the feed database"""
        if not self.is_available():
            return {
                "total_feeds": 0,
                "total_categories": 0,
                "english_feeds": 0,
                "english_categories": 0,
                "by_type": {},
                "available": False,
                "message": "Feed discovery database not available. Run setup script to enable."
            }
        
        total_feeds = sum(len(data["feeds"]) for data in self.feeds_cache.values())
        
        by_type = {}
        for data in self.feeds_cache.values():
            feed_type = data["type"]
            if feed_type not in by_type:
                by_type[feed_type] = 0
            by_type[feed_type] += len(data["feeds"])
        
        english_categories = self.get_english_categories()
        english_feeds_count = sum(cat["feed_count"] for cat in english_categories)
        
        return {
            "total_feeds": total_feeds,
            "total_categories": len(self.feeds_cache),
            "english_feeds": english_feeds_count,
            "english_categories": len(english_categories),
            "by_type": by_type,
            "available": True
        }


# Global instance
feed_discovery = FeedDiscovery()