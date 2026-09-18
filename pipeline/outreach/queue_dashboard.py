"""
Whitespace Minimalist HTML Queue Dashboard Generator.
Renders interactive administrative review dashboard for Track A and Track B SME leads.
"""

import os
import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional
from pipeline.payment.payment_gateway import PaymentGateway
from pipeline.deployer.vercel_deployer import VercelDeployer
from pipeline.outreach.message_formatter import generate_outreach_message

QUEUE_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", "outreach_queue.html"))

def generate_html_queue_dashboard(leads: List[Dict[str, Any]], output_path: str = QUEUE_HTML_PATH) -> str:
    """
    Generates a clean, classic whitespace minimalist dashboard with distinct
    [Jalur A] vs [Jalur B] badges and basic Green (Centang) / Red (Discard) buttons.
    """
    cards_html = []
    if isinstance(leads, dict):
        leads_list = list(leads.values())
    else:
        leads_list = list(leads)

    # Sort descending by created_at: newest leads at the top, older leads at the bottom
    active_leads = sorted(
        [l for l in leads_list if l.get("status") != "discarded"],
        key=lambda x: (x.get("created_at") or x.get("updated_at") or ""),
        reverse=True
    )

    price_label = "Rp 1.490.000 (Flat All-In Terima Beres)"

    for lead in active_leads:
        b_name = lead.get("business_name", "Bisnis Indonesia")
        domain = lead.get("domain", "")
        wa = lead.get("whatsapp", "")
        email = lead.get("email", "")
        pdf_path = lead.get("proposal_pdf", "")
        signals = lead.get("outdated_signals", [])
        status = lead.get("status", "discovered")
        track = lead.get("track", "track_b_modernize")
        vercel_url = lead.get("vercel_url", "")
        payment_status = lead.get("payment_status", "unpaid")
        client_slug = domain.replace(".", "_").replace("-", "_")

        pdf_rel = ""
        if pdf_path:
            pdf_rel = os.path.relpath(pdf_path, os.path.dirname(output_path)).replace("\\", "/")

        # Status Badge (Google Material Design Chips)
        status_badge = {
            "discovered": '<span class="badge">Antrean</span>',
            "ready_for_permission": '<span class="badge" style="background:#fef7e0; color:#b06000; border-color:#feefc3;">Siap Izin Tahap 1</span>',
            "proposal_ready": '<span class="badge">Siap Kirim</span>',
            "sent_whatsapp": '<span class="badge badge-sent">Izin Tahap 1 Terkirim</span>',
            "sent_step1": '<span class="badge badge-sent">Izin Tahap 1 Terkirim</span>',
            "sent_step2": '<span class="badge badge-demo">Proposal & Demo Terkirim 📄</span>',
            "sent_email": '<span class="badge badge-sent">Email Terkirim</span>',
            "fallback_email": '<span class="badge" style="background:#e6f4ea; color:#137333; border-color:#ceead6;">✉️ Fallback Email</span>',
            "sent_all": '<span class="badge badge-sent">Terkirim (WA+Email)</span>',
            "replied": '<span class="badge badge-replied">Balasan Masuk 💬</span>',
            "demo_sent": '<span class="badge badge-demo">Demo Vercel 🌐</span>',
            "options_sent": '<span class="badge badge-demo">Opsi Dikirim 📋</span>',
            "paid": '<span class="badge badge-paid">LUNAS ($100) ✅</span>',
            "dry_run": '<span class="badge">Siap Di-review</span>',
            "wa_cooldown": '<span class="badge" style="background:#fef7e0; color:#b06000; border-color:#feefc3;">⚠️ WA Cooldown Meta</span>',
            "invalid_phone": '<span class="badge" style="background:#fce8e6; color:#c5221f; border-color:#fad2cf;">Bukan Nomor WA ✕</span>',
            "failed": '<span class="badge" style="background:#fce8e6; color:#c5221f; border-color:#fad2cf;">Gagal / Perlu Cek</span>'
        }.get(status, f'<span class="badge">{status}</span>')

        # Track Badge
        track_badge = (
            '<span class="badge-track badge-track-a">Jalur A: Web Baru</span>'
            if track == "track_a_new_web"
            else '<span class="badge-track badge-track-b">Jalur B: Modernisasi</span>'
        )

        signals_li = "".join([f"<li>{s}</li>" for s in signals[:2]]) or "<li>Evaluasi teknis visibilitas Google & Kenyamanan Mobile</li>"

        is_step1_sent = status in ["sent_whatsapp", "sent_step1"]
        is_step2_sent = status in ["sent_step2", "sent_all", "demo_sent", "options_sent", "paid"]
        is_replied = status == "replied"
        is_invalid = status == "invalid_phone"
        is_sent = is_step2_sent

        if is_invalid:
            approve_btn_text = "Nomor Bukan WA"
            approve_btn_class = "btn btn-approve btn-disabled"
            approve_btn_disabled = "disabled"
            approve_step = ""
        elif is_step2_sent:
            approve_btn_text = "Proposal & Demo Tahap 2 Sudah Terkirim"
            approve_btn_class = "btn btn-approve btn-disabled"
            approve_btn_disabled = "disabled"
            approve_step = ""
        elif is_replied:
            approve_btn_text = "💬 Klien Membalas! Kirim Proposal & Demo (Tahap 2)"
            approve_btn_class = "btn btn-approve"
            approve_btn_disabled = ""
            approve_step = "step_2_delivery"
        elif is_step1_sent:
            approve_btn_text = "✓ Kirim Proposal & Demo (Tahap 2) via Bot"
            approve_btn_class = "btn btn-approve"
            approve_btn_disabled = ""
            approve_step = "step_2_delivery"
        else:
            approve_btn_text = "✓ Centang (Kirim WA Izin Tahap 1)"
            approve_btn_class = "btn btn-approve"
            approve_btn_disabled = ""
            approve_step = "step_1_permission"

        # Determine verified Vercel URL (NEVER fabricate a phantom URL if not deployed yet!)
        live_vercel_url = (vercel_url or "").strip()

        # Domain & Vercel links in card header
        if track == "track_a_new_web":
            if live_vercel_url:
                domain_display_html = (
                    f'<div style="margin-top: 3px;">'
                    f'<a href="{live_vercel_url}" target="_blank" class="biz-domain" style="color:var(--google-blue); font-weight:600;">'
                    f'🌐 Live Vercel: {live_vercel_url} ↗</a>'
                    f'</div>'
                )
            else:
                domain_display_html = (
                    f'<div style="margin-top: 3px;">'
                    f'<span class="biz-domain" style="color:var(--text-secondary); font-size:12px;">'
                    f'🌐 Vercel: <span style="color:#d93025; font-weight:600;">Belum Deploy</span> (JIT Prototype Siap)</span>'
                    f'</div>'
                )
        else:
            if live_vercel_url:
                domain_display_html = (
                    f'<div style="display:flex; flex-direction:column; gap:2px; margin-top: 3px;">'
                    f'<a href="https://{domain}" target="_blank" class="biz-domain" style="color:var(--text-secondary); font-size:12px;">'
                    f'Web Asli: https://{domain} ↗</a>'
                    f'<a href="{live_vercel_url}" target="_blank" class="biz-domain" style="color:var(--google-blue); font-weight:600;">'
                    f'🌐 Live Vercel: {live_vercel_url} ↗</a>'
                    f'</div>'
                )
            else:
                domain_display_html = (
                    f'<div style="display:flex; flex-direction:column; gap:2px; margin-top: 3px;">'
                    f'<a href="https://{domain}" target="_blank" class="biz-domain" style="color:var(--text-secondary); font-size:12px;">'
                    f'Web Asli: https://{domain} ↗</a>'
                    f'<span class="biz-domain" style="color:var(--text-secondary); font-size:12px;">'
                    f'🌐 Vercel: <span style="color:#d93025; font-weight:600;">Belum Deploy</span> (JIT Prototype Siap)</span>'
                    f'</div>'
                )

        # Secondary Action Buttons:
        sub_actions = []
        if live_vercel_url:
            sub_actions.append(f'<a href="{live_vercel_url}" target="_blank" class="btn-sub" style="font-weight:600; color:var(--google-blue);">🌐 Live Vercel ↗</a>')
        else:
            sub_actions.append(f'<button onclick="deployVercel(\'{domain}\', this)" class="btn-sub" style="font-weight:600; color:#e37400; background:#fef7e0; border-color:#fce8e6;">🚀 Deploy ke Vercel</button>')
        sub_actions.append(f'<a href="/api/download-package?client={domain}" target="_blank" class="btn-sub">📦 Download ZIP Paket Klien</a>')
        sub_actions.append(f'<button onclick="createInvoice(\'{domain}\', this)" class="btn-sub">💳 Link Bayar {price_label}</button>')
        
        if wa:
            clean_wa = re.sub(r"[^\d]", "", wa)
            msg_step1 = generate_outreach_message(b_name, domain, signals, track=track, rating_text=lead.get("gmaps_rating", ""), step="step_1_permission")
            encoded_wa_step1 = urllib.parse.quote_plus(msg_step1)
            sub_actions.append(f'<a href="https://wa.me/{clean_wa}?text={encoded_wa_step1}" target="_blank" class="btn-sub" style="font-weight:600; color:#188038; background:#e6f4ea; border-color:#ceead6;">📱 Chat Izin Tahap 1 ↗</a>')

            msg_step2 = generate_outreach_message(b_name, domain, signals, track=track, rating_text=lead.get("gmaps_rating", ""), step="step_2_delivery")
            encoded_wa_step2 = urllib.parse.quote_plus(msg_step2)
            sub_actions.append(f'<a href="https://wa.me/{clean_wa}?text={encoded_wa_step2}" target="_blank" class="btn-sub" style="font-weight:600; color:#1a73e8; background:#e8f0fe; border-color:#d2e3fc;">📄 Chat Demo & PDF (Tahap 2) ↗</a>')

            if not is_sent:
                sub_actions.append(f'<button onclick="markSent(\'{domain}\', this)" class="btn-sub" style="font-weight:600; color:var(--google-blue);">✓ Tandai Terkirim Manual</button>')

        sub_actions_html = "".join(sub_actions)

        # Official PDF Proposal link only (0 HTML/MD duplicate links)
        pdf_link_html = (
            f'<a href="{pdf_rel}" target="_blank" class="pdf-preview-link">📄 Lihat Dokumen Proposal Resmi (client_proposal.pdf) ↗</a>'
            if pdf_rel
            else f'<a href="{client_slug}/client_proposal.pdf" target="_blank" class="pdf-preview-link">📄 client_proposal.pdf ↗</a>'
        )

        cards_html.append(f"""
        <div class="card" id="card-{domain.replace('.', '_')}" data-search="{b_name.lower()} {domain.lower()}" data-track="{track}" data-status="{status}">
          <div class="card-head">
            <div>
              <div style="margin-bottom: 6px;">{track_badge}</div>
              <h3 class="biz-title">{b_name}</h3>
              {domain_display_html}
            </div>
            <div id="badge-{domain.replace('.', '_')}">{status_badge}</div>
          </div>
          <div class="card-body">
            <div class="contact-row">
              <div>WhatsApp: <strong>{wa or '<em style="color:#80868b">Tidak ditemukan</em>'}</strong></div>
              <div>Email: <strong>{email or '<em style="color:#80868b">Tidak ditemukan</em>'}</strong></div>
            </div>
            <div class="audit-summary" style="margin-top:10px;">
              <strong>Poin Strategis:</strong>
              <ul>{signals_li}</ul>
            </div>
          </div>
          <div class="card-actions">
            <button onclick="approveLead('{domain}', this, '{approve_step}')" class="{approve_btn_class}" {approve_btn_disabled}>
              {approve_btn_text}
            </button>
            {f'<button onclick="discardLead(\'{domain}\', this)" class="btn btn-discard">✕ Discard</button>' if not is_sent else ''}
          </div>
          <div class="sub-actions-row">
            {sub_actions_html}
          </div>
          <div class="card-footer">
            {pdf_link_html}
          </div>
        </div>
        """)

    track_a_count = len([l for l in active_leads if l.get('track') == 'track_a_new_web'])
    track_b_count = len([l for l in active_leads if l.get('track') != 'track_a_new_web'])
    replied_count = len([l for l in active_leads if l.get('status') in ['replied', 'demo_sent', 'options_sent']])
    email_count = len([l for l in active_leads if l.get('status') == 'fallback_email'])
    paid_count = len([l for l in active_leads if l.get('payment_status') == 'paid' or l.get('status') == 'paid'])

    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = "127.0.0.1"

    full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Antrean Prospek Outreach - Website Updater Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
