"""
Dedicated B2B Email Dispatcher Module.
Sends executive proposals and modernization audits via dedicated/isolated SMTP accounts.
Includes draft simulation mode and HTML/EML preview logging for 100% safe testing.
"""

import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional


def load_env_file(env_path: Optional[str] = None):
    """Loads key-value pairs from .env file if present without requiring external package."""
    if not env_path:
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception:
            pass


class EmailDispatcher:
    def __init__(self):
        load_env_file()
        self.smtp_host = os.environ.get("OUTREACH_EMAIL_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("OUTREACH_EMAIL_PORT", "587"))
        self.sender_email = os.environ.get("OUTREACH_EMAIL_USER", "").strip()
        self.sender_password = os.environ.get("OUTREACH_EMAIL_PASSWORD", "").strip().replace(" ", "")
        self.sender_name = os.environ.get("OUTREACH_SENDER_NAME", "Web Modernization Studio").strip()
        self.contact_wa = os.environ.get("OUTREACH_SENDER_WA", "").strip()

    def generate_email_body(self, business_name: str, domain: str, audit_signals: list) -> Dict[str, str]:
        """Generates professional Indonesian B2B proposal copy."""
        signals_text = ""
        if audit_signals:
            signals_text = "\n".join([f"  • {s}" for s in audit_signals[:3]])
        else:
            signals_text = "  • Peningkatan visual responsif di layar smartphone\n  • Integrasi tombol WhatsApp direct chat untuk konversi lead\n  • Optimasi meta SEO Google agar lebih mudah ditemukan pelanggan"

        subject = f"Rekomendasi Modernisasi & Audit Website {business_name} (Dokumen Terlampir)"

        plain_text = f"""Yth. Tim Manajemen / Pimpinan {business_name},

Semoga pesan ini menjumpai Anda dalam keadaan sehat dan sukses.

Kami baru saja meninjau website Anda ({domain}). Bisnis Anda memiliki profil layanan yang sangat prospektif, namun kami melihat ada beberapa peluang optimasi teknis & visual yang dapat meningkatkan kepercayaan calon pelanggan:

{signals_text}

Sebagai bagian dari inisiatif peningkatan standar digital bisnis di Indonesia, tim kami telah menyusun satu dokumen proposal dan audit komprehensif, serta merancang konsep purwarupa tampilan website yang jauh lebih modern, cepat diakses dari HP, dan ramah Google SEO.

Biaya pengerjaan turn-key all-in kami tawarkan flat $100 USD (flat kurs terjangkau tanpa biaya tersembunyi), mencakup redesain total, copywriting profesional, optimasi SEO, hingga serah terima source code lengkap.

Dokumen detail proposal eksekutif 4 halaman telah kami lampirkan bersama email ini (PDF).

Jika Anda berkenan mendiskusikan atau melihat demonstrasi tampilan barunya, silakan balas email ini atau hubungi kami melalui WhatsApp di {self.contact_wa or 'nomor kontak terlampir'}.

Terima kasih atas waktu dan perhatian Anda.

Salam hangat,
{self.sender_name}
Layanan Desain & Modernisasi Website Profesional
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; background-color: #f8fafc; margin: 0; padding: 24px; }}
  .container {{ max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
  .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 16px; margin-bottom: 24px; }}
  .header h2 {{ margin: 0; color: #0f172a; font-size: 20px; }}
  .badge {{ display: inline-block; background: #eff6ff; color: #1d4ed8; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; margin-top: 8px; }}
  .box {{ background: #f1f5f9; border-left: 4px solid #3b82f6; padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
  .box ul {{ margin: 6px 0; padding-left: 20px; }}
  .price-tag {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 16px; text-align: center; margin: 24px 0; }}
  .price-tag .amount {{ font-size: 24px; font-weight: 700; color: #065f46; }}
  .cta-btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 12px; }}
  .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 13px; color: #64748b; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2>Audit & Rekomendasi Modernisasi Website</h2>
    <span class="badge">Khusus untuk {business_name}</span>
  </div>
  
  <p>Yth. Pimpinan / Tim Manajemen <strong>{business_name}</strong>,</p>
  
  <p>Semoga pesan ini menjumpai Anda dan rekan-rekan dalam kondisi prima dan sukses selalu.</p>
  
  <p>Kami baru saja melakukan evaluasi teknis terhadap website operasional Anda di <a href="https://{domain}" target="_blank"><strong>{domain}</strong></a>. Bisnis Anda memiliki fondasi layanan yang sangat kredibel, namun kami melihat beberapa aspek penting yang dapat ditingkatkan secara signifikan:</p>
  
  <div class="box">
    <strong>Temuan Utama & Area Peluang:</strong>
    <ul>
      {''.join([f'<li>{s}</li>' for s in audit_signals[:3]]) if audit_signals else '<li>Tampilan mobile responsif untuk kenyamanan pengguna HP</li><li>Integrasi fast WhatsApp checkout & inquiry</li><li>Optimasi struktur SEO Google</li>'}
    </ul>
  </div>

  <p>Tim kami telah menyusun <strong>Dokumen Proposal & Audit Eksekutif</strong> setebal 4 halaman yang merinci perbandingan tampilan baru, peningkatan SEO, dan arsitektur visual modern. Dokumen PDF lengkap telah kami lampirkan bersama email ini.</p>

  <div class="price-tag">
    <div style="font-size: 13px; color: #047857; text-transform: uppercase; letter-spacing: 0.5px;">Paket Turn-Key Modernisasi Lengkap</div>
    <div class="amount">$100 USD <span style="font-size: 15px; font-weight: 400; color: #065f46;">(Flat Kurs IDR / All-Inclusive)</span></div>
    <div style="font-size: 12px; color: #059669; margin-top: 4px;">Termasuk redesain penuh, copywriting, mobile & SEO optimization, serah terima kode bersih.</div>
  </div>

  <p>Silakan unduh dokumen PDF terlampir. Apabila Bapak/Ibu berminat melihat preview live interaktif website versi barunya, kami sangat terbuka untuk berdiskusi santai melalui balasan email ini atau langsung via WhatsApp:</p>

  {f'<div style="margin: 16px 0;"><a href="https://wa.me/{re.sub(r"[^0-9]", "", self.contact_wa)}" target="_blank" style="background-color: #16a34a; color: #ffffff !important; padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; font-size: 14px;">💬 Chat WhatsApp Tim Kami ({self.contact_wa})</a></div>' if self.contact_wa else ''}

  <p style="margin-top: 24px;">
    Salam hangat dan sukses selalu,<br>
    <strong>{self.sender_name}</strong><br>
    <span style="font-size: 13px; color: #64748b;">Specialist Website Modernization & Conversion</span>
  </p>

  <div class="footer">
    Email ini dikirimkan khusus sebagai penawaran kemitraan profesional B2B. Dokumen proposal <em>client_proposal.pdf</em> terlampir di email ini.
  </div>
</div>
</body>
</html>
"""
        return {"subject": subject, "plain": plain_text, "html": html_body}

    def dispatch(
        self,
        recipient_email: str,
        business_name: str,
        domain: str,
        pdf_path: Optional[str] = None,
        audit_signals: Optional[list] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Sends the proposal email or saves a draft if dry_run=True or credentials are unconfigured.
        """
        content = self.generate_email_body(business_name, domain, audit_signals or [])
        draft_dir = os.path.join(os.path.dirname(__file__), "..", "..", "clients", "outreach_drafts", domain)
        os.makedirs(draft_dir, exist_ok=True)

        msg = MIMEMultipart("mixed")
        msg["Subject"] = content["subject"]
        msg["From"] = f"{self.sender_name} <{self.sender_email or 'dedicated-outreach@agency.com'}>"
        msg["To"] = recipient_email

        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(content["plain"], "plain", "utf-8"))
        alt_part.attach(MIMEText(content["html"], "html", "utf-8"))
        msg.attach(alt_part)

        # Attach PDF if exists
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                pdf_attachment.add_header(
                    "Content-Disposition", "attachment", filename=f"Proposal_Modernisasi_{business_name.replace(' ', '_')}.pdf"
                )
                msg.attach(pdf_attachment)

        # Save HTML and EML draft locally for verification
        eml_path = os.path.join(draft_dir, "email_proposal.eml")
        html_path = os.path.join(draft_dir, "email_proposal_preview.html")
        with open(eml_path, "w", encoding="utf-8") as f:
            f.write(msg.as_string())
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content["html"])

        # Check if we can actually send
        is_configured = bool(self.sender_email and self.sender_password)

        if dry_run or not is_configured:
            reason = "Dry-run mode active" if dry_run else "Dedicated email credentials not configured in .env"
            return {
                "success": True,
                "mode": "dry_run" if dry_run else "draft_only",
                "recipient": recipient_email,
                "eml_path": eml_path,
                "html_path": html_path,
                "message": f"Proposal email draft created successfully ({reason})."
            }

        # Live SMTP sending via dedicated account
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, [recipient_email], msg.as_string())

            return {
                "success": True,
                "mode": "live_sent",
                "recipient": recipient_email,
                "eml_path": eml_path,
                "message": f"Email successfully dispatched to {recipient_email} from dedicated account {self.sender_email}."
            }
        except Exception as e:
            return {
                "success": False,
                "mode": "error",
                "recipient": recipient_email,
                "error": str(e),
                "eml_path": eml_path,
                "message": f"SMTP Error sending to {recipient_email}: {e}"
            }
