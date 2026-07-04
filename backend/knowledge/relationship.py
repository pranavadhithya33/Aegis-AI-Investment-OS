import logging
from typing import List
from sqlalchemy.orm import Session
from backend.database.models import News, Asset
from backend.knowledge.resolver import EntityResolver

logger = logging.getLogger("knowledge.relationship")

class RelationshipBuilder:
    """
    Builds links between unstructured ingestion items (like news feeds) and 
    structured database objects (like Assets or portfolios) using entity resolution.
    """
    def __init__(self, db: Session):
        self.db = db
        self.resolver = EntityResolver(db)

    def link_news_item(self, news_item: News) -> bool:
        """
        Scan a news article's title and content, resolve the primary asset discussed,
        and link it by setting news_item.asset_id.
        
        Returns True if a link was successfully identified and saved, False otherwise.
        """
        # If already linked, skip
        if news_item.asset_id is not None:
            return False
            
        combined_text = f"{news_item.title} {news_item.content or ''}"
        
        # 1. Scan title and body for active assets
        resolved_ids = self.resolver.scan_text(combined_text)
        if not resolved_ids:
            return False
            
        # 2. Determine the primary asset
        # Give higher weight to entities mentioned in the title
        title_resolved = self.resolver.scan_text(news_item.title)
        if title_resolved:
            primary_id = title_resolved[0]
        else:
            primary_id = resolved_ids[0]
            
        try:
            news_item.asset_id = primary_id
            self.db.add(news_item)
            self.db.commit()
            logger.info(f"Linked news ID {news_item.id} ('{news_item.title[:40]}...') to Asset ID {primary_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save relationship link for news ID {news_item.id}: {e}")
            return False

    def link_unlinked_news(self) -> int:
        """
        Scan all news items with asset_id == None and attempt to link them.
        Returns the number of news items successfully linked.
        """
        unlinked = self.db.query(News).filter(News.asset_id == None).all()
        if not unlinked:
            return 0
            
        logger.info(f"Scanning {len(unlinked)} unlinked news items for asset relationships...")
        linked_count = 0
        for item in unlinked:
            if self.link_news_item(item):
                linked_count += 1
                
        return linked_count