--bg-main: #ffffff;
--bg-surface: #f8f9fa;
--border-color: #dadce0;
--border-light: #dfe1e5;
--text-primary: #202124;
--text-secondary: #5f6368;
--google-blue: #1a73e8;
--google-blue-hover: #174ea6;
--google-blue-light: #e8f0fe;
--google-red: #d93025;
--google-green: #188038;
--shadow-search: 0 1px 6px rgba(32,33,36,.28);
--shadow-card: 0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15);
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Plus Jakarta Sans", sans-serif;
    font-variant-ligatures: none;
    text-rendering: optimizeLegibility;
    background-color: var(--bg-surface);
    color: var(--text-primary);
    padding: 24px 20px 60px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{ max-width: 1080px; margin: 0 auto; }}

  /* GOOGLE HEADER & CENTER LOGO */
  .google-top-bar {{
display: flex; justify-content: space-between; align-items: center;
background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px;
padding: 14px 24px; margin-bottom: 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  }}
  .brand-group {{ display: flex; align-items: center; gap: 10px; }}
  .dots {{ display: flex; gap: 3px; }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
  .dot-b {{ background: #4285f4; }}
  .dot-r {{ background: #ea4335; }}
  .dot-y {{ background: #fbbc05; }}
  .dot-g {{ background: #34a853; }}
  .brand-title {{ font-size: 17px; font-weight: 700; color: var(--text-primary); }}
  .brand-sub {{ font-size: 13px; color: var(--text-secondary); margin-left: 6px; }}

  /* ICONIC ROUNDED SEARCH BAR */
  .search-wrapper {{
max-width: 680px; margin: 0 auto 24px; position: relative;
  }}
  .search-box {{
width: 100%; height: 48px; background: #ffffff;
border: 1px solid var(--border-light); border-radius: 24px;
padding: 0 20px; display: flex; align-items: center; gap: 12px;
box-shadow: none; transition: all 0.2s ease;
  }}
  .search-box:focus-within, .search-box:hover {{
box-shadow: var(--shadow-search); border-color: transparent;
  }}
  .search-icon {{ color: #9aa0a6; width: 20px; height: 20px; flex-shrink: 0; }}
  .search-input {{
flex: 1; border: none; outline: none; font-size: 15px;
color: var(--text-primary); font-family: inherit;
  }}
  .search-input::placeholder {{ color: #80868b; }}

  /* NOTICE BANNER */
  .notice-banner {{
background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px;
padding: 12px 18px; font-size: 13px; color: var(--text-secondary); margin-bottom: 20px;
display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
  }}
  .notice-banner strong {{ color: var(--text-primary); }}

  /* STATS CHIPS */
  .stats-bar {{
    display: flex; gap: 10px; margin-bottom: 24px; flex-wrap: wrap;
  }}
  .stat-chip {{
    background: #ffffff; border: 1px solid var(--border-color);
    padding: 8px 16px; border-radius: 20px; font-size: 13px; color: var(--text-secondary);
    display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;
    transition: all 0.15s ease;
  }}
  .stat-chip:hover {{
    border-color: #9aa0a6; box-shadow: 0 1px 4px rgba(0,0,0,0.08); transform: translateY(-1px);
  }}
  .stat-chip.active-filter {{
    background: var(--google-blue-light); border-color: #aecbfa; font-weight: 700; color: #174ea6;
  }}
  .stat-chip strong {{ font-size: 14px; color: inherit; }}

  .empty-state-box {{
    grid-column: 1 / -1; background: #ffffff; border: 1px dashed var(--border-color);
    border-radius: 12px; padding: 40px 24px; text-align: center; margin: 10px 0;
  }}

  /* GLOBAL TOUCH & TAP OPTIMIZATION */
  button, .btn, .btn-sub, select, a {{
touch-action: manipulation;
-webkit-tap-highlight-color: transparent;
  }}

  /* LEAD GRID */
  .lead-grid {{
display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 20px;
  }}
  @media (max-width: 768px) {{
body {{ padding: 12px 10px 48px; }}
.container {{ width: 100%; max-width: 100%; }}
.google-top-bar {{
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
  padding: 12px 14px;
}}
.google-top-bar > div:last-child {{
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}}
.google-top-bar select, .google-top-bar button, .google-top-bar a {{
  width: 100%;
  height: 44px !important;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 14px;
}}
.search-box {{ height: 44px; padding: 0 16px; }}
.stats-bar {{ justify-content: flex-start; gap: 6px; }}
.stat-chip {{ padding: 6px 12px; font-size: 12px; }}
.lead-grid {{ grid-template-columns: 1fr; gap: 16px; }}
.card {{ padding: 16px 14px; }}
.card-actions {{ flex-direction: column; gap: 8px; }}
.card-actions .btn {{ width: 100%; min-height: 44px; font-size: 14px; }}
.sub-actions-row {{ flex-direction: column; gap: 8px; }}
.sub-actions-row .btn-sub {{ width: 100%; min-height: 42px; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 13px; }}
  }}
  
  /* CARDS: MATERIAL DESIGN */
  .card {{
background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px;
padding: 20px; display: flex; flex-direction: column; justify-content: space-between;
transition: box-shadow 0.2s, transform 0.15s;
  }}
  .card:hover {{
box-shadow: 0 4px 12px rgba(60,64,67,.15);
  }}
  .card-head {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }}
  .biz-title {{ font-size: 17px; font-weight: 700; color: var(--text-primary); }}
  .biz-domain {{ font-size: 13px; color: var(--google-blue); text-decoration: none; display: inline-block; margin-top: 2px; }}
  .biz-domain:hover {{ text-decoration: underline; }}

  /* MATERIAL CHIPS & BADGES */
  .badge {{
display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;
background: #f1f3f4; color: var(--text-secondary); border: 1px solid var(--border-light);
  }}
  .badge-sent {{ background: var(--google-blue-light); color: var(--google-blue); border-color: #c2e7ff; }}
  .badge-replied {{ background: #fce8e6; color: #c5221f; border-color: #fad2cf; }}
  .badge-demo {{ background: #f3e8fd; color: #7627bb; border-color: #e9d5ff; }}
  .badge-paid {{ background: #e6f4ea; color: #137333; border-color: #ceead6; }}

  .badge-track {{
display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;
  }}
  .badge-track-a {{
background: #e8f0fe; color: #1967d2; border: 1px solid #c2e7ff;
  }}
  .badge-track-b {{
background: #fef7e0; color: #b06000; border: 1px solid #feefc3;
  }}
  
  .card-body {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 16px; }}
  .contact-row {{
background: var(--bg-surface); padding: 10px 14px; border-radius: 6px;
margin-bottom: 10px; border: 1px solid #f1f3f4; display: flex; flex-direction: column; gap: 4px;
  }}
  .contact-row strong {{ color: var(--text-primary); }}
  .audit-summary {{ font-size: 12px; }}
  .audit-summary ul {{ padding-left: 18px; margin-top: 4px; color: var(--text-secondary); }}

  /* GOOGLE MATERIAL BUTTONS */
  .card-actions {{ display: flex; gap: 8px; margin-top: 6px; }}
  .btn {{
display: inline-flex; align-items: center; justify-content: center;
padding: 10px 16px; border-radius: 4px; font-size: 13px; font-weight: 600;
cursor: pointer; border: none; transition: background 0.15s, box-shadow 0.15s;
font-family: inherit;
  }}
  .btn-approve {{ background: var(--google-blue); color: #ffffff; flex: 2; }}
  .btn-approve:hover:not(:disabled) {{ background: var(--google-blue-hover); box-shadow: 0 1px 3px rgba(66,133,244,.3); }}
  .btn-discard {{ background: #ffffff; color: var(--google-red); border: 1px solid #fad2cf; flex: 1; }}
  .btn-discard:hover {{ background: #fce8e6; }}
  .btn-disabled {{
background: #f1f3f4 !important; color: #80868b !important; border: 1px solid var(--border-color) !important; cursor: default;
  }}
  
  /* SUB ACTIONS ROW */
  .sub-actions-row {{
display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap;
  }}
  .btn-sub {{
background: #ffffff; border: 1px solid var(--border-color); color: var(--text-primary);
padding: 6px 12px; border-radius: 4px; font-size: 12px; text-decoration: none;
cursor: pointer; font-weight: 500; transition: background 0.15s, border-color 0.15s;
  }}
  .btn-sub:hover {{ background: #f8f9fa; border-color: #c4c7c5; color: var(--text-primary); }}

  .card-footer {{
margin-top: 12px; padding-top: 8px; border-top: 1px solid #f1f3f4; text-align: center;
  }}
  .pdf-preview-link {{
font-size: 12px; color: var(--google-blue); text-decoration: none;
  }}
  .pdf-preview-link:hover {{ text-decoration: underline; }}

  #toast {{
position: fixed; bottom: 24px; right: 24px; background: #323232; color: #ffffff;
padding: 12px 20px; border-radius: 4px; box-shadow: 0 3px 8px rgba(0,0,0,.24);
display: none; font-size: 13px; z-index: 9999;
  }}
</style>
</head>
<body>
<div class="container">
  <!-- Google Style Top Bar -->
  <div class="google-top-bar">
    <div class="brand-group">
      <div class="dots">
        <span class="dot dot-b"></span>
        <span class="dot dot-r"></span>
        <span class="dot dot-y"></span>
        <span class="dot dot-g"></span>
      </div>
      <div>
        <span class="brand-title">Website Updater</span>
        <span class="brand-sub">Dasbor Antrean Prospek Indonesia ($100 Turn-Key)</span>
      </div>
    </div>
    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
      <select id="target-scope" class="btn-sub" style="font-weight:600; cursor:pointer; padding:6px 10px; height:36px;">
        <option value="auto">🎯 Seluruh Indonesia (Rotasi Multi-Sektor)</option>
        <option value="b2b_distributor">🏭 B2B Distributor & Manufaktur</option>
        <option value="ekspedisi_spesialis">🚛 Ekspedisi & Kargo Logistik</option>
        <option value="kontraktor_komersial">🏗️ Kontraktor Komersial & HVAC</option>
        <option value="klinik_spesialis">🏥 Klinik & Laboratorium Spesialis</option>
        <option value="layanan_profesional">💼 Layanan Korporat & Konsultan</option>
        <option value="jabodetabek">📍 Jabodetabek (Jakarta, Cikarang, Tangerang)</option>
        <option value="surabaya_jatim">📍 Jawa Timur (Surabaya, Sidoarjo, Gresik)</option>
        <option value="kalimantan">📍 Hub Kalimantan (Balikpapan, Samarinda)</option>
        <option value="sumatera">📍 Sumatera (Medan, Batam, Pekanbaru)</option>
      </select>
      <button id="btn-hunt-outdated" onclick="huntOutdated(this)" class="btn-sub" style="background:#b06000; color:#ffffff; font-weight:700; border-color:#b06000; height:36px;">
        ⚡ Buru Web B2B (Jalur B)
      </button>
      <button id="btn-scan-niche" onclick="scanNiche(this)" class="btn-sub" style="background:var(--google-blue); color:#ffffff; font-weight:700; border-color:var(--google-blue); height:36px;">
        🔍 Scan Maps (Jalur A)
      </button>
      <button onclick="checkReplies()" class="btn-sub" style="height:36px;">
        🔄 Cek Balasan WA
      </button>
      <a href="https://websiteupdater.vercel.app" target="_blank" class="btn-sub" style="color:var(--google-blue); font-weight:600; height:36px; display:inline-flex; align-items:center;">
        🌐 Agency ↗
      </a>
    </div>
  </div>

  <!-- Iconic Rounded Google Search Bar for Real-Time Filtering -->
  <div class="search-wrapper">
    <div class="search-box">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input type="text" id="lead-filter-input" class="search-input" placeholder="Cari nama bisnis, domain, atau status prospek..." oninput="filterLeads(this.value)">
    </div>
  </div>

  <!-- Notice Banner -->
  <div class="notice-banner">
    <div>
      Tarif resmi flat: <strong>{price_label}</strong>. Klik <strong>Centang</strong> untuk kirim otomatis, atau klik <strong>📱 Buka Chat di HP / Web</strong> untuk kirim via WhatsApp HP tanpa pembatasan.
    </div>
    <div style="display:flex; gap:12px; font-size:12px; color:var(--text-secondary); align-items:center;">
      <span>💻 Laptop: <strong>http://localhost:8080</strong></span>
      <span>📱 Akses HP: <strong style="color:var(--google-blue);">http://{lan_ip}:8080</strong></span>
    </div>
  </div>

  <!-- Stats Chips Interaktif -->
  <div class="stats-bar">
    <div class="stat-chip active-filter" onclick="filterByTag('all', this)" id="chip-all">
      Total Antrean: <strong id="stat-total-cnt">{len(active_leads)}</strong>
    </div>
    <div class="stat-chip" style="color:#1967d2;" onclick="filterByTag('track_a', this)" id="chip-track-a">
      Jalur A (Web Baru): <strong>{track_a_count}</strong>
    </div>
    <div class="stat-chip" style="color:#b06000;" onclick="filterByTag('track_b', this)" id="chip-track-b">
      Jalur B (Modernisasi): <strong>{track_b_count}</strong>
    </div>
    <div class="stat-chip" style="color:#137333;" onclick="filterByTag('email', this)" id="chip-email">
      ✉️ Fallback Email: <strong>{email_count}</strong>
    </div>
    <div class="stat-chip" style="color:#c5221f;" onclick="filterByTag('replied', this)" id="chip-replied">
      Balasan Masuk: <strong>{replied_count}</strong>
    </div>
    <div class="stat-chip" style="color:#137333;" onclick="filterByTag('paid', this)" id="chip-paid">
      Lunas ($100): <strong>{paid_count}</strong>
    </div>
  </div>

  <!-- Lead Cards Grid -->
  <div class="lead-grid" id="lead-grid">
    {''.join(cards_html)}
    <div class="empty-state-box" id="empty-state" style="{'display:none;' if cards_html else ''}">
      <div style="font-size: 36px; margin-bottom: 8px;">🚀</div>
      <h4 style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">Semua Antrean Telah Diproses (Clean Slate)</h4>
      <p style="color: var(--text-secondary); font-size: 13px; max-width: 560px; margin: 0 auto 18px; line-height: 1.5;">
        Pilih target niche industri atau wilayah di atas, lalu klik salah satu tombol aksi di bawah untuk menjaring prospek baru ke antrean dasbor:
      </p>
      <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
        <button onclick="huntOutdated(this)" class="btn-sub" style="background:#b06000; color:#fff; border-color:#b06000; font-weight:700; padding:9px 18px; font-size:13px;">
          ⚡ Buru Web B2B Lama (Jalur B)
        </button>
        <button onclick="scanNiche(this)" class="btn-sub" style="background:var(--google-blue); color:#fff; border-color:var(--google-blue); font-weight:700; padding:9px 18px; font-size:13px;">
          🔍 Scan Google Maps (Jalur A)
        </button>
      </div>
      <div style="margin-top: 18px; font-size: 12px; color: var(--text-secondary);">
        Atau via terminal: <code>python auto_outreach.py --hunt-outdated --limit 3</code> | <code>python auto_outreach.py --maps auto --limit 3</code>
      </div>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
  function showToast(msg) {{
const toast = document.getElementById('toast');
toast.style.display = 'block';
toast.innerHTML = msg;
setTimeout(() => {{ toast.style.display = 'none'; }}, 4000);
  }}

  // Real-time Google Search filtering of leads
  function filterLeads(query) {{
const q = query.toLowerCase().trim();
const cards = document.querySelectorAll('.card');
cards.forEach(card => {{
  const searchData = card.getAttribute('data-search') || '';
  card.style.display = searchData.includes(q) ? 'flex' : 'none';
}});
  }}

  function getAuthToken() {{
    const urlToken = new URLSearchParams(window.location.search).get('token');
    if (urlToken) return urlToken;
    const m = document.cookie.match(/(?:^|;\\s*)auth_token=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }}

  function getAuthHeaders() {{
    const token = getAuthToken();
    const h = {{ 'Content-Type': 'application/json' }};
    if (token) h['Authorization'] = 'Bearer ' + token;
    return h;
  }}

  function getAuthQuery() {{
    const token = getAuthToken();
    return token ? '&token=' + encodeURIComponent(token) : '';
  }}

  async function approveLead(domain, btn, step) {{
    step = step || 'step_1_permission';
    const isStep2 = step === 'step_2_delivery';
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = isStep2 ? '⏳ Mengirim WA Proposal & Demo (Tahap 2)...' : '⏳ Mengetik & Mengirim WA Izin (Tahap 1)...';
    btn.style.opacity = '0.7';

    try {{
      const res = await fetch('/api/approve?domain=' + encodeURIComponent(domain) + getAuthQuery(), {{
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({{ step: step }})
      }});
      
      const data = await res.json().catch(() => null);
      if (!res.ok) {{
        const errMsg = (data && (data.message || data.error)) || ('HTTP ' + res.status);
        throw new Error(errMsg);
      }}
      
      if (data.success) {{
        if (isStep2) {{
          btn.innerHTML = 'Proposal & Demo Tahap 2 Sudah Terkirim';
          btn.className = 'btn btn-approve btn-disabled';
          btn.disabled = true;
          btn.style.opacity = '1';
          const badge = document.getElementById('badge-' + domain.replace(/\\./g, '_'));
          if (badge) badge.innerHTML = '<span class="badge badge-demo">Proposal & Demo Terkirim 📄</span>';
          showToast('✅ WhatsApp Proposal & Demo Tahap 2 sukses terkirim ke ' + domain);
        }} else {{
          btn.innerHTML = '✓ Kirim Proposal & Demo (Tahap 2) via Bot';
          btn.className = 'btn btn-approve';
          btn.onclick = function() {{ approveLead(domain, btn, 'step_2_delivery'); }};
          btn.disabled = false;
          btn.style.opacity = '1';
          const badge = document.getElementById('badge-' + domain.replace(/\\./g, '_'));
          if (badge) badge.innerHTML = '<span class="badge badge-sent">Izin Tahap 1 Terkirim</span>';
          showToast('✅ WhatsApp Izin Tahap 1 sukses terkirim ke ' + domain);
        }}
        
        const cardId = 'card-' + domain.replace(/\\./g, '_');
        const card = document.getElementById(cardId);
        if (card && isStep2) {{
          const discardBtn = card.querySelector('.btn-discard');
          if (discardBtn) discardBtn.remove();
        }}
      }} else if (data.mode === 'restricted' || data.status === 'wa_cooldown') {{
        btn.disabled = false;
        btn.innerHTML = originalText;
        btn.style.opacity = '1';
        const badge = document.getElementById('badge-' + domain.replace(/\\./g, '_'));
        if (badge) badge.innerHTML = '<span class="badge" style="background:#fef7e0; color:#b06000; border-color:#feefc3;">⚠️ WA Cooldown Meta</span>';
        alert('⚠️ Akun WhatsApp Web (Linked Device) sedang masa cooldown pembatasan kontak baru oleh Meta (' + (data.countdown || '~2 jam 45m') + ').\\n\\n💡 Solusi Instan:\\nMeta mengizinkan pengiriman tanpa batasan melalui aplikasi WhatsApp di HP utama.\\nSilakan klik tombol [📄 Chat Demo & PDF (Tahap 2) ↗] pada kartu prospek ini untuk langsung mengirim pesan dari HP Anda, lalu klik [✓ Tandai Terkirim Manual].');
      }} else {{
        btn.disabled = false;
        btn.innerHTML = originalText;
        btn.style.opacity = '1';
        showToast('Gagal: ' + (data.errors ? data.errors.join(', ') : (data.message || data.error)));
      }}
    }} catch (err) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = '1';
      const msg = err.message || '';
      if (msg.includes('401') || msg.toLowerCase().includes('unauthorized')) {{
        alert("Sesi autentikasi dashboard kedaluwarsa.\\n\\nSilakan muat ulang (refresh) halaman dashboard di browser.");
      }} else if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {{
        alert("Server dashboard belum aktif di terminal.\\n\\nJalankan perintah ini di terminal:\\npython auto_outreach.py --dashboard");
      }} else {{
        alert("Pemberitahuan pengiriman:\\n" + msg + "\\n\\n💡 Solusi Instan:\\nAnda juga bisa langsung klik tombol [📄 Chat Demo & PDF (Tahap 2) ↗] di bawah kartu prospek untuk langsung mengirim dari WhatsApp HP/PC tanpa antrean bot!");
      }}
    }}
  }}

  async function markSent(domain, btn) {{
    if (!confirm('Tandai prospek ' + domain + ' sebagai sudah terkirim via WhatsApp HP?')) return;
    try {{
      const res = await fetch('/api/mark-sent?domain=' + encodeURIComponent(domain) + getAuthQuery(), {{
        method: 'POST',
        headers: getAuthHeaders()
      }});
      const data = await res.json();
      if (data.success) {{
        const isStep2 = data.status === 'sent_step2';
        const badge = document.getElementById('badge-' + domain.replace(/\\./g, '_'));
        if (badge) {{
          badge.innerHTML = isStep2 ? '<span class="badge badge-demo">Proposal & Demo Terkirim 📄</span>' : '<span class="badge badge-sent">Izin Tahap 1 Terkirim</span>';
        }}
        const card = document.getElementById('card-' + domain.replace(/\\./g, '_'));
        if (card) {{
          const approveBtn = card.querySelector('.btn-approve');
          if (approveBtn) {{
            if (isStep2) {{
              approveBtn.innerHTML = 'Proposal & Demo Tahap 2 Sudah Terkirim';
              approveBtn.className = 'btn btn-approve btn-disabled';
              approveBtn.disabled = true;
              btn.remove();
            }} else {{
              approveBtn.innerHTML = '✓ Kirim Proposal & Demo (Tahap 2) via Bot';
              approveBtn.className = 'btn btn-approve';
              approveBtn.onclick = function() {{ approveLead(domain, approveBtn, 'step_2_delivery'); }};
              approveBtn.disabled = false;
            }}
          }}
        }}
        showToast('✅ ' + (data.message || ('Prospek ' + domain + ' berhasil ditandai')));
      }}
    }} catch (e) {{
      alert('Gagal update status: ' + e);
    }}
  }}

  async function discardLead(domain, btn) {{
    if (!confirm('Hapus prospek ' + domain + ' dari antrean dan bersihkan folder disk?')) return;

    const cardId = 'card-' + domain.replace(/\\./g, '_');
    const card = document.getElementById(cardId);

    // Instantly remove card with smooth animation
    if (card) {{
      card.style.transition = 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)';
      card.style.opacity = '0';
      card.style.transform = 'scale(0.92)';
      setTimeout(() => {{ card.remove(); }}, 250);
    }}

    try {{
      const res = await fetch('/api/discard?domain=' + encodeURIComponent(domain) + getAuthQuery(), {{
        method: 'POST',
        headers: getAuthHeaders()
      }});
      const data = await res.json();
      if (!res.ok || !data.success) {{
        showToast('Gagal discard: ' + (data.error || 'Server error'));
        return;
      }}
      showToast('🗑️ Prospek ' + domain + ' & folder fisik berhasil dibersihkan.');
      
      const totalEl = document.getElementById('stat-total-cnt');
      if (totalEl) {{
        let cur = parseInt(totalEl.innerText) || 1;
        totalEl.innerText = Math.max(0, cur - 1);
      }}
    }} catch (err) {{
      showToast('Prospek ' + domain + ' di-discard.');
    }}
  }}

  async function deployVercel(domain, btn) {{
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = 'Deploying...';
    try {{
      const res = await fetch('/api/deploy-vercel?domain=' + encodeURIComponent(domain) + getAuthQuery(), {{
        method: 'POST',
        headers: getAuthHeaders()
      }});
      const data = await res.json();
      if (data.success) {{
        btn.outerHTML = `<a href="${{data.url}}" target="_blank" class="btn-sub">🌐 Live Demo ↗</a>`;
        showToast('Website berhasil live di Vercel: ' + data.url);
      }} else {{
        btn.disabled = false;
        btn.innerHTML = originalText;
        alert('Gagal deploy: ' + data.error);
      }}
    }} catch (e) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      alert('Error server: ' + e);
    }}
  }}

  async function createInvoice(domain, btn) {{
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = 'Membuat invoice...';
    try {{
      const res = await fetch('/api/create-invoice?domain=' + encodeURIComponent(domain) + getAuthQuery(), {{
        method: 'POST',
        headers: getAuthHeaders()
      }});
      const data = await res.json();
      if (data.success) {{
        btn.disabled = false;
        btn.innerHTML = '💳 Buka Invoice';
        btn.onclick = () => window.open(data.payment_url, '_blank');
        showToast('Link Invoice $100: ' + data.payment_url);
        navigator.clipboard.writeText(data.payment_url);
      }} else {{
        btn.disabled = false;
        btn.innerHTML = originalText;
        alert('Gagal membuat invoice: ' + data.error);
      }}
    }} catch (e) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      alert('Error server: ' + e);
    }}
  }}

  async function checkReplies() {{
showToast('Sedang memindai balasan WhatsApp masuk...');
try {{
  const res = await fetch('/api/check-replies', {{ method: 'POST' }});
  const data = await res.json();
  showToast('Pemeriksaan selesai. Balasan baru: ' + (data.replies_found || 0));
  setTimeout(() => location.reload(), 1500);
}} catch (e) {{
  alert('Gagal memeriksa balasan: ' + e);
}}
  }}

  let currentFilter = 'all';
  function filterByTag(tag, el) {{
    currentFilter = tag;
    document.querySelectorAll('.stat-chip').forEach(c => c.classList.remove('active-filter'));
    if (el) el.classList.add('active-filter');

    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {{
      const track = card.getAttribute('data-track') || '';
      const status = card.getAttribute('data-status') || '';

      let match = false;
      if (tag === 'all') match = true;
      else if (tag === 'track_a') match = (track === 'track_a_new_web');
      else if (tag === 'track_b') match = (track !== 'track_a_new_web');
      else if (tag === 'email') match = (status === 'fallback_email');
      else if (tag === 'replied') match = ['replied', 'demo_sent', 'options_sent'].includes(status);
      else if (tag === 'paid') match = (status === 'paid');

      card.style.display = match ? 'flex' : 'none';
    }});
  }}

  async function huntOutdated(btn) {{
    const scopeEl = document.getElementById('target-scope');
    const scope = scopeEl ? scopeEl.value : 'auto';
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ Memburu Web B2B...';
    btn.style.opacity = '0.7';
    showToast('⚡ [Jalur B] Memburu website B2B lama via SERP Dorking (' + scope + ')...');

    try {{
      const res = await fetch('/api/hunt-outdated' + (getAuthToken() ? '?token=' + encodeURIComponent(getAuthToken()) : ''), {{
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({{ category: scope, limit: 3 }})
      }});
      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = '1';

      if (data.success && data.count > 0) {{
        showToast('🎉 Berhasil menjaring ' + data.count + ' website B2B lama siap modernisasi!');
        setTimeout(() => location.reload(), 1200);
      }} else if (data.success && data.count === 0) {{
        alert(data.message || 'Tidak ada website lama baru yang terdeteksi atau semua sudah ada di antrean.');
      }} else {{
        alert('Gagal memburu: ' + (data.error || 'Terjadi kesalahan pada mesin pemburu.'));
      }}
    }} catch (e) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = '1';
      alert('Error server: ' + e);
    }}
  }}

  async function scanNiche(btn) {{
    const scopeEl = document.getElementById('target-scope');
    const scope = scopeEl ? scopeEl.value : 'auto';
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ Memindai Google Maps...';
    btn.style.opacity = '0.7';
    showToast('🔍 [Jalur A] Memindai Google Maps untuk UKM berdaya beli tinggi (' + scope + ')...');

    try {{
      const res = await fetch('/api/scan-niche' + (getAuthToken() ? '?token=' + encodeURIComponent(getAuthToken()) : ''), {{
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({{ scope: scope, limit: 3 }})
      }});
      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = '1';

      if (data.success && data.count > 0) {{
        showToast('🎉 Berhasil menambahkan ' + data.count + ' UKM baru ke antrean!');
        setTimeout(() => location.reload(), 1200);
      }} else if (data.success && data.count === 0) {{
        alert(data.message || 'Tidak ada prospek baru yang memenuhi kriteria atau semua sudah tersimpan di antrean.');
      }} else {{
        alert('Gagal memindai: ' + (data.error || 'Terjadi kesalahan saat pemindaian.'));
      }}
    }} catch (e) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = '1';
      alert('Error server: ' + e);
    }}
  }}

  function scanKalimantan(btn) {{
    return scanNiche(btn);
  }}

  async function deployVercel(domain, btn) {{
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ Mendeploy...';
    btn.style.opacity = '0.7';
    showToast('🚀 Mengunggah prototipe live ' + domain + ' ke Vercel Cloud...');

    try {{
      const res = await fetch('/api/deploy-vercel' + (getAuthToken() ? '?token=' + encodeURIComponent(getAuthToken()) : ''), {{
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({{ domain: domain }})
      }});
      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = '1';

      if (data.success && data.url) {{
        showToast('🎉 Live Vercel aktif: ' + data.url);
        setTimeout(() => {{ window.location.reload(); }}, 1200);
      }} else {{
        alert('Gagal deploy ke Vercel: ' + (data.error || 'Terjadi kesalahan sistem.'));
      }}
    }} catch (e) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      btn.style.opacity = '1';
      alert('Error server: ' + e);
    }}
  }}
</script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    return output_path
