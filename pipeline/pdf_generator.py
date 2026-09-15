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
import urllib.parse
import urllib.request
import subprocess
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pipeline.researcher.business_researcher import BusinessResearcher
from pipeline.logging_config import get_logger
from pipeline.templates.renderer import render_template

logger = get_logger("pdf_generator")


class ProposalPdfGenerator:
    def __init__(self):
        self.edge_paths = [
            # Windows
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            # Linux / Unix
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/microsoft-edge",
            "/snap/bin/chromium",
            # macOS
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]

    def _find_browser_executable(self) -> str:
        for p in self.edge_paths:
            if os.path.exists(p):
                return p
        # Try system PATH
        for binary in ["google-chrome", "chrome", "msedge", "chromium", "chromium-browser"]:
            found = shutil.which(binary)
            if found:
                return found
        return ""

    def _convert_html_to_pdf(self, html_path: str, pdf_path: str) -> bool:
        """
        Converts an HTML file to a professional PDF.
        Priority:
          1. Playwright Python API (channels: 'msedge', 'chrome', default chromium)
          2. Headless Chrome/Edge subprocess via _find_browser_executable()
        """
        abs_html = os.path.abspath(html_path).replace("\\", "/")
        abs_pdf = os.path.abspath(pdf_path)

        if os.path.exists(abs_pdf):
            try:
                os.remove(abs_pdf)
            except Exception:
                pass

        # Strategy 1: Playwright Python API
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                for ch in ["msedge", "chrome", None]:
                    try:
                        launch_kwargs = {"headless": True}
                        if ch:
                            launch_kwargs["channel"] = ch
                        browser = p.chromium.launch(**launch_kwargs)
                        page = browser.new_page()
                        page.goto(f"file:///{abs_html}", wait_until="networkidle", timeout=30000)
                        page.pdf(
                            path=abs_pdf,
                            format="A4",
                            print_background=True,
                            prefer_css_page_size=True,
                            margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"}
                        )
                        browser.close()
                        if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                            logger.info(f"PDF rendered via Playwright (channel: {ch})")
                            return True
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"Playwright PDF attempt skipped or failed: {e}")

        # Strategy 2: Subprocess with detected browser executable
        browser_exe = self._find_browser_executable()
        if browser_exe:
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
                if os.path.exists(abs_pdf) and os.path.getsize(abs_pdf) > 0:
                    logger.info(f"PDF rendered via browser subprocess: {browser_exe}")
                    return True
                else:
                    logger.warning(f"Subprocess PDF output missing: {res.stderr}")
            except Exception as e:
                logger.error(f"Subprocess PDF generation error: {e}")

        return False

    def _get_base64_image(self, file_path: str) -> str:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 300:
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

    def generate(
        self,
        scraped: Dict[str, Any],
        audit: Any = None,
        style: Any = None,
        quotation: Any = None,
        output_dir: Any = None,
        vercel_url: str = "",
        client_dir: Any = None,
        partner_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Renders executive HTML proposal and converts it to a professional multi-page PDF.
        Supports both full pipeline 5-tuple signature and streamlined lead/client_dir signature.
        Supports whitelabel partner branding via partner_info dict.
        """
        effective_out_dir = output_dir or client_dir or "."
        p_info = partner_info or scraped.get("partner_info") or (quotation.get("partner_info") if quotation else None)
        if audit is None or style is None or quotation is None:
            return self.generate_track_b(scraped, output_dir=effective_out_dir, vercel_url=vercel_url, partner_info=p_info)

        html_content = self._render_html(scraped, audit, style, quotation, effective_out_dir, vercel_url=vercel_url, partner_info=p_info)
        html_path = os.path.join(effective_out_dir, "client_proposal.html")
        pdf_path = os.path.join(effective_out_dir, "client_proposal.pdf")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[+] Executive HTML Proposal saved -> {html_path}")

        # Convert to PDF via Playwright with subprocess fallback
        pdf_generated = self._convert_html_to_pdf(html_path, pdf_path)

        if pdf_generated:
            # Check page count
            with open(pdf_path, "rb") as pf:
                pdf_data = pf.read()
            page_matches = re.findall(rb'/Count\s+(\d+)', pdf_data)
            page_cnt = page_matches[0].decode() if page_matches else "multi"
            print(f"[+] Executive PDF Proposal generated -> {pdf_path} ({os.path.getsize(pdf_path):,} bytes, {page_cnt} pages)")

            # Clean up temporary HTML proposal to prevent duplicate client_proposal files
            try:
                if os.path.exists(html_path):
                    os.remove(html_path)
            except Exception:
                pass
        else:
            print("[!] Headless Edge/Chrome not found for direct PDF export. HTML version is available.")

        return {
            "html_path": html_path if not pdf_generated else "",
            "pdf_path": pdf_path if pdf_generated else ""
        }

    def generate_track_b(self, lead_or_scraped: Dict[str, Any], output_dir: str, vercel_url: str = "", partner_info: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Renders executive Track B proposal (Modernisasi & SEO Audit) from lead data or scraped data.
        Loads authentic on-disk scraped data, audit report, and style analysis when available.
        Supports whitelabel partner branding.
        """
        import json
        scraped = dict(lead_or_scraped)

        # 1. Load authentic scraped_data.json from output_dir if present
        scraped_path = os.path.join(output_dir, "scraped_data.json")
        if os.path.exists(scraped_path):
            try:
                with open(scraped_path, "r", encoding="utf-8") as f:
                    disk_scraped = json.load(f)
                for k, v in disk_scraped.items():
                    if k not in scraped or not scraped[k]:
                        scraped[k] = v
                    elif k in ["metadata", "headings", "layanan", "keunggulan", "visi_misi", "kontak", "social_media", "raw_html"]:
                        scraped[k] = v
            except Exception as e:
                logger.warning(f"Could not load scraped_data.json from {scraped_path}: {e}")

        b_name = scraped.get("brand_name") or scraped.get("business_name") or scraped.get("name") or "Perusahaan"
        dom = scraped.get("domain") or "domain.com"
        target_url = scraped.get("website_url") or scraped.get("url") or f"https://{dom}"

        from pipeline.auditor import WebsiteAuditor
        from pipeline.quotation import QuotationEngine

        # 2. Load audit from disk or generate from rich scraped data
        audit_path = os.path.join(output_dir, "audit_report.json")
        audit = scraped.get("audit")
        if not audit and os.path.exists(audit_path):
            try:
                with open(audit_path, "r", encoding="utf-8") as f:
                    audit = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load audit_report.json from {audit_path}: {e}")

        if not audit:
            if "headings" in scraped or "metadata" in scraped or "raw_html" in scraped:
                audit = WebsiteAuditor().audit(scraped)
            else:
                signals = scraped.get("outdated_signals", [])
                seo_issues = []
                for i, s in enumerate(signals):
                    s_clean = s.strip()
                    if s_clean:
                        seo_issues.append({
                            "severity": "CRITICAL" if i == 0 else "HIGH",
                            "type": "AUDIT DEFECT",
                            "message": s_clean
                        })
                if not seo_issues:
                    seo_issues = [
                        {"severity": "CRITICAL", "type": "SCHEMA ORG", "message": f"Tidak ditemukan Schema.org JSON-LD resmi untuk {b_name}."},
                        {"severity": "HIGH", "type": "MOBILE UX", "message": "Tata letak dan navigasi belum dioptimasi untuk layar smartphone modern."}
                    ]
                audit = {
                    "overall_score": 52,
                    "seo_score": 45,
                    "ux_score": 44,
                    "conversion_score": 75,
                    "seo_issues": seo_issues,
                    "keyword_targets": [
                        {"keyword": f"layanan {b_name.lower()}", "intent": "Komersial", "volume_est": "Tinggi", "potential_impact": "Mendatangkan inquiry langsung"},
                        {"keyword": f"kontak {b_name.lower()}", "intent": "Transaksi", "volume_est": "Menengah", "potential_impact": "Menarik calon klien siap beli"}
                    ]
                }

        # 3. Load style from disk or scraped
        style_path = os.path.join(output_dir, "style_analysis.json")
        style = scraped.get("style")
        if not style and os.path.exists(style_path):
            try:
                with open(style_path, "r", encoding="utf-8") as f:
                    style = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load style_analysis.json from {style_path}: {e}")

        if not style:
            style = {
                "palette": {"primary": "#0d4d87", "secondary": "#1e293b", "accent": "#0284c7"}
            }

        # 4. Generate or load quotation
        quotation = scraped.get("quotation")
        if not quotation:
            quotation = QuotationEngine().generate_quotation(
                {"brand_name": b_name, "domain": dom, "url": target_url},
                audit,
                style
            )

        html_content = self._render_html(scraped, audit, style, quotation, output_dir, vercel_url=vercel_url, partner_info=partner_info)
        html_path = os.path.join(output_dir, "client_proposal.html")
        pdf_path = os.path.join(output_dir, "client_proposal.pdf")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        pdf_generated = self._convert_html_to_pdf(html_path, pdf_path)
        if pdf_generated:
            print(f"[+] Executive PDF Proposal (Track B) generated -> {pdf_path}")
            try:
                if os.path.exists(html_path):
                    os.remove(html_path)
            except Exception:
                pass

        return {
            "html_path": html_path if not pdf_generated else "",
            "pdf_path": pdf_path if pdf_generated else ""
        }

    def _render_html(self, scraped: Dict[str, Any], audit: Dict[str, Any], style: Dict[str, Any], quotation: Dict[str, Any], output_dir: str, vercel_url: str = "", partner_info: Optional[Dict[str, str]] = None) -> str:
        client_name = quotation.get("client_name") or scraped.get("brand_name") or "Perusahaan"
        domain = quotation.get("domain") or scraped.get("domain") or "domain.com"
        url = quotation.get("url") or scraped.get("url") or f"https://{domain}"
        pkg = quotation.get("package", {})

        # Whitelabel Partner Branding
        p_info = partner_info or quotation.get("partner_info") or scraped.get("partner_info") or {}
        partner_brand = html.escape(p_info.get("name") or "Website Studio")
        partner_team = html.escape(p_info.get("team") or "Tim Desain & Web Development")
        partner_tagline = html.escape(p_info.get("tagline") or "Studio Desain & Pengembangan Web Modern")
        p_wa = p_info.get("whatsapp") or p_info.get("phone", "")
        p_url = p_info.get("url") or p_info.get("website", "")
        if p_wa:
            partner_contact = html.escape(f"Kontak/WhatsApp: {p_wa}")
        elif p_url:
            partner_contact = html.escape(f"Layanan Resmi: {p_url}")
        else:
            partner_contact = "Layanan Resmi: https://websiteupdater.vercel.app"
        
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

        # 1. Direct logo file lookup in assets
        for ext in ["png", "webp", "jpg", "jpeg", "svg"]:
            p = os.path.join(assets_dir, f"logo.{ext}")
            if os.path.exists(p):
                logo_b64 = self._get_base64_image(p)
                if logo_b64:
                    break

        # 2. General asset folder search
        if not logo_b64 and os.path.exists(assets_dir):
            for fname in os.listdir(assets_dir):
                fl = fname.lower()
                if any(ign in fl for ign in ["star", "f.svg", "rating", "wa.svg", "fb.svg", "ig.svg", "soc", "check"]):
                    continue
                if any(k in fl for k in ["logo", "brand", "company", "header", "navbar"]):
                    logo_b64 = self._get_base64_image(os.path.join(assets_dir, fname))
                    if logo_b64:
                        break

        # 3. Dynamic fetch from scraped logo_url, og:image, or favicon
        if not logo_b64:
            cand_url = scraped.get("logo_url") or scraped.get("metadata", {}).get("og_image") or scraped.get("metadata", {}).get("favicon")
            if cand_url and isinstance(cand_url, str):
                if cand_url.startswith("data:image"):
                    if "PHN2Zy" not in cand_url and len(cand_url) > 300:
                        logo_b64 = cand_url
                elif cand_url.startswith("http"):
                    try:
                        req = urllib.request.Request(cand_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                        with urllib.request.urlopen(req, timeout=8) as r:
                            c_bytes = r.read()
                            if len(c_bytes) > 500:
                                mime = "image/png"
                                if ".jpg" in cand_url or ".jpeg" in cand_url:
                                    mime = "image/jpeg"
                                elif ".webp" in cand_url:
                                    mime = "image/webp"
                                elif ".svg" in cand_url:
                                    mime = "image/svg+xml"
                                logo_b64 = f"data:{mime};base64,{base64.b64encode(c_bytes).decode('utf-8')}"
                    except Exception:
                        pass

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

        # Build SEO issues & UX defects with escaped text
        all_defects = []
        if "openseo_categories" in audit and isinstance(audit["openseo_categories"], dict):
            for cat_list in audit["openseo_categories"].values():
                if isinstance(cat_list, list):
                    all_defects.extend(cat_list)
        if not all_defects:
            all_defects = audit.get("seo_issues", []) + audit.get("ux_issues", [])
        if not all_defects:
            all_defects = audit.get("defects", [])

        # Deduplicate defects while preserving priority
        seen_msgs = set()
        deduped_defects = []
        for d in all_defects:
            msg = d.get("message", "").strip()
            if msg and msg not in seen_msgs:
                seen_msgs.add(msg)
                deduped_defects.append(d)

        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        deduped_defects.sort(key=lambda x: sev_order.get(x.get("severity", "MEDIUM"), 9))

        seo_cards = ""
        for issue in deduped_defects[:5]:
            sev = issue.get("severity", "MEDIUM")
            sev_class = "sev-critical" if sev == "CRITICAL" else ("sev-high" if sev == "HIGH" else "sev-med")
            raw_msg = issue.get("message", "")
            safe_msg = html.escape(raw_msg)
            safe_type = html.escape(issue.get("type", "").replace("_", " ").upper())
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
        if vercel_url:
            deliv_items += f"<li class='deliv-item'><span class='check-icon'>✓</span> <span><strong>Cloud Hosting Vercel Edge Aktif:</strong> Live demo berkecepatan tinggi telah online di <a href='{vercel_url}' style='color: #1268b3; font-weight: 700;' target='_blank'>{vercel_url}</a> siap migrasi ke domain resmi.</span></li>"

        # Build live demo interactive banner
        live_demo_html = ""
        if vercel_url:
            encoded_v = urllib.parse.quote_plus(vercel_url)
            live_demo_html = f"""
    <!-- Live Demo Preview Banner -->
    <div style="background: linear-gradient(135deg, #0b1329 0%, #1e293b 100%); border: 1.5px solid #38bdf8; border-radius: 8px; padding: 12px 16px; margin: 14px 0 16px 0; display: flex; justify-content: space-between; align-items: center; color: #ffffff;">
      <div style="max-width: 82%;">
        <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; padding: 2px 7px; border-radius: 4px; font-size: 9.5px; font-weight: 700; margin-bottom: 4px;">
          🌐 PROTOTIPE RESMI LIVE DI VERCEL CLOUD
        </div>
        <div style="font-size: 13px; font-weight: 800; color: #ffffff; margin-bottom: 2px;">Uji Coba Langsung Website Baru {html.escape(client_name)} di Smartphone Anda</div>
        <div style="font-size: 10px; color: #94a3b8; line-height: 1.4;">Website modern baru Anda telah selesai kami bangun dan online. Buka tautan ini untuk merasakan kecepatan sub-detik (&lt; 0.5s) dan kenyamanan pemesanan WhatsApp:</div>
        <div style="margin-top: 5px;">
          <a href="{vercel_url}" target="_blank" style="color: #38bdf8; font-weight: 700; font-size: 11.5px; text-decoration: underline;">{vercel_url} ↗</a>
        </div>
      </div>
      <div style="text-align: center; background: #ffffff; padding: 5px; border-radius: 6px; min-width: 68px;">
        <div style="font-size: 8px; font-weight: 800; color: #0f172a; margin-bottom: 2px;">SCAN HP</div>
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data={encoded_v}" width="54" height="54" alt="QR Demo" style="display: block; margin: 0 auto;">
      </div>
    </div>
"""

        monogram = client_name[:2].upper()
        raw_old_title = scraped.get("metadata", {}).get("title", "")
        old_title = html.escape(raw_old_title) if raw_old_title else "Belum Optimal / Missing"
        if raw_old_title and len(raw_old_title) > 15:
            new_title = html.escape(raw_old_title)
        else:
            new_title = html.escape(f"{client_name} | Solusi & Layanan Terpercaya di Indonesia")

        raw_old_desc = scraped.get("metadata", {}).get("meta_description", "")
        if raw_old_desc:
            clean_desc = raw_old_desc[:85] + ("..." if len(raw_old_desc) > 85 else "")
            old_meta_desc = html.escape(clean_desc)
        else:
            old_meta_desc = "Kosong / Tidak Terstandar (Google memotong cuplikan acak)"

        new_meta_desc = html.escape(f"155 karakter deskripsi terstruktur mencakup profil layanan, spesialisasi, dan kontak resmi {client_name}")

        h1_list = scraped.get("headings", {}).get("h1", [])
        h2_list = scraped.get("headings", {}).get("h2", [])
        if not h1_list:
            old_heading_desc = "Tidak ada tag H1 utama pada halaman web"
        elif len(h1_list) > 1:
            old_heading_desc = f"Ditemukan {len(h1_list)} tag H1 ganda (hierarki crawler belum tertata)"
        else:
            old_heading_desc = f"Struktur heading ({len(h1_list)} H1, {len(h2_list)} H2) belum difokuskan ke kata kunci"
        old_heading_desc = html.escape(old_heading_desc)

        old_schema_desc = "Nol (0% JSON-LD, tidak dikenal Google Knowledge Graph)"
        old_mobile_desc = "Tautan aset & tata letak belum optimal di smartphone"
        old_wa_desc = "Tautan kontak WhatsApp generik tanpa format pemesanan instan"
        old_speed_desc = "Beban aset belum teroptimasi pada koneksi seluler"

        pkg_name = html.escape(pkg.get("name", "Paket Transformasi Digital & Dominasi SEO"))
        pkg_summary = html.escape(pkg.get("summary", ""))
        price_flat_idr = pkg.get("price_flat_idr", "Rp 1.490.000")
        price_monthly_idr = pkg.get("price_monthly_idr", "Rp 99.000 / bln")
        price_idr = pkg.get("price_idr", "Rp 1.490.000")
        price_usd = price_idr

        return render_template(
            "pdf/proposal_track_b.html",
            client_name=client_name,
            domain=domain,
            url=url,
            tagline=html.escape(tagline),
            address=address,
            phone=phone,
            today_str=today_str,
            proposal_no=proposal_no,
            scores=scores,
            seo_score=seo_score,
            ux_score=ux_score,
            conv_score=conv_score,
            logo_b64=logo_b64,
            cert_b64=cert_b64,
            monogram=monogram,
            kw_rows=kw_rows,
            seo_cards=seo_cards,
            deliv_items=deliv_items,
            live_demo_html=live_demo_html,
            old_title=old_title,
            new_title=new_title,
            old_meta_desc=old_meta_desc,
            new_meta_desc=new_meta_desc,
            old_schema_desc=old_schema_desc,
            old_heading_desc=old_heading_desc,
            old_mobile_desc=old_mobile_desc,
            old_wa_desc=old_wa_desc,
            old_speed_desc=old_speed_desc,
            pkg_name=pkg_name,
            pkg_summary=pkg_summary,
            price_usd=price_usd,
            price_idr=price_idr,
            price_flat_idr=price_flat_idr,
            price_monthly_idr=price_monthly_idr,
            partner_brand=partner_brand,
            partner_team=partner_team,
            partner_tagline=partner_tagline,
            partner_contact=partner_contact,
        )

    def generate_track_a(self, business_data: Dict[str, Any], output_dir: str, vercel_url: str = "", partner_info: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Renders executive 4-page HTML and PDF proposal tailored specifically for
        Track A businesses (local businesses discovered on Google Maps that lack an official website).
        Supports whitelabel partner branding.
        """
        html_content = self._render_html_track_a(business_data, output_dir, vercel_url=vercel_url, partner_info=partner_info)
        html_path = os.path.join(output_dir, "client_proposal.html")
        pdf_path = os.path.join(output_dir, "client_proposal.pdf")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        pdf_generated = self._convert_html_to_pdf(html_path, pdf_path)
        if pdf_generated:
            print(f"[+] Executive PDF Proposal (Track A) generated -> {pdf_path} ({os.path.getsize(pdf_path):,} bytes, 4 pages)")

            # Clean up temporary HTML proposal to prevent duplicate client_proposal files
            try:
                if os.path.exists(html_path):
                    os.remove(html_path)
            except Exception:
                pass
        else:
            print("[!] PDF generation failed or browser not found. HTML version is available.")

        # Clean up any leftover md proposal file
        md_path = os.path.join(output_dir, "client_proposal.md")
        if os.path.exists(md_path):
            try:
                os.remove(md_path)
            except Exception:
                pass

        return {
            "html_path": html_path if not pdf_generated else "",
            "pdf_path": pdf_path if pdf_generated else ""
        }

    def _render_html_track_a(self, business_data: Dict[str, Any], output_dir: str, vercel_url: str = "", partner_info: Optional[Dict[str, str]] = None) -> str:
        biz_name = business_data.get("name") or business_data.get("business_name") or "Bisnis Klien"
        rating = business_data.get("rating") or "4.9"
        reviews = business_data.get("review_count") or 50
        phone = business_data.get("phone") or business_data.get("whatsapp") or ""
        cat = business_data.get("category") or ""
        address = business_data.get("address") or ""
        city_input = business_data.get("city") or ""

        # Whitelabel Partner Branding
        p_info = partner_info or business_data.get("partner_info") or {}
        partner_brand = html.escape(p_info.get("name") or "Website Studio")
        partner_team = html.escape(p_info.get("team") or "Tim Desain & Web Development")
        partner_tagline = html.escape(p_info.get("tagline") or "Studio Desain & Pengembangan Web Modern")
        p_wa = p_info.get("whatsapp") or p_info.get("phone", "")
        p_url = p_info.get("url") or p_info.get("website", "")
        if p_wa:
            partner_contact = html.escape(f"Kontak/WhatsApp: {p_wa}")
        elif p_url:
            partner_contact = html.escape(f"Layanan Resmi: {p_url}")
        else:
            partner_contact = "Layanan Resmi: https://websiteupdater.vercel.app"

        # Smart localized address discovery from generated site index.html if missing or generic
        site_html_path = os.path.join(output_dir, "site", "index.html")
        if os.path.exists(site_html_path) and (not address or "area operasional" in address.lower() or not city_input):
            try:
                with open(site_html_path, "r", encoding="utf-8") as f:
                    site_content = f.read()
                if not address or "area operasional" in address.lower():
                    m_addr = re.search(r'"streetAddress":\s*"([^"]+)"', site_content)
                    if m_addr:
                        address = m_addr.group(1).strip()
                    else:
                        m_span = re.search(r'(?:📍|<span class="top-icon">.*?</span>)\s*<span>([^<|]+)', site_content, re.DOTALL)
                        if m_span:
                            address = m_span.group(1).strip()
                if not city_input:
                    m_loc = re.search(r'"addressLocality":\s*"([^"]+)"', site_content)
                    if m_loc:
                        city_input = m_loc.group(1).strip()
            except Exception as e:
                logger.debug(f"Could not extract address from site HTML: {e}")

        today_str = datetime.now().strftime("%d %B %Y")
        safe_code = re.sub(r'[^A-Z0-9]', '', biz_name.upper())[:10] or "CLIENT"
        proposal_no = f"PROP-A-{safe_code}-TURNKEY"

        # Trade research & profiling
        researcher = BusinessResearcher()
        profile = researcher.research_business(
            business_name=biz_name,
            category=cat,
            address=address,
            phone=phone,
            rating=rating,
            review_count=reviews
        )
        trade_name = profile["trade_name"]
        headline = profile["headline"]
        city = city_input or profile["city"]
        if city.lower().startswith("kota "):
            city = city[5:].strip()

        # Clean display area for headline & cards (prevent awkward "Area Operasional Sekitar" repetitions)
        if city and not any(k in city.lower() for k in ["sekitarnya", "lokal", "operasional"]):
            display_area = f"{city} & Sekitarnya"
        elif "operasional" in city.lower():
            display_area = "Lokal & Sekitarnya"
            city = "Lokal"
        else:
            display_area = city or "Lokal & Sekitarnya"

        clean_location = address if (address and "area operasional" not in address.lower()) else display_area

        # Build 6 services PDF HTML
        services_pdf_html = ""
        for s in profile["services"][:6]:
            services_pdf_html += f"""
          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 7px 10px;">
            <div style="font-weight: 700; font-size: 10px; color: #0d4d87;">{s.get('icon', '⭐')} {html.escape(s['title'])}</div>
            <div style="font-size: 9px; color: #475569; margin-top: 2px; line-height: 1.35;">{html.escape(s['desc'][:115])}...</div>
          </div>"""

        encoded_v = urllib.parse.quote_plus(vercel_url) if vercel_url else ""
        live_demo_html = ""
        if vercel_url:
            live_demo_html = f"""
    <div style="background: linear-gradient(135deg, #0b1329 0%, #1e293b 100%); border: 1.5px solid #38bdf8; border-radius: 8px; padding: 14px 18px; margin: 16px 0; display: flex; justify-content: space-between; align-items: center; color: #ffffff;">
      <div style="max-width: 80%;">
        <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; padding: 3px 8px; border-radius: 4px; font-size: 9.5px; font-weight: 700; margin-bottom: 6px;">
          🌐 PROTOTIPE RESMI LIVE DI VERCEL CLOUD
        </div>
        <div style="font-size: 14px; font-weight: 800; color: #ffffff; margin-bottom: 3px;">Uji Coba Langsung Website Baru {html.escape(biz_name)} di Smartphone Anda</div>
        <div style="font-size: 10.5px; color: #94a3b8; line-height: 1.4;">Prototipe website resmi bisnis Anda telah kami bangun dan aktif di cloud global. Buka tautan ini untuk merasakan navigasi instan dan kenyamanan order via WhatsApp:</div>
        <div style="margin-top: 6px;">
          <a href="{vercel_url}" target="_blank" style="color: #38bdf8; font-weight: 700; font-size: 12px; text-decoration: underline;">{vercel_url} ↗</a>
        </div>
      </div>
      <div style="text-align: center; background: #ffffff; padding: 6px; border-radius: 6px; min-width: 72px;">
        <div style="font-size: 8px; font-weight: 800; color: #0f172a; margin-bottom: 2px;">SCAN HP</div>
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data={encoded_v}" width="56" height="56" alt="QR Demo" style="display: block; margin: 0 auto;">
      </div>
    </div>
"""

        monogram = biz_name[:2].upper()
        safe_domain_slug = re.sub(r'[^a-zA-Z0-9]', '', biz_name).lower()

        return render_template(
            "pdf/proposal_track_a.html",
            biz_name=html.escape(biz_name),
            rating=rating,
            reviews=reviews,
            phone=phone or "Tersedia",
            cat=cat,
            address=html.escape(clean_location),
            today_str=today_str,
            proposal_no=proposal_no,
            trade_name=html.escape(trade_name),
            headline=html.escape(headline),
            city=html.escape(city),
            display_area=html.escape(display_area),
            services_pdf_html=services_pdf_html,
            live_demo_html=live_demo_html,
            monogram=monogram,
            safe_domain_slug=safe_domain_slug,
            vercel_url=vercel_url,
            price_flat_idr="Rp 1.490.000",
            price_monthly_idr="Rp 99.000 / bln",
            price_idr="Rp 1.490.000",
            partner_brand=partner_brand,
            partner_team=partner_team,
            partner_tagline=partner_tagline,
            partner_contact=partner_contact,
        )



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
