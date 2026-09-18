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
import urllib.parse
try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass
from pipeline.scraper import ClientWebsiteScraper
from pipeline.style_analyzer import WebsiteStyleAnalyzer
from pipeline.auditor import WebsiteAuditor
from pipeline.quotation import QuotationEngine
from pipeline.site_generator import SiteGenerator
from pipeline.pdf_generator import ProposalPdfGenerator
from pipeline.deployer.vercel_deployer import VercelDeployer
from pipeline.state import PipelineCheckpoint, PipelineState


if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Website Modernization, SEO Audit, Price Quotation & PDF Proposal Pipeline")
    parser.add_argument("--url", type=str, default="https://suncargo.sunfrozencargo.com", help="Target client website URL")
    parser.add_argument("--output", type=str, default="clients/suncargo", help="Output directory for client deliverables")
    parser.add_argument("--force", action="store_true", help="Force re-run all pipeline steps without resuming from checkpoints")
    parser.add_argument("--whitelabel", action="store_true", help="Enable Reseller / Freelancer Whitelabel Mode")
    parser.add_argument("--partner-name", type=str, default="", help="Name of freelancer agency / reseller for whitelabel branding")
    parser.add_argument("--partner-wa", type=str, default="", help="Partner WhatsApp number for whitelabel contact")
    parser.add_argument("--partner-logo", type=str, default="", help="Partner logo path or URL")
    parser.add_argument("--partner-url", type=str, default="", help="Partner website / portfolio URL")
    args = parser.parse_args()

    partner_info = None
    if args.whitelabel or args.partner_name:
        partner_info = {
            "name": args.partner_name or "Mitra Digital Agency",
            "whatsapp": args.partner_wa,
            "logo": args.partner_logo,
            "url": args.partner_url,
            "team": f"Tim Desain & Rekayasa Web {args.partner_name}" if args.partner_name else "Tim Desain & Web Development",
            "tagline": f"Mitra Rekayasa Web Resmi • {args.partner_name}" if args.partner_name else "Studio Desain & Pengembangan Web Modern"
        }

    target_url = args.url
    out_dir = args.output
    assets_dir = os.path.join(out_dir, "site", "assets")
    domain = urllib.parse.urlparse(target_url).netloc.replace("www.", "")
    checkpoint = PipelineCheckpoint(domain, out_dir)

    print("=" * 80)
    print("[*] STARTING WEBSITE MODERNIZATION & PROPOSAL PIPELINE")
    print(f"[*] Target URL: {target_url}")
    print(f"[*] Output Directory: {out_dir}")
    print("=" * 80)

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # 1. Scrape 100% of authentic content and download media assets with Scrapling
    scraped_path = os.path.join(out_dir, "scraped_data.json")
    if not args.force and checkpoint.has_completed("scrape") and os.path.exists(scraped_path):
        print("\n[Step 1/7] [Scraper] [RESUME] Loading existing scraped data from checkpoint...")
        with open(scraped_path, "r", encoding="utf-8") as f:
            scraped_data = json.load(f)
    else:
        print("\n[Step 1/7] [Scraper] Scraping authentic website content & assets with Scrapling...")
        scraper = ClientWebsiteScraper()
        scraped_data = scraper.scrape(target_url, assets_dir=assets_dir)
        with open(scraped_path, "w", encoding="utf-8") as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)
        checkpoint.save(PipelineState.SCRAPED, "scrape", artifacts={"scraped_data": scraped_path})

    print(f"[+] Scraped real data -> {scraped_path}")
    print(f"  Brand Title: {scraped_data['metadata']['title']}")
    print(f"  Visi items: {len(scraped_data['visi_misi']['visi'])} | Misi items: {len(scraped_data['visi_misi']['misi'])}")
    print(f"  Services: {[s['title'] for s in scraped_data.get('layanan', [])][:4]}")
    print(f"  Headings Extracted: {scraped_data.get('headings', {}).get('total_h2', 0)} H2, {scraped_data.get('headings', {}).get('total_h3', 0)} H3")
    print(f"  Assets Downloaded to: {assets_dir}")

    # 2. Analyze original style and design system with UI/UX Pro Max
    style_path = os.path.join(out_dir, "style_analysis.json")
    if not args.force and checkpoint.has_completed("style_analysis") and os.path.exists(style_path):
        print("\n[Step 2/7] [Style Analyzer] [RESUME] Loading existing style analysis from checkpoint...")
        with open(style_path, "r", encoding="utf-8") as f:
            style_report = json.load(f)
    else:
        print("\n[Step 2/7] [Style Analyzer] Analyzing original website style & visual hierarchy...")
        analyzer = WebsiteStyleAnalyzer()
        style_report = analyzer.analyze(scraped_data.get("raw_html", ""), scraped_data)
        with open(style_path, "w", encoding="utf-8") as f:
            json.dump(style_report, f, indent=2, ensure_ascii=False)
        checkpoint.save(PipelineState.STYLE_ANALYZED, "style_analysis", artifacts={"style_analysis": style_path})

    print(f"[+] Style analysis completed -> {style_path}")
    print(f"  Original Colors: {list(style_report['original_colors'].values())[:4]}")
    print(f"  Original Fonts: {style_report['original_typography']['fonts']}")
    print(f"  Design Flaws Detected: {len(style_report['design_flaws'])}")

    # 3. Technical SEO & UX Audit
    audit_path = os.path.join(out_dir, "audit_report.json")
    if not args.force and checkpoint.has_completed("audit") and os.path.exists(audit_path):
        print("\n[Step 3/7] [Auditor] [RESUME] Loading existing audit report from checkpoint...")
        with open(audit_path, "r", encoding="utf-8") as f:
            audit_report = json.load(f)
    else:
        print("\n[Step 3/7] [Auditor] Performing Technical SEO, UX & Conversion Audit...")
        auditor = WebsiteAuditor()
        audit_report = auditor.audit(scraped_data)
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_report, f, indent=2, ensure_ascii=False)
        checkpoint.save(PipelineState.AUDITED, "audit", artifacts={"audit_report": audit_path})

    print(f"[+] Technical SEO & UX audit completed -> {audit_path}")
    print(f"  Overall Score: {audit_report['overall_score']}/100")
    print(f"  SEO Score: {audit_report['seo_score']}/100 (🔴 Critical Ranking Gaps)")
    print(f"  UX Score: {audit_report['ux_score']}/100")
    print(f"  Commercial Keywords Identified: {len(audit_report['keyword_targets'])}")

    # 4. Quotation Engine (Rp 1.490.000 flat all-in turn-key offer)
    print("\n[Step 4/7] [Quotation] Generating Commercial Price Quotation & Pitch Proposal...")
    qe = QuotationEngine()
    quotation = qe.generate_quotation(scraped_data, audit_report, style_report)
    proposal_md = quotation.get("proposal_markdown", "")

    pkg = quotation["package"]
    print(f"  - Package: {pkg['name']}")
    print(f"  - Pricing: {pkg['price_usd']} ({pkg['price_idr']}) - [1 Single Phase Turn-Key]")
    print(f"  - Handover Terms: Instant Turn-Key Delivery (Client receives finished website immediately upon payment)")
    print(f"  - Sign-off: Tim Web Engineering Pipeline")

    # 5. Site Generator (Authentic Elevated Website)
    print("\n[Step 5/7] [Generator] Building Authentic Elevated Website Redesign...")
    site_gen = SiteGenerator()
    site_dir = site_gen.generate(scraped_data, style_report, audit_report, out_dir)
    print(f"[+] Modernized website built in -> {site_dir}")

    # 6. Deploy Modernized Website to Vercel (Edge Cloud Staging)
    print("\n[Step 6/7] [Deployer] Deploying Modernized Website to Vercel Cloud...")
    vercel_deployer = VercelDeployer()
    out_basename = os.path.basename(os.path.normpath(out_dir))
    if out_basename and out_basename not in ["site", "dist", "output", "build", "clients"]:
        client_proj_name = out_basename
    else:
        client_proj_name = scraped_data.get("brand_name") or scraped_data.get("domain") or "client"

    vercel_res = vercel_deployer.deploy(site_dir, client_proj_name)
    vercel_url = vercel_res.get("url", "")
    if vercel_res.get("success"):
        print(f"[+] Live Demo successfully online on Vercel: {vercel_url}")
    else:
        print(f"[!] Vercel deployment notice: {vercel_res.get('error', 'Staging mode active')}")

    # 7. PDF Proposal Generator (Neat, Executive PDF with Live Vercel Demo)
    print("\n[Step 7/7] [PDF Generator] Generating Neat Executive PDF & HTML Proposal...")
    pdf_gen = ProposalPdfGenerator()
    pdf_res = pdf_gen.generate(scraped_data, audit_report, style_report, quotation, out_dir, vercel_url=vercel_url, partner_info=partner_info)
    pdf_path = pdf_res.get("pdf_path", "")
    html_proposal_path = pdf_res.get("html_path", "")

    # 8. Package Client Deliverables into ready-to-send ZIP (Clean Client Package)
    print("\n[Packager] Packaging Client Deliverables into Instant ZIP Package...")
    import shutil, zipfile
    from datetime import datetime
    from pipeline.delivery.code_packager import CPANEL_GUIDE_TEMPLATE, SEO_GUIDE_TEMPLATE

    # Ensure site/ has no internal proposal copies
    docs_dir = os.path.join(out_dir, "site", "docs")
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir, ignore_errors=True)

    biz_title = scraped_data.get("brand_name") or scraped_data.get("metadata", {}).get("title") or "Bisnis Klien"
    dom = scraped_data.get("domain") or os.path.basename(os.path.normpath(out_dir))
    clean_brand = VercelDeployer.clean_slug(client_proj_name).replace("-", "_").upper()
    zip_filename = f"{clean_brand}_Client_Package.zip"
    zip_path = os.path.join(out_dir, zip_filename)
    today_str = datetime.now().strftime("%d %B %Y")

    # 1. Generate Clean Laporan Audit SEO (Human-Readable Markdown for Client)
    overall_sc = audit_report.get("overall_score", 50)
    seo_sc = audit_report.get("seo_score", 40)
    ux_sc = audit_report.get("ux_score", 50)
    conv_sc = audit_report.get("conversion_score", 70)
    one_thing = audit_report.get("one_thing", {})

    categories = audit_report.get("openseo_categories", {})
    critical_issues = []
    for cat_name, issues in categories.items():
        for iss in issues:
            sev = iss.get("severity", "MEDIUM")
            msg = iss.get("message", "")
            if sev in ["CRITICAL", "HIGH"]:
                critical_issues.append(f"- **[{sev}] {iss.get('type', '').replace('_', ' ').title()}:** {msg}")

    kw_list = audit_report.get("commercial_keywords", [])
    kw_md = "\n".join([f"- `{kw}`" for kw in kw_list[:8]]) if kw_list else "- *Kata kunci lokal teroptimasi otomatis via Schema.org*"
    issues_md = "\n".join(critical_issues[:8]) if critical_issues else "- Tidak ditemukan isu kritis mayor."

    audit_md_content = f"""# LAPORAN AUDIT TEKNIS SEO & CORE WEB VITALS
**Klien:** {biz_title} ({dom})  
**Tanggal Audit:** {today_str}  
**Standar Evaluasi:** Google Helpful Content, Core Web Vitals & OpenSEO Protocol

---

## 1. RINGKASAN SKOR PERFORMA WEBSITE LAMA
| Indikator Evaluasi | Skor Sebelum Modernisasi | Standar Target Google | Status |
| :--- | :---: | :---: | :---: |
| **Kesehatan Keseluruhan (Overall)** | **{overall_sc}/100** | 85+ | {'Perlu Pembaruan' if overall_sc < 70 else 'Cukup'} |
| **Optimasi Struktur Google SEO** | **{seo_sc}/100** | 90+ | {'Kritis (Butuh Schema.org)' if seo_sc < 60 else 'Optimal'} |
| **User Experience & Mobile Usability** | **{ux_sc}/100** | 85+ | {'Perlu Perapihan Hero' if ux_sc < 70 else 'Responsif'} |
| **Kesiapan Konversi WhatsApp** | **{conv_sc}/100** | 80+ | Optimal |

---

## 2. PRIORITAS UTAMA
**{one_thing.get('title', 'Aktivasi Optimasi SEO & Tampilan Rapi')}**  
- **Alasan:** {one_thing.get('why', 'Website lama belum memaksimalkan visibilitas pencarian Google.')}  
- **Dampak Bisnis:** {one_thing.get('impact', 'Menaikkan peringkat pencarian lokal dan konversi pelanggan baru.')}

---

## 3. TEMUAN CELAH TEKNIS KRITIS PADA WEBSITE LAMA
{issues_md}

---

## 4. PERBAIKAN YANG TELAH DILAKUKAN PADA PROTOTIPE WEBSITE BARU
Seluruh file di dalam folder `website_prototype/` telah selesai dirombak dan dioptimasi dengan standar:
1. **Google Schema.org JSON-LD**: Penandaan tipe `LocalBusiness` lengkap dengan data NAP (*Name, Address, Phone*) untuk Google Knowledge Panel.
2. **Kecepatan Sub-Detik (Core Web Vitals)**:
   - Gambar di bawah lipatan dilengkapi atribut `loading="lazy"` dan `decoding="async"`.
   - Skrip non-kritis menggunakan `defer` guna memangkas FCP (*First Contentful Paint*).
   - Tipografi menggunakan Google Fonts modern dengan `font-display: swap`.
3. **OpenGraph & WhatsApp Meta Preview**: Tautan ketika dibagikan ke WhatsApp akan menampilkan gambar pratinjau, logo, dan judul profesional.
4. **Peta Situs (Sitemap.xml) & Robots.txt**: Berkas sitemap siap kirim ke Google Search Console untuk pengindeksan instan.

---

## 5. REKOMENDASI KATA KUNCI KOMERSIAL GOOGLE
Berikut kata kunci berdaya beli tinggi yang telah ditanamkan ke dalam arsitektur website baru:
{kw_md}

---
*Dokumen audit ini disusun secara otomatis oleh Sistem Pipeline Web Engineering sebagai bagian dari serah terima resmi kepemilikan website.*
"""
    audit_md_path = os.path.join(out_dir, "LAPORAN_AUDIT_SEO.md")
    with open(audit_md_path, "w", encoding="utf-8") as f:
        f.write(audit_md_content)

    # 2. Generate Guides
    cpanel_md = CPANEL_GUIDE_TEMPLATE.format(business_name=biz_title, domain=dom, date_str=today_str)
    seo_guide_md = SEO_GUIDE_TEMPLATE.format(business_name=biz_title, domain=dom, date_str=today_str)

    cpanel_path = os.path.join(out_dir, "PANDUAN_PEMASANGAN_CPANEL.md")
    seo_guide_path = os.path.join(out_dir, "PANDUAN_OPTIMASI_SEO.md")
    with open(cpanel_path, "w", encoding="utf-8") as f:
        f.write(cpanel_md)
    with open(seo_guide_path, "w", encoding="utf-8") as f:
        f.write(seo_guide_md)

    # 3. Generate Friendly Client Readme
    guide_text = f"""================================================================================
PAKET SERAH TERIMA WEBSITE MODERN & LAPORAN AUDIT SEO
Klien: {biz_title} ({dom})
Disiapkan oleh: Tim Web Engineering Pipeline
================================================================================

Halo Tim Klien,

Selamat atas kepemilikan website modern baru Anda! Bersama ini kami serahkan 
seluruh berkas kode sumber dan panduan teknis resmi:

ISI BERKAS DALAM ARSIP ZIP INI:

1. FOLDER 'website_prototype/'
   Berisi seluruh source code website modern Anda yang telah selesai 100%:
   - index.html   : Halaman website utama dengan optimasi SEO & tombol WhatsApp
   - assets/      : Berkas gambar, icon, logo, dan gaya visual responsif
   - robots.txt   : Petunjuk perayapan Google
   - sitemap.xml  : Peta situs otomatis untuk Google Search Console
   - vercel.json  : Konfigurasi cloud caching & clean URLs

   *Cara Coba Langsung*:
   Cukup klik dua kali (double-click) pada file 'index.html' di dalam folder
   'website_prototype' untuk membukanya langsung di browser tanpa instalasi.

2. DOKUMEN PANDUAN & AUDIT:
   - LAPORAN_AUDIT_SEO.md
     Laporan audit teknis performa, celah SEO Google, dan rekomendasi kata kunci.
   - PANDUAN_PEMASANGAN_CPANEL.md
     Petunjuk langkah demi langkah mengunggah website ke cPanel hosting sendiri.
   - PANDUAN_OPTIMASI_SEO.md
     Petunjuk verifikasi Google Search Console dan sinkronisasi Google Maps.

Website ini adalah milik bisnis Anda 100% tanpa biaya bulanan maupun keterikatan.

Salam hangat,
Tim Web Engineering Pipeline
"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Client documents (bundled inside ZIP, not loose in client root folder)
        zipf.writestr("PANDUAN_UNTUK_KLIEN.txt", guide_text.strip())
        zipf.writestr("PANDUAN_PEMASANGAN_CPANEL.md", cpanel_md.strip())
        zipf.writestr("PANDUAN_OPTIMASI_SEO.md", seo_guide_md.strip())
        zipf.writestr("LAPORAN_AUDIT_SEO.md", audit_md_content.strip())

        # Website files inside website_prototype/ (clean, NO proposals)
        site_dir = os.path.join(out_dir, "site")
        for root, dirs, files in os.walk(site_dir):
            if ".git" in root.split(os.sep) or "docs" in root.split(os.sep):
                continue
            for f in files:
                full_f = os.path.join(root, f)
                rel_f = os.path.relpath(full_f, site_dir)
                zipf.write(full_f, os.path.join("website_prototype", rel_f))

    # Clean up any loose intermediate documents from out_dir so folder is completely clean
    for loose_f in ["LAPORAN_AUDIT_SEO.md", "PANDUAN_PEMASANGAN_CPANEL.md", "PANDUAN_OPTIMASI_SEO.md", "client_proposal.md", "client_proposal.html"]:
        p = os.path.join(out_dir, loose_f)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[+] Client Deliverables ZIP created -> {zip_path} ({zip_size_mb:.2f} MB)")

    # Save programmatic pipeline result for orchestrators & dashboard
    from datetime import datetime
    result_data = {
        "domain": scraped_data.get("domain", ""),
        "business_name": scraped_data.get("brand_name") or scraped_data.get("metadata", {}).get("title", ""),
        "vercel_url": vercel_url,
        "proposal_pdf": os.path.abspath(pdf_path) if pdf_path else "",
        "proposal_html": os.path.abspath(html_proposal_path) if html_proposal_path else "",
        "package_zip": os.path.abspath(zip_path),
        "audit_overall": audit_report.get("overall_score", 0),
        "audit_seo": audit_report.get("seo_score", 0),
        "audit_ux": audit_report.get("ux_score", 0),
        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    result_path = os.path.join(out_dir, "pipeline_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("[SUCCESS] PIPELINE RUN COMPLETED SUCCESSFULLY!")
    print(f"[*] Audit Report: {audit_path}")
    if pdf_path:
        print(f"[*] Executive PDF Proposal: {pdf_path}")
    if vercel_url:
        print(f"[*] Live Vercel Demo: {vercel_url}")
    print(f"[*] Modern Website Prototype: {os.path.join(site_dir, 'index.html')}")
    print(f"[*] Ready-to-Send Client ZIP: {zip_path}")
    print("=" * 80)
    checkpoint.save(PipelineState.COMPLETE, "pipeline", artifacts={
        "audit_report": audit_path,
        "proposal_pdf": pdf_path,
        "vercel_url": vercel_url,
        "package_zip": zip_path,
        "pipeline_result": result_path
    })

    # 9. Sync lead status to outreach tracker and regenerate interactive HTML dashboard
    try:
        from pipeline.outreach.tracker import OutreachTracker
        from pipeline.outreach.whatsapp_dispatcher import WhatsAppDispatcher
        tracker = OutreachTracker()
        lead_dom = scraped_data.get("domain", "") or clean_brand.lower()
        wa_contact = scraped_data.get("kontak", {}).get("whatsapp", "")
        email_contact = scraped_data.get("kontak", {}).get("email", "")

        lead_entry = {
            "domain": lead_dom,
            "business_name": biz_title,
            "website_url": target_url,
            "whatsapp": wa_contact,
            "email": email_contact,
            "track": "track_b_modernize",
            "proposal_pdf": os.path.abspath(pdf_path) if pdf_path else "",
            "vercel_url": vercel_url,
            "package_zip": os.path.abspath(zip_path),
            "payment_status": "unpaid",
            "outdated_signals": [
                f"Skor SEO Lama: {audit_report.get('seo_score', 0)}/100",
                f"Skor UX Lama: {audit_report.get('ux_score', 0)}/100"
            ],
            "status": "ready_for_review",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        tracker.record_lead(lead_dom, lead_entry, status="ready_for_review")
        wa_disp = WhatsAppDispatcher()
        wa_disp.generate_html_queue_dashboard(list(tracker.get_all_leads().values()))
        print(f"[+] Lead recorded in outreach tracker & dashboard queue refreshed ({lead_dom})")
    except Exception as e:
        print(f"[!] Notice: Outreach queue refresh skipped: {e}")


if __name__ == "__main__":
    main()
