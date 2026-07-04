from typing import List, Dict, Set
import re

class TagGenerator:
    """
    Categorizes text articles, news, and filings using rule-based keyword matching.
    Provides fast, deterministic tagging.
    """
    def __init__(self):
        # Keyword rules map tags to lists of regex/substring patterns
        self.tag_rules: Dict[str, List[str]] = {
            "Macroeconomics": [
                r"\binflation\b", r"\bcpi\b", r"\bfed\b", r"\bfederal reserve\b", 
                r"\binterest rates?\b", r"\brecession\b", r"\bunemployment\b", 
                r"\bgdp\b", r"\btreasur(y|ies)\b", r"\byield curve\b", r"\bmonetary policy\b"
            ],
            "Earnings": [
                r"\bearnings\b", r"\bdividends?\b", r"\brevenue\b", r"\beps\b", 
                r"\bnet income\b", r"\bquarterly profit\b", r"\bprofit beat\b", 
                r"\bearnings release\b", r"\bfinancial results\b"
            ],
            "M&A (Mergers & Acquisitions)": [
                r"\bacquisition\b", r"\bmergers?\b", r"\bbuyout\b", r"\btakeover\b", 
                r"\bacquired\b", r"\bmerging\b", r"\bdeal value\b"
            ],
            "Artificial Intelligence": [
                r"\bai\b", r"\bartificial intelligence\b", r"\bllms?\b", r"\bgpt\b", 
                r"\bgemini\b", r"\bopenai\b", r"\bmachine learning\b", r"\bgpus?\b", 
                r"\bdeep learning\b", r"\bneural networks?\b"
            ],
            "Regulation & Legal": [
                r"\bsec\b", r"\bantitrust\b", r"\blawsuits?\b", r"\bregulation\b", 
                r"\blegal dispute\b", r"\bfines?\b", r"\binvestigations?\b", r"\bcompliance\b"
            ],
            "Cryptocurrency & Web3": [
                r"\bcrypto\b", r"\bcryptocurrenc(y|ies)\b", r"\bbitcoin\b", r"\bethereum\b", 
                r"\bbtc\b", r"\beth\b", r"\bblockchain\b", r"\bsolana\b", r"\bcoinbase\b"
            ],
            "Product Releases": [
                r"\blaunch(es|ed|s|ing)?\b", r"\brelease(s|d|ing)?\b", r"\bannounc(e|es|ed|s|ing)?\b", 
                r"\bnew products?\b", r"\brollouts?\b", r"\bfeatures?\b"
            ],
            "Executive Leadership": [
                r"\bceo\b", r"\bcfo\b", r"\bboard of directors\b", r"\bexecutive chair\b",
                r"\bresign(ed|s)?\b", r"\bappointed\b", r"\bleadership change\b"
            ]
        }

    def generate_tags(self, title: str, content: str = "") -> List[str]:
        """
        Scan title and content to generate a list of matching tags.
        """
        combined_text = f"{title} {content}".lower()
        matched_tags: Set[str] = set()

        for tag, patterns in self.tag_rules.items():
            for pattern in patterns:
                # Compile regex to match word boundaries safely
                try:
                    if re.search(pattern, combined_text):
                        matched_tags.add(tag)
                        break  # Stop checking patterns for this tag if one matches
                except re.error:
                    # Fallback to simple substring match if regex compilation fails
                    clean_pattern = pattern.replace(r"\b", "")
                    if clean_pattern in combined_text:
                        matched_tags.add(tag)
                        break

        return sorted(list(matched_tags))
