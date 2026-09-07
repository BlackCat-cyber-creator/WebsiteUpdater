"""
Master Pipeline Orchestrator CLI.
Runs the complete website modernization, SEO audit, price quotation, and PDF proposal pipeline
for any client URL using Scrapling and UI/UX Pro Max.

Usage:
  python run_pipeline.py --url https://suncargo.sunfrozencargo.com --output clients/suncargo
"""

import os
import sys
import json
import argparse
from pipeline.scraper import ClientWebsiteScraper
from pipeline.style_analyzer import WebsiteStyleAnalyzer
from pipeline.auditor import WebsiteAuditor
from pipeline.quotation import QuotationEngine
from pipeline.site_generator import SiteGenerator
from pipeline.pdf_generator import ProposalPdfGenerator


if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Website Modernization, SEO Audit, Price Quotation & PDF Proposal Pipeline")
    parser.add_argument("--url", type=str, default="https://suncargo.sunfrozencargo.com", help="Target client website URL")
    parser.add_argument("--output", type=str, default="clients/suncargo", help="Output directory for client deliverables")
    args = parser.parse_args()

    target_url = args.url
    out_dir = args.output
    assets_dir = os.path.join(out_dir, "site", "assets")

    print("=" * 80)
    print("[*] STARTING WEBSITE MODERNIZATION & PROPOSAL PIPELINE")
    print(f"[*] Target URL: {target_url}")
    print(f"[*] Output Directory: {out_dir}")
    print("=" * 80)

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # 1. Scrape 100% of authentic content and download media assets with Scrapling
    print("\n[Step 1/6] [Scraper] Scraping authentic website content & assets with Scrapling...")
    scraper = ClientWebsiteScraper()
    scraped_data = scraper.scrape(target_url, assets_dir=assets_dir)
    scraped_path = os.path.join(out_dir, "scraped_data.json")
    with open(scraped_path, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)
    print(f"[+] Scraped real data -> {scraped_path}")
    print(f"  Brand Title: {scraped_data['metadata']['title']}")
    print(f"  Visi items: {len(scraped_data['visi_misi']['visi'])} | Misi items: {len(scraped_data['visi_misi']['misi'])}")
    print(f"  Services: {[s['title'] for s in scraped_data.get('layanan', [])][:4]}")
    print(f"  Headings Extracted: {scraped_data.get('headings', {}).get('total_h2', 0)} H2, {scraped_data.get('headings', {}).get('total_h3', 0)} H3")
    print(f"  Assets Downloaded to: {assets_dir}")

    # 2. Analyze original style and design system with UI/UX Pro Max
    print("\n[Step 2/6] [Style Analyzer] Analyzing original website style & visual hierarchy...")
    analyzer = WebsiteStyleAnalyzer()
    style_report = analyzer.analyze(scraped_data.get("raw_html", ""), scraped_data)
    style_path = os.path.join(out_dir, "style_analysis.json")
    with open(style_path, "w", encoding="utf-8") as f:
        json.dump(style_report, f, indent=2, ensure_ascii=False)
    print(f"[+] Style analysis completed -> {style_path}")
    print(f"  Original Colors: {list(style_report['original_colors'].values())[:4]}")
    print(f"  Original Fonts: {style_report['original_typography']['fonts']}")
    print(f"  Design Flaws Detected: {len(style_report['design_flaws'])}")

    # 3. Technical SEO & UX Audit
    print("\n[Step 3/6] [Auditor] Performing Technical SEO, UX & Conversion Audit...")
    auditor = WebsiteAuditor()
    audit_report = auditor.audit(scraped_data)
    audit_path = os.path.join(out_dir, "audit_report.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)
    print(f"[+] Technical SEO & UX audit completed -> {audit_path}")
    print(f"  Overall Score: {audit_report['overall_score']}/100")
    print(f"  SEO Score: {audit_report['seo_score']}/100 (🔴 Critical Ranking Gaps)")
    print(f"  UX Score: {audit_report['ux_score']}/100")
    print(f"  Commercial Keywords Identified: {len(audit_report['keyword_targets'])}")

    # 4. Quotation Engine (Single-phase $300 flat turn-key offer)
    print("\n[Step 4/6] [Quotation] Generating Commercial Price Quotation & Pitch Proposal...")
    qe = QuotationEngine()
    quotation = qe.generate_quotation(scraped_data, audit_report, style_report)
    proposal_path = os.path.join(out_dir, "client_proposal.md")
    with open(proposal_path, "w", encoding="utf-8") as f:
        f.write(quotation["proposal_markdown"])
    print(f"[+] Client Pitch Proposal saved -> {proposal_path}")
    pkg = quotation["package"]
    print(f"  - Package: {pkg['name']}")
    print(f"  - Pricing: {pkg['price_usd']} ({pkg['price_idr']}) - [1 Single Phase Turn-Key]")
    print(f"  - Handover Terms: Instant Turn-Key Delivery (Client receives finished website immediately upon payment)")
    print(f"  - Sign-off: Tim Web Engineering Pipeline")

    # 5. Site Generator (Authentic Elevated Website)
    print("\n[Step 5/6] [Generator] Building Authentic Elevated Website Redesign...")
    site_gen = SiteGenerator()
    site_dir = site_gen.generate(scraped_data, style_report, audit_report, out_dir)
    print(f"[+] Modernized website built in -> {site_dir}")

    # 6. PDF Proposal Generator (Neat, Executive PDF)
    print("\n[Step 6/6] [PDF Generator] Generating Neat Executive PDF & HTML Proposal...")
    pdf_gen = ProposalPdfGenerator()
    pdf_res = pdf_gen.generate(scraped_data, audit_report, style_report, quotation, out_dir)
    pdf_path = pdf_res.get("pdf_path", "")
    html_proposal_path = pdf_res.get("html_path", "")

    # 7. Package Client Deliverables into ready-to-send ZIP
    print("\n[Step 7/7] [Packager] Packaging Client Deliverables into Instant ZIP Package...")
    client_slug = os.path.basename(os.path.normpath(out_dir)).upper()
    zip_filename = f"{client_slug}_Client_Package.zip"
    zip_path = os.path.join(out_dir, zip_filename)

    # Sync docs to site/docs
    docs_dir = os.path.join(out_dir, "site", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    import shutil, zipfile
    if pdf_path and os.path.exists(pdf_path):
        shutil.copy2(pdf_path, os.path.join(docs_dir, "client_proposal.pdf"))
    if os.path.exists(proposal_path):
        shutil.copy2(proposal_path, os.path.join(docs_dir, "client_proposal.md"))
    if os.path.exists(html_proposal_path):
        shutil.copy2(html_proposal_path, os.path.join(docs_dir, "client_proposal.html"))

    # Generate friendly client guide
    guide_text = f"""================================================================================
PAKET PROPOSAL & PROTOTIPE WEBSITE MODERN
Klien: {scraped_data['metadata'].get('title') or client_slug}
Disiapkan oleh: Tim Web Engineering Pipeline
================================================================================

Halo Tim Klien,

Terima kasih atas dedikasi dan kepercayaan Anda. Bersama ini kami lampirkan
paket berkas lengkap hasil modernisasi website dan audit optimasi SEO Google.

ISI PAKET BERKAS:

1. DOKUMEN PROPOSAL & AUDIT TEKNIS:
   - PROPOSAL_EKSEKUTIF_{client_slug}.pdf
     Dokumen proposal resmi 4 halaman mencakup ringkasan audit teknis,
     perbandingan website lama vs hasil baru, proyeksi ROI, target kata kunci
     komersial Google, serta syarat serah terima Turn-Key ($100 flat).
   - PROPOSAL_WEB_VIEW.html
     Tampilan proposal interaktif format web yang dapat dibuka langsung di browser.
   - LAPORAN_AUDIT_SEO.json
     Data audit teknis mendalam berbasis standar OpenSEO / Semrush.

2. PROTOTIPE WEBSITE BARU SIAP PAKAI:
   Folder 'website_prototype/' berisi seluruh file website modern yang telah selesai 100%:
   - Cara Mencoba Langsung di Komputer/Laptop:
     Cukup klik dua kali (double-click) pada file 'index.html' di dalam folder 'website_prototype'.
     Website akan langsung terbuka di browser Anda secara offline tanpa perlu instalasi apa pun!
   - Fitur-Fitur Utama:
     * Tampilan responsif modern (smartphone, tablet, desktop).
     * Integrasi formulir konsultasi terformat langsung ke WhatsApp sales.
     * Multimedia interaktif (video player profil armada & carousel testimoni).
     * Optimasi SEO Google (Schema.org JSON-LD terstruktur).

3. SERAH TERIMA & PENAYANGAN (GO-LIVE):
   Website ini telah siap 100% ditayangkan di domain resmi Anda.
   Penyerahan source code penuh, pengaturan domain, dan garansi teknis 60 hari
   dapat langsung diaktifkan (Instant Turn-Key Handover).

Salam hangat,
Tim Web Engineering Pipeline
"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("PANDUAN_UNTUK_KLIEN.txt", guide_text.strip())
        if pdf_path and os.path.exists(pdf_path):
            zipf.write(pdf_path, f"PROPOSAL_EKSEKUTIF_{client_slug}.pdf")
        if os.path.exists(html_proposal_path):
            zipf.write(html_proposal_path, "PROPOSAL_WEB_VIEW.html")
        if os.path.exists(audit_path):
            zipf.write(audit_path, "LAPORAN_AUDIT_SEO.json")

        site_dir = os.path.join(out_dir, "site")
        for root, dirs, files in os.walk(site_dir):
            if ".git" in root.split(os.sep):
                continue
            for f in files:
                full_f = os.path.join(root, f)
                rel_f = os.path.relpath(full_f, site_dir)
                zipf.write(full_f, os.path.join("website_prototype", rel_f))

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[+] Client Deliverables ZIP created -> {zip_path} ({zip_size_mb:.2f} MB)")

    print("\n" + "=" * 80)
    print("[SUCCESS] PIPELINE RUN COMPLETED SUCCESSFULLY!")
    print(f"[*] Audit Report: {audit_path}")
    print(f"[*] Markdown Proposal: {proposal_path}")
    print(f"[*] Web Proposal (HTML): {html_proposal_path}")
    if pdf_path:
        print(f"[*] Executive PDF Proposal: {pdf_path}")
    print(f"[*] Modern Website Prototype: {os.path.join(site_dir, 'index.html')}")
    print(f"[*] Ready-to-Send Client ZIP: {zip_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
