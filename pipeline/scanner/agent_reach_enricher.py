"""
Social & Contact Enrichment Module (Agent-Reach).
Backward-compatible wrapper re-exporting ContactEnricher & AgentReachContactEnricher.
"""

from pipeline.scanner.contact_enricher import ContactEnricher, AgentReachContactEnricher

__all__ = ["ContactEnricher", "AgentReachContactEnricher"]


if __name__ == "__main__":
    enricher = ContactEnricher()
    print("Testing social enrichment for 'CV. SUNCARGO'...")
    res = enricher.enrich_from_social_bio("SUNCARGO", "Pontianak")
    print("Enrichment Result:", res)
