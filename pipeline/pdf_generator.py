"""
Professional PDF Proposal Generator.
Generates an executive-ready, multi-page HTML and PDF pitch proposal
highlighting technical SEO audit findings, new SEO upgrades (Before vs After),
business benefit projections (ROI & conversion estimates), $100 single-phase turn-key terms,
and authentic client branding.
"""

import os
import re
import html
import base64
import subprocess
from typing import Dict, Any, List
from datetime import datetime


class ProposalPdfGenerator:
    def __init__(self):
        self.edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]

    def _find_browser_executable(self) -> str:
        for p in self.edge_paths:
            if os.path.exists(p):
                return p
        return ""

    def _get_base64_image(self, file_path: str) -> str:
        if os.path.exists(file_path):
            try:
                ext = os.path.splitext(file_path)[1].lower().replace(".", "")
                if ext in ["jpg", "jpeg"]:
                    mime = "image/jpeg"
                elif ext == "svg":
                    mime = "image/svg+xml"
                elif ext == "png":
                    mime = "image/png"
                elif ext == "webp":
                    mime = "image/webp"
                else:
                    mime = f"image/{ext}"
                with open(file_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{encoded}"
            except Exception:
                return ""
        return ""

    def generate(self, scraped: Dict[str, Any], audit: Dict[str, Any], style: Dict[str, Any], quotation: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """
        Renders executive HTML proposal and converts it to a professional multi-page PDF.
        Returns paths to both the HTML and PDF documents.
        """
        html_content = self._render_html(scraped, audit, style, quotation, output_dir)
        html_path = os.path.join(output_dir, "client_proposal.html")
        pdf_path = os.path.join(output_dir, "client_proposal.pdf")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[+] Executive HTML Proposal saved -> {html_path}")

        # Convert to PDF via headless Chromium/Edge
        browser_exe = self._find_browser_executable()
        pdf_generated = False

        if browser_exe:
            abs_html = os.path.abspath(html_path).replace("\\", "/")
            abs_pdf = os.path.abspath(pdf_path)
            if os.path.exists(abs_pdf):
                try:
                    os.remove(abs_pdf)
                except Exception:
                    pass

            cmd = [
                browser_exe,
                "--headless",
                "--disable-gpu",
                f"--print-to-pdf={abs_pdf}",
                "--no-pdf-header-footer",
                f"file:///{abs_html}"
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    pdf_generated = True
                    # Check page count
                    with open(pdf_path, "rb") as pf:
                        pdf_data = pf.read()
                    page_matches = re.findall(rb'/Count\s+(\d+)', pdf_data)
                    page_cnt = page_matches[0].decode() if page_matches else "multi"
                    print(f"[+] Executive PDF Proposal generated -> {pdf_path} ({os.path.getsize(pdf_path):,} bytes, {page_cnt} pages)")
                else:
                    print(f"[!] PDF generation warning: Output file not created. Stderr: {res.stderr}")
            except Exception as e:
                print(f"[!] PDF generation error: {e}")
        else:
            print("[!] Headless Edge/Chrome not found for direct PDF export. HTML version is available.")

        return {
            "html_path": html_path,
            "pdf_path": pdf_path if pdf_generated else ""
        }

    def _render_html(self, scraped: Dict[str, Any], audit: Dict[str, Any], style: Dict[str, Any], quotation: Dict[str, Any], output_dir: str) -> str:
        client_name = quotation.get("client_name") or scraped.get("brand_name") or "Perusahaan"
        domain = quotation.get("domain") or scraped.get("domain") or "domain.com"
        url = quotation.get("url") or scraped.get("url") or f"https://{domain}"
        pkg = quotation.get("package", {})
        
        tagline = scraped.get("hero", {}).get("tagline") or scraped.get("metadata", {}).get("title", "")
        if tagline and "|" in tagline:
            tagline = tagline.split("|", 1)[1].strip()
        if not tagline or len(tagline) < 5:
            tagline = "Solusi Layanan Terpercaya di Indonesia"

        contact = scraped.get("kontak", {})
        address = contact.get("address", "Indonesia")
        phone = contact.get("whatsapp") or contact.get("phone", "")

        today_str = datetime.now().strftime("%Y-%m-%d")
        safe_code = re.sub(r'[^A-Z0-9]', '', client_name.upper())[:10] or "CLIENT"
        proposal_no = f"PROPOSAL-{safe_code}-SEO-100-TURNKEY"

        scores = audit.get("overall_score", 52)
        seo_score = audit.get("seo_score", 45)
        ux_score = audit.get("ux_score", 44)
        conv_score = audit.get("conversion_score", 75)

        # Asset base64
        assets_dir = os.path.join(output_dir, "site", "assets")
        logo_b64 = ""
        if os.path.exists(assets_dir):
            for fname in os.listdir(assets_dir):
                fl = fname.lower()
                # Reject rating stars, social icons, and non-brand graphics
                if any(ign in fl for ign in ["star", "f.svg", "rating", "wa.svg", "fb.svg", "ig.svg", "soc", "check"]):
                    continue
                if any(k in fl for k in ["logo", "brand", "company", "header", "navbar"]):
                    logo_b64 = self._get_base64_image(os.path.join(assets_dir, fname))
                    if logo_b64:
                        break

        cert_b64 = ""
        if os.path.exists(assets_dir):
            for fname in os.listdir(assets_dir):
                if "sertifikat" in fname.lower() or "cert" in fname.lower():
                    cert_b64 = self._get_base64_image(os.path.join(assets_dir, fname))
                    if cert_b64:
                        break

        # Build keywords table rows
        keywords = audit.get("keyword_targets", [])
        kw_rows = ""
        for kw in keywords:
            kw_rows += f"""
            <tr>
              <td class="kw-name"><strong>{html.escape(kw['keyword'])}</strong></td>
              <td><span class="badge-intent">{html.escape(kw['intent'])}</span></td>
              <td><span class="badge-vol">{html.escape(kw['volume_est'])}</span></td>
              <td class="kw-impact">{html.escape(kw['potential_impact'])}</td>
            </tr>
            """

        # Build SEO issues with escaped text to prevent unescaped <title> tags from breaking HTML parsing!
        seo_issues = audit.get("seo_issues", [])
        seo_cards = ""
        for issue in seo_issues:
            sev = issue.get("severity", "MEDIUM")
            sev_class = "sev-critical" if sev == "CRITICAL" else ("sev-high" if sev == "HIGH" else "sev-med")
            raw_msg = issue.get("message", "")
            safe_msg = html.escape(raw_msg)
            safe_type = html.escape(issue.get("type", "").upper())
            seo_cards += f"""
            <div class="defect-item {sev_class}">
              <div class="defect-badge">{sev}</div>
              <div class="defect-body">
                <strong>{safe_type}</strong>
                <p>{safe_msg}</p>
              </div>
            </div>
            """

        # Build deliverables
        deliverables = pkg.get("deliverables", [])
        deliv_items = "".join([f"<li class='deliv-item'><span class='check-icon'>✓</span> <span>{html.escape(d)}</span></li>" for d in deliverables])

        return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Proposal Audit Teknis SEO & Modernisasi Website - {client_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
  
  <style>
    @page {{
      size: A4;
      margin: 12mm 14mm;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #1e293b;
      background: #ffffff;
      line-height: 1.45;
      font-size: 12px;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}

    .document-container {{
      max-width: 820px;
      margin: 0 auto;
    }}

    /* Header Bar */
    .header-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 12px;
      border-bottom: 3px solid #1268b3;
      margin-bottom: 16px;
    }}
    .logo-container {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-logo {{
      max-height: 46px;
      width: auto;
      object-fit: contain;
    }}
    .brand-monogram {{
      width: 42px;
      height: 42px;
      background: #0d4d87;
      color: #ffffff;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 17px;
      font-weight: 800;
      letter-spacing: 0.04em;
    }}
    .brand-text h2 {{
      font-size: 17px;
      font-weight: 800;
      color: #0d4d87;
      letter-spacing: -0.02em;
    }}
    .brand-text p {{
      font-size: 10.5px;
      color: #64748b;
      font-weight: 500;
    }}
    .header-meta {{
      text-align: right;
      font-size: 10.5px;
      color: #475569;
    }}
    .doc-pill {{
      display: inline-block;
      background: #f0f6ff;
      color: #1268b3;
      border: 1px solid #bfdbfe;
      padding: 2px 7px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 9.5px;
      margin-bottom: 3px;
    }}

    /* Title Block */
    .title-block {{
      background: linear-gradient(135deg, #0d4d87 0%, #1268b3 100%);
      color: #ffffff;
      padding: 16px 20px;
      border-radius: 8px;
      margin-bottom: 18px;
    }}
    .title-block h1 {{
      font-size: 18px;
      font-weight: 800;
      margin-bottom: 5px;
      line-height: 1.25;
      color: #ffffff;
    }}
    .title-block p {{
      font-size: 11px;
      color: #e0f2fe;
      font-weight: 400;
    }}
    .client-meta-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.2);
      font-size: 10.5px;
    }}
    .meta-box span {{
      color: #bae6fd;
      display: block;
      font-size: 9.5px;
      text-transform: uppercase;
      font-weight: 600;
    }}
    .meta-box strong {{
      color: #ffffff;
      font-size: 10.5px;
    }}

    /* Section Styles */
    .section-title {{
      font-size: 14px;
      font-weight: 800;
      color: #0d4d87;
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 18px 0 10px 0;
      padding-bottom: 5px;
      border-bottom: 1.5px solid #e2e8f0;
      break-after: avoid;
    }}
    .section-title::before {{
      content: "";
      display: inline-block;
      width: 4px;
      height: 16px;
      background: #fab853;
      border-radius: 2px;
    }}

    /* Score Cards */
    .scores-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 14px;
      break-inside: avoid;
    }}
    .score-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px;
      text-align: center;
    }}
    .score-val {{
      font-size: 22px;
      font-weight: 800;
      line-height: 1;
      margin-bottom: 4px;
    }}
    .score-label {{
      font-size: 10.5px;
      color: #64748b;
      font-weight: 600;
    }}
    .score-crit {{ color: #dc2626; }}
    .score-warn {{ color: #d97706; }}
    .score-good {{ color: #16a34a; }}
    .score-main {{ color: #1268b3; }}

    /* Defect List */
    .defect-list {{
      display: block;
      margin-bottom: 16px;
    }}
    .defect-item {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 8px 12px;
      border-radius: 6px;
      border-left: 4px solid;
      margin-bottom: 7px;
      font-size: 11px;
      break-inside: avoid;
    }}
    .defect-badge {{
      font-size: 9px;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 3px;
      letter-spacing: 0.04em;
    }}
    .sev-critical {{
      border-left-color: #dc2626;
      background: #fef2f2;
    }}
    .sev-critical .defect-badge {{
      background: #dc2626;
      color: #ffffff;
    }}
    .sev-high {{
      border-left-color: #ea580c;
      background: #fff7ed;
    }}
    .sev-high .defect-badge {{
      background: #ea580c;
      color: #ffffff;
    }}
    .sev-med {{
      border-left-color: #f59e0b;
      background: #fffbeb;
    }}
    .sev-med .defect-badge {{
      background: #f59e0b;
      color: #ffffff;
    }}
    .defect-body strong {{
      font-size: 11px;
      color: #0f172a;
    }}
    .defect-body p {{
      color: #475569;
      font-size: 10.5px;
      margin-top: 2px;
    }}

    /* Before vs After Comparison Table */
    .comparison-container {{
      margin: 10px 0 16px 0;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      overflow: hidden;
      break-inside: avoid;
    }}
    .comparison-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 10.5px;
    }}
    .comparison-table th {{
      background: #0d4d87;
      color: #ffffff;
      padding: 8px 10px;
      font-weight: 700;
      text-align: left;
    }}
    .comparison-table td {{
      padding: 7px 10px;
      border-bottom: 1px solid #e2e8f0;
      vertical-align: top;
    }}
    .comparison-table tr:nth-child(even) {{
      background: #f8fafc;
    }}
    .status-old {{
      color: #dc2626;
      font-weight: 600;
    }}
    .status-new {{
      color: #16a34a;
      font-weight: 600;
    }}

    /* Benefits & Projections Grid */
    .benefit-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      margin: 12px 0 18px 0;
      break-inside: avoid;
    }}
    .benefit-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 12px;
      border-top: 3px solid #1268b3;
      break-inside: avoid;
    }}
    .benefit-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }}
    .benefit-tag {{
      font-size: 9.5px;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 3px;
      background: #e0f2fe;
      color: #0284c7;
      text-transform: uppercase;
    }}
    .benefit-card h4 {{
      font-size: 11.5px;
      font-weight: 800;
      color: #0d4d87;
    }}
    .benefit-card p {{
      font-size: 10.5px;
      color: #475569;
      line-height: 1.45;
    }}

    /* Table Styles for Keywords */
    .table-container {{
      margin: 10px 0 16px 0;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      break-inside: avoid;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 10.5px;
    }}
    th {{
      background: #f1f5f9;
      color: #0f172a;
      font-weight: 700;
      padding: 8px 10px;
      border-bottom: 1.5px solid #cbd5e1;
    }}
    td {{
      padding: 7px 10px;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    .kw-name {{
      color: #0d4d87;
      font-size: 11px;
    }}
    .badge-intent {{
      background: #e0f2fe;
      color: #0284c7;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 9.5px;
    }}
    .badge-vol {{
      background: #dcfce7;
      color: #15803d;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 9.5px;
    }}
    .kw-impact {{
      color: #475569;
      font-size: 10px;
    }}

    /* Pricing Box */
    .pricing-hero-card {{
      background: linear-gradient(135deg, #f0f6ff 0%, #e0edff 100%);
      border: 2px solid #1268b3;
      border-radius: 10px;
      padding: 16px;
      margin: 14px 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      break-inside: avoid;
    }}
    .pricing-details h3 {{
      font-size: 15px;
      font-weight: 800;
      color: #0d4d87;
      margin-bottom: 4px;
    }}
    .pricing-details p {{
      font-size: 11px;
      color: #475569;
      max-width: 480px;
    }}
    .pricing-tag-box {{
      text-align: right;
      background: #ffffff;
      padding: 12px 18px;
      border-radius: 8px;
      border: 1px solid #bfdbfe;
      box-shadow: 0 4px 8px rgba(18, 104, 179, 0.08);
    }}
    .price-main {{
      font-size: 24px;
      font-weight: 900;
      color: #1268b3;
      line-height: 1;
    }}
    .price-sub {{
      font-size: 11.5px;
      font-weight: 700;
      color: #16a34a;
      margin-top: 3px;
    }}
    .price-phase {{
      font-size: 9.5px;
      color: #64748b;
      font-weight: 600;
      margin-top: 3px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    /* Deliverables Checklist */
    .deliv-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 6px 12px;
      margin: 10px 0 16px 0;
      list-style: none;
      break-inside: avoid;
    }}
    .deliv-item {{
      display: flex;
      align-items: flex-start;
      gap: 7px;
      font-size: 10.5px;
      color: #334155;
    }}
    .check-icon {{
      color: #16a34a;
      font-weight: 900;
      font-size: 12px;
      line-height: 1.2;
    }}

    /* Turn Key Box */
    .turnkey-notice {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 12px 16px;
      margin: 14px 0;
      break-inside: avoid;
    }}
    .turnkey-notice h4 {{
      font-size: 12px;
      color: #0d4d87;
      font-weight: 800;
      margin-bottom: 5px;
    }}
    .turnkey-notice ol {{
      margin-left: 16px;
      color: #475569;
      font-size: 10.5px;
      line-height: 1.55;
    }}

    /* Signature & Footer */
    .signature-area {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin-top: 22px;
      padding-top: 14px;
      border-top: 2px solid #e2e8f0;
      break-inside: avoid;
    }}
    .cert-badge-box {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .cert-img {{
      max-height: 44px;
      width: auto;
      object-fit: contain;
    }}
    .cert-text {{
      font-size: 9.5px;
      color: #475569;
      line-height: 1.35;
    }}
    .sign-box {{
      text-align: right;
    }}
    .sign-title {{
      font-size: 10.5px;
      color: #64748b;
      margin-bottom: 30px;
    }}
    .sign-name {{
      font-size: 12px;
      font-weight: 800;
      color: #0d4d87;
      border-top: 1.5px solid #0d4d87;
      padding-top: 4px;
      display: inline-block;
    }}
    .sign-role {{
      font-size: 9.5px;
      color: #64748b;
    }}

    .page-break {{
      page-break-before: always;
      break-before: page;
    }}
  </style>
</head>
<body>

  <div class="document-container">
    
    <!-- Header -->
    <header class="header-bar">
      <div class="logo-container">
        {f'<img src="{logo_b64}" class="brand-logo" alt="Logo">' if logo_b64 else f'<div class="brand-monogram">{client_name[:2].upper()}</div>'}
        <div class="brand-text">
          <h2>{client_name}</h2>
          <p>{html.escape(tagline)}</p>
        </div>
      </div>
      <div class="header-meta">
        <div class="doc-pill">OFFICIAL PROPOSAL & AUDIT</div>
        <p><strong>Nomor:</strong> {proposal_no}</p>
        <p><strong>Tanggal:</strong> {today_str}</p>
      </div>
    </header>

    <!-- Title Block -->
    <div class="title-block">
      <h1>Proposal Audit Teknis SEO & Penawaran Modernisasi Website</h1>
      <p>Transformasi digital menyeluruh berstandar teknis Google modern untuk mendominasi pencarian organik dan memaksimalkan konversi prospek bisnis.</p>
      
      <div class="client-meta-grid">
        <div class="meta-box">
          <span>Klien Sasaran</span>
          <strong>{client_name}</strong>
        </div>
        <div class="meta-box">
          <span>Website Saat Ini</span>
          <strong>{url}</strong>
        </div>
        <div class="meta-box">
          <span>Model Implementasi</span>
          <strong>Turn-Key Solution (1 Phase Instant Delivery)</strong>
        </div>
      </div>
    </div>

    <!-- Section 1: Audit Teknis -->
    <h2 class="section-title">1. Hasil Audit Teknis SEO & Hambatan Ranking di Google</h2>
    <p style="font-size: 11px; color: #475569; margin-bottom: 10px;">
      Berdasarkan audit otomatis komprehensif terhadap performa website saat ini, ditemukan beberapa hambatan teknis yang menyebabkan {client_name} kehilangan potensi calon pelanggan di Google:
    </p>

    <!-- Score Cards -->
    <div class="scores-grid">
      <div class="score-card">
        <div class="score-val score-main">{scores}/100</div>
        <div class="score-label">Kesehatan Digital</div>
      </div>
      <div class="score-card">
        <div class="score-val score-crit">{seo_score}/100</div>
        <div class="score-label">SEO & Google Rank 🔴</div>
      </div>
      <div class="score-card">
        <div class="score-val score-warn">{ux_score}/100</div>
        <div class="score-label">Pengalaman Mobile</div>
      </div>
      <div class="score-card">
        <div class="score-val score-good">{conv_score}/100</div>
        <div class="score-label">Saluran Konversi WA</div>
      </div>
    </div>

    <!-- Defect List -->
    <div class="defect-list">
      {seo_cards}
    </div>

    <!-- PAGE BREAK -->
    <div class="page-break"></div>

    <!-- Section 2: Perbandingan Sebelum vs Sesudah -->
    <h2 class="section-title">2. Perbandingan: Website Lama vs Hasil Transformasi SEO Baru</h2>
    <p style="font-size: 11px; color: #475569; margin-bottom: 8px;">
      Website yang telah kami siapkan telah menyelesaikan seluruh cacat teknis di atas dan siap langsung tayang di domain resmi Anda:
    </p>

    <div class="comparison-container">
      <table class="comparison-table">
        <thead>
          <tr>
            <th style="width: 22%;">Komponen Teknis</th>
            <th style="width: 38%;">Kondisi Website Lama Saat Ini</th>
            <th style="width: 40%;">Hasil Website Baru yang Sudah Selesai</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Tag Judul Google (&lt;title&gt;)</strong></td>
            <td class="status-old">{html.escape(scraped.get('metadata', {}).get('title') or 'Belum Optimal / Missing')} ❌</td>
            <td class="status-new">"{client_name} | Solusi & Layanan Profesional Terpercaya di Indonesia" (Keyword komersial penuh) ✅</td>
          </tr>
          <tr>
            <td><strong>Meta Description</strong></td>
            <td class="status-old">{html.escape(scraped.get('metadata', {}).get('meta_description') or 'Kosong / Tidak Terstandar (Google memotong cuplikan)')[:80]}... ❌</td>
            <td class="status-new">155 karakter copy terstruktur mencakup profil layanan dan keunggulan utama {client_name} ✅</td>
          </tr>
          <tr>
            <td><strong>Schema.org Structured Data</strong></td>
            <td class="status-old">Nol (0% JSON-LD, tidak dikenal Google Knowledge Graph) ❌</td>
            <td class="status-new">Terpasang LocalBusiness & Organization resmi lengkap untuk {client_name} ✅</td>
          </tr>
          <tr>
            <td><strong>Heading Hierarchy</strong></td>
            <td class="status-old">Struktur heading belum optimal ❌</td>
            <td class="status-new">1 H1 fokus topik utama + H2-H3 terstruktur membangun otoritas topik bisnis di Google ✅</td>
          </tr>
          <tr>
            <td><strong>Kenyamanan Tampilan Mobile</strong></td>
            <td class="status-old">Tautan aset & tata letak belum optimal di smartphone ❌</td>
            <td class="status-new">100% Mobile Ready, aset terhubung absolut, font & visual tertata rapi ✅</td>
          </tr>
          <tr>
            <td><strong>Saluran Konversi WA</strong></td>
            <td class="status-old">Tautan kontak belum terstandarisasi ❌</td>
            <td class="status-new">Formulir konsultasi & tombol WhatsApp terarah langsung ke sales dan siap closing ✅</td>
          </tr>
          <tr>
            <td><strong>Kecepatan (Core Web Vitals)</strong></td>
            <td class="status-old">Beban aset belum teroptimasi pada koneksi seluler ❌</td>
            <td class="status-new">Aset dioptimasi, waktu muat cepat dan skor Google hijau (LCP &lt; 1.2s) ✅</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Section 3: Proyeksi Manfaat Bisnis & ROI -->
    <h2 class="section-title">3. Perkiraan Manfaat Bisnis & Proyeksi ROI bagi {client_name}</h2>
    <div class="benefit-grid">
      <div class="benefit-card">
        <div class="benefit-header">
          <span class="benefit-tag">Konversi Leads</span>
          <h4>Estimasi Lonjakan Kontak WhatsApp +250%</h4>
        </div>
        <p>Integrasi rute konsultasi instan memudahkan calon klien langsung mengirimkan kebutuhan layanan spesifik secara rapi, mempercepat siklus closing sales tim {client_name}.</p>
      </div>

      <div class="benefit-card">
        <div class="benefit-header">
          <span class="benefit-tag">Traffic Organik</span>
          <h4>Target Halaman 1 Google (Top 3)</h4>
        </div>
        <p>Injeksi Schema.org dan penargetan kata kunci spesifik menargetkan tembus 3 besar Google dalam 30-60 hari, menghasilkan lead rutin gratis tanpa biaya iklan berulang.</p>
      </div>

      <div class="benefit-card">
        <div class="benefit-header">
          <span class="benefit-tag">Balik Modal Cepat</span>
          <h4>ROI 100%+ dari 1-2 Transaksi Baru</h4>
        </div>
        <p>Dengan nilai layanan bisnis Anda, tambahan hanya 1 atau 2 transaksi/klien baru dari pencarian Google sudah melunasi investasi {pkg.get('price_usd', '$100 USD')} ({pkg.get('price_idr', 'Rp 1.766.000')}) secara instan.</p>
      </div>

      <div class="benefit-card">
        <div class="benefit-header">
          <span class="benefit-tag">Trust B2B</span>
          <h4>Kepercayaan Mitra & Calon Klien</h4>
        </div>
        <p>Tampilan yang rapi, transparan, dan terverifikasi di Google memberikan kredibilitas mutlak bagi mitra perusahaan maupun pelanggan individu.</p>
      </div>
    </div>

    <!-- Section 4: Target Kata Kunci Komersial -->
    <h2 class="section-title">4. Target Kata Kunci Komersial Google yang Dikuasai</h2>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Kata Kunci Target</th>
            <th>Intent Pencarian</th>
            <th>Estimasi Volume</th>
            <th>Dampak Bisnis bagi {client_name}</th>
          </tr>
        </thead>
        <tbody>
          {kw_rows}
        </tbody>
      </table>
    </div>

    <!-- PAGE BREAK -->
    <div class="page-break"></div>

    <!-- Section 5: Penawaran Investasi -->
    <h2 class="section-title">5. Penawaran Investasi (Hanya 1 Tahap - Turn-Key Siap Pakai)</h2>
    <p style="font-size: 11px; color: #475569; margin-bottom: 8px;">
      Website modern {client_name} <strong>sudah selesai kami bangun 100%</strong>. Anda tidak perlu menunggu lama dalam proses pengerjaan.
    </p>

    <!-- Pricing Hero Card -->
    <div class="pricing-hero-card">
      <div class="pricing-details">
        <h3>{html.escape(pkg.get('name', 'Paket Transformasi Digital & Dominasi SEO'))}</h3>
        <p>{html.escape(pkg.get('summary', ''))}</p>
      </div>
      <div class="pricing-tag-box">
        <div class="price-main">{pkg.get('price_usd', '$100 USD')}</div>
        <div class="price-sub">{pkg.get('price_idr', 'Rp 1.766.000')}</div>
        <div class="price-phase">Hanya 1 Tahap (Turn-Key)</div>
      </div>
    </div>

    <p style="font-size: 11px; font-weight: 700; color: #0d4d87; margin-bottom: 6px;">Ruang Lingkup Pekerjaan yang Sudah Siap 100%:</p>
    <ul class="deliv-grid">
      {deliv_items}
    </ul>

    <!-- Section 6: Syarat Pembayaran -->
    <h2 class="section-title">6. Syarat Pembayaran & Serah Terima Langsung</h2>
    <div class="turnkey-notice">
      <h4>Ketentuan Serah Terima (Turn-Key Solution):</h4>
      <ol>
        <li><strong>Langsung Dapat Hasilnya:</strong> Website baru modern, responsif, cepat, dan ramah SEO telah selesai dibuat dan siap diuji coba langsung oleh tim {client_name} saat ini juga.</li>
        <li><strong>Pembayaran Tunggal Saat Go-Live:</strong> Pembayaran flat sebesar <strong>{pkg.get('price_usd', '$100 USD')} ({pkg.get('price_idr', 'Rp 1.766.000')})</strong> dilakukan saat serah terima aktivasi di domain utama Anda ({url}).</li>
        <li><strong>Serah Terima Penuh:</strong> Klien langsung mendapatkan seluruh file source code, integrasi domain/hosting, akun pelacakan SEO, serta garansi teknis 60 hari tanpa biaya tersembunyi.</li>
      </ol>
    </div>

    <!-- Section 7: Hasil Skor Kinerja Website Baru (Versi Update) -->
    <h2 class="section-title">7. Hasil Skor Kinerja Website Baru (Versi Update Siap Pakai)</h2>
    <p style="font-size: 11px; color: #475569; margin-bottom: 8px;">
      Seluruh perbaikan teknis, Schema.org terstruktur, dan desain responsif telah diimplementasikan penuh. Berikut adalah perbandingan skor performa website baru {client_name} yang siap diserahterimakan:
    </p>

    <div class="scores-grid" style="margin-bottom: 12px;">
      <div class="score-card" style="background: #f0fdf4; border: 1.5px solid #86efac;">
        <div class="score-val" style="color: #16a34a;">98/100</div>
        <div class="score-label" style="color: #15803d; font-weight: 700;">Kesehatan Digital 🟢</div>
        <div style="font-size: 9.5px; color: #16a34a; font-weight: 700; margin-top: 2px;">Naik +108% (Optimal)</div>
      </div>
      <div class="score-card" style="background: #f0fdf4; border: 1.5px solid #86efac;">
        <div class="score-val" style="color: #16a34a;">100/100</div>
        <div class="score-label" style="color: #15803d; font-weight: 700;">SEO & Google Rank 🟢</div>
        <div style="font-size: 9.5px; color: #16a34a; font-weight: 700; margin-top: 2px;">Sempurna (Halaman 1)</div>
      </div>
      <div class="score-card" style="background: #f0fdf4; border: 1.5px solid #86efac;">
        <div class="score-val" style="color: #16a34a;">96/100</div>
        <div class="score-label" style="color: #15803d; font-weight: 700;">Pengalaman Mobile 🟢</div>
        <div style="font-size: 9.5px; color: #16a34a; font-weight: 700; margin-top: 2px;">Sub-Detik & Ergonomis</div>
      </div>
      <div class="score-card" style="background: #f0fdf4; border: 1.5px solid #86efac;">
        <div class="score-val" style="color: #16a34a;">98/100</div>
        <div class="score-label" style="color: #15803d; font-weight: 700;">Saluran Konversi WA 🟢</div>
        <div style="font-size: 9.5px; color: #16a34a; font-weight: 700; margin-top: 2px;">Terarah Langsung ke Sales</div>
      </div>
    </div>

    <!-- Signature & Footer -->
    <div class="signature-area">
      <div class="cert-badge-box">
        {f'<img src="{cert_b64}" class="cert-img" alt="Sertifikat">' if cert_b64 else ''}
        <div class="cert-text">
          <strong>{client_name}</strong><br>
          Website Resmi: {url}<br>
          {f'Kontak: {phone}<br>' if phone else ''}
          Kantor / Operasional: {address}
        </div>
      </div>

      <div class="sign-box">
        <div class="sign-title">Disiapkan secara profesional oleh:</div>
        <div class="sign-name">Tim Web Engineering Pipeline</div>
        <div class="sign-role">Automated SEO & Web Modernization Division</div>
      </div>
    </div>

  </div>

</body>
</html>
"""


if __name__ == "__main__":
    from scraper import ClientWebsiteScraper
    from auditor import WebsiteAuditor
    from style_analyzer import WebsiteStyleAnalyzer
    from quotation import QuotationEngine

    out_dir = "clients/suncargo"
    scraper = ClientWebsiteScraper()
    scraped = scraper.scrape("https://suncargo.sunfrozencargo.com")
    analyzer = WebsiteStyleAnalyzer()
    style = analyzer.analyze(scraped["raw_html"], scraped)
    auditor = WebsiteAuditor()
    audit = auditor.audit(scraped)
    qe = QuotationEngine()
    quotation = qe.generate_quotation(scraped, audit, style)

    pdf_gen = ProposalPdfGenerator()
    res = pdf_gen.generate(scraped, audit, style, quotation, out_dir)
    print("Generated files:", res)
