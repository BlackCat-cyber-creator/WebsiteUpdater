"""
Master Autonomous Lead Finder & Outreach Orchestrator ($100 Turn-Key Engine).
Discovers Indonesian SME businesses (Dual-Track: Track A Web Baru vs Track B Modernisasi),
generates Swiss Minimalist websites or audits technical SEO gaps, deploys to Vercel,
packages clean source code for cPanel, and handles live-rate WhatsApp engagement & settlements.

Usage:
  # 1. Setup dedicated WhatsApp account (one-time QR scan):
  python auto_outreach.py --setup-wa

  # 2. Search & harvest SME leads from Google Maps (10 to 1,000 reviews):
  python auto_outreach.py --maps "distributor bahan plastik surabaya" --limit 3 --dry-run

  # 3. Launch Whitespace Minimalist Review Dashboard Server:
  python auto_outreach.py --dashboard

  # 4. Listen for client WhatsApp replies & auto-send demo/options:
  python auto_outreach.py --listen-replies

  # 5. Programmatic deployment to Vercel:
  python auto_outreach.py --deploy-vercel suncargo.sunfrozencargo.com

  # 6. Package clean source code .ZIP & cPanel guide:
  python auto_outreach.py --package suncargo.sunfrozencargo.com

  # 7. Generate $100 live-rate invoice link:
  python auto_outreach.py --create-invoice suncargo.sunfrozencargo.com
"""

import sys
import argparse

try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from pipeline.commands import dispatch_cli, MID_TIER_CATEGORIES
from pipeline.commands.context import execute_pipeline_for_client


def main():
    parser = argparse.ArgumentParser(description="Autonomous Indonesian Mid-Tier Business Scanner & Outreach System ($100 Turn-Key Engine)")
    parser.add_argument("--setup-wa", action="store_true", help="Launch interactive WhatsApp Web QR setup for dedicated account")
    parser.add_argument("--maps", type=str, default="", help="Search local developing SME businesses directly from Google Maps (e.g. 'distributor bahan plastik surabaya')")
    parser.add_argument("--query", type=str, default="", help="Search query (e.g. 'ekspedisi surabaya makassar')")
    parser.add_argument("--category", choices=list(MID_TIER_CATEGORIES.keys()), default=None,
                        help="Target curated mid-tier niche")
    parser.add_argument("--domain", type=str, default="", help="Direct single target domain (e.g. 'suncargo.sunfrozencargo.com')")
    parser.add_argument("--limit", type=int, default=3, help="Maximum number of candidate leads to process per run")
    parser.add_argument("--track", choices=["a", "b", "all"], default="all", help="Filter target processing track (a = Web Baru di Vercel, b = Modernisasi & SEO, all = keduanya)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate outreach without sending live messages (Default: True)")
    parser.add_argument("--live", action="store_true", help="Enable actual live outreach via dedicated SMTP and WhatsApp")
    parser.add_argument("--test-email", type=str, default="", help="Send a test proposal email to this address to verify SMTP connection")
    parser.add_argument("--generate-queue", action="store_true", help="Regenerate clients/outreach_queue.html from tracker history")
    parser.add_argument("--channel", choices=["all", "whatsapp", "email"], default="all", help="Target communication channel")
    parser.add_argument("--dashboard", action="store_true", help="Launch interactive Review & Approval dashboard server on localhost")
    parser.add_argument("--approve", type=str, default="", help="Approve and send WhatsApp + Email to a specific domain")
    parser.add_argument("--discard", type=str, default="", help="Discard/remove a lead from the outreach queue")
    parser.add_argument("--listen-replies", action="store_true", help="Scan WhatsApp Web for incoming replies and auto-dispatch demo/options")
    parser.add_argument("--deploy-vercel", type=str, default="", help="Deploy a specific client's website to Vercel")
    parser.add_argument("--package", type=str, default="", help="Package clean source code .ZIP and guides for a client domain")
    parser.add_argument("--create-invoice", type=str, default="", help="Generate live-rate invoice (Rp 1.490.000 / dual pricing) with payment link for a client")
    parser.add_argument("--simulate-payment", type=str, default="", help="Simulate a PAID webhook event for an invoice ID to test auto-fulfillment")
    parser.add_argument("--auto-modernize", action="store_true", help="Batch process and modernize all leads in queue (generate websites, deploy to Vercel, generate PDF proposals)")
    parser.add_argument("--min-reviews", type=int, default=10, help="Minimum Google Maps review count filter (Default: 10)")
    parser.add_argument("--max-reviews", type=int, default=1000, help="Maximum Google Maps review count filter (Default: 1000)")
    parser.add_argument("--hunt-outdated", action="store_true", help="Hunt Indonesian B2B websites that already have old/outdated websites (Jalur B Revitalizer via SERP dorking)")
    parser.add_argument("--pre-generate", action="store_true", default=False, help="Pre-emptively generate Vercel demo & PDF proposal upfront (Default: False for fast JIT)")
    parser.add_argument("--whitelabel", action="store_true", help="Enable Reseller / Freelancer Whitelabel Engine")
    parser.add_argument("--partner-name", type=str, default="", help="Partner / Freelancer Agency Brand Name")
    parser.add_argument("--partner-wa", type=str, default="", help="Partner WhatsApp Number")
    parser.add_argument("--partner-logo", type=str, default="", help="Partner Logo Path or URL")
    parser.add_argument("--partner-url", type=str, default="", help="Partner Website or Portfolio URL")

    args = parser.parse_args()
    dispatch_cli(args)


if __name__ == "__main__":
    main()
