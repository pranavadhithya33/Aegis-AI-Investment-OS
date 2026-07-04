import os
import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Asset, News
from backend.knowledge.normalizer import Normalizer
from backend.knowledge.resolver import EntityResolver
from backend.knowledge.tagger import TagGenerator
from backend.knowledge.relationship import RelationshipBuilder

# --- 1. NORMALIZER TESTS ---
def test_normalizer_clean_text():
    html_text = "<p>Microsoft <b>announced</b> a new product release.</p>"
    assert Normalizer.clean_text(html_text) == "Microsoft announced a new product release."
    
    whitespace_text = "   Apple    Inc.   reports earnings   "
    assert Normalizer.clean_text(whitespace_text) == "Apple Inc. reports earnings"

def test_normalizer_to_decimal():
    assert Normalizer.to_decimal(123.45) == Decimal("123.45")
    assert Normalizer.to_decimal("1,234.56") == Decimal("1234.56")
    assert Normalizer.to_decimal("nan") is None
    assert Normalizer.to_decimal(None) is None

def test_normalizer_to_date():
    assert Normalizer.to_date("2026-07-03") == date(2026, 7, 3)
    # Millisecond timestamp for 2026-07-03 approx
    assert Normalizer.to_date(1783036800 * 1000) == date(2026, 7, 3)
    assert Normalizer.to_date("invalid-date") is None

# --- 2. ENTITY RESOLVER TESTS ---
def test_entity_resolver():
    db = SessionLocal()
    try:
        resolver = EntityResolver(db)
        
        # Verify MSFT ticker resolution
        msft_id = resolver.resolve_ticker("MSFT")
        assert msft_id is not None
        
        # Verify name resolution with suffixes
        assert resolver.resolve_name("Microsoft Corp.") == msft_id
        assert resolver.resolve_name("Microsoft Corporation") == msft_id
        assert resolver.resolve_name("AAPL") == resolver.resolve_ticker("AAPL")
        
        # Test text scanning
        text = "Today, Microsoft Corp and Apple Inc declared a partnership."
        scanned_ids = resolver.scan_text(text)
        
        assert resolver.resolve_ticker("MSFT") in scanned_ids
        assert resolver.resolve_ticker("AAPL") in scanned_ids
        assert len(scanned_ids) >= 2
    finally:
        db.close()

# --- 3. TAG GENERATOR TESTS ---
def test_tag_generator():
    tagger = TagGenerator()
    
    tags1 = tagger.generate_tags("Fed raises interest rates to curb inflation")
    assert "Macroeconomics" in tags1
    
    tags2 = tagger.generate_tags("Nvidia launches new Blackwell GPU for advanced AI LLMs")
    assert "Artificial Intelligence" in tags2
    assert "Product Releases" in tags2
    
    tags3 = tagger.generate_tags("SEC launches investigation into Bitcoin exchange coinbase")
    assert "Regulation & Legal" in tags3
    assert "Cryptocurrency & Web3" in tags3

# --- 4. RELATIONSHIP BUILDER TESTS ---
def test_relationship_builder():
    db = SessionLocal()
    try:
        # Create unlinked news item mentioning Microsoft
        news_title = "Microsoft releases quarterly financial results"
        news_content = "Microsoft (MSFT) reported revenue growth of 18% in the cloud segment."
        
        # Check if already exists from previous runs, clean up if needed
        existing = db.query(News).filter(News.title == news_title).first()
        if existing:
            db.delete(existing)
            db.commit()
            
        unlinked_news = News(
            title=news_title,
            url="http://example.com/msft-earnings-test",
            content=news_content,
            source="Test Feed",
            published_at=datetime.utcnow()
        )
        db.add(unlinked_news)
        db.commit()
        db.refresh(unlinked_news)
        
        # Verify it starts unlinked
        assert unlinked_news.asset_id is None
        
        # Link it
        builder = RelationshipBuilder(db)
        success = builder.link_news_item(unlinked_news)
        
        assert success is True
        db.refresh(unlinked_news)
        
        # Verify it resolved to MSFT asset ID
        msft_asset = db.query(Asset).filter(Asset.ticker == "MSFT").first()
        assert unlinked_news.asset_id == msft_asset.id
        
        # Clean up
        db.delete(unlinked_news)
        db.commit()
    finally:
        db.close()
