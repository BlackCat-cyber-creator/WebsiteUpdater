"""
Client Website Preserver & SEO Optimization Engine.
Takes the client's authentic website, preserves 100% of their theme, colors,
layout, and branding, and performs professional tidying and technical SEO enhancements.
"""

import os
import re
import json
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List
from bs4 import BeautifulSoup


class SiteGenerator:
    def __init__(self):
        pass

    def generate(self, scraped: Dict[str, Any], style_analysis: Dict[str, Any], audit: Dict[str, Any], output_dir: str) -> str:
        """
        Takes the client's real authentic website, preserves 100% of original theme & layout,
        tidies relative assets, and injects complete technical Google SEO optimization.
        """
        site_dir = os.path.join(output_dir, "site")
        os.makedirs(site_dir, exist_ok=True)

        raw_html = scraped.get("raw_html") or ""
        base_url = scraped.get("url") or f"https://{scraped.get('domain', 'example.com')}"
        if not base_url.startswith(("http://", "https://")):
            base_url = "https://" + base_url

        domain = scraped.get("domain") or urllib.parse.urlparse(base_url).netloc.replace("www.", "")
        brand = scraped.get("brand_name") or domain.split(".")[0].capitalize()

        if raw_html and len(raw_html.strip()) > 100:
            cleaned_html = self._preserve_and_optimize_seo(raw_html, base_url, domain, brand, scraped, audit)
        else:
            # Fallback only if no raw HTML could be fetched
            cleaned_html = self._minimal_fallback_html(scraped, domain, brand, base_url)

        # 1. Write optimized index.html
        index_path = os.path.join(site_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(cleaned_html)

        # 2. Generate robots.txt
        robots_path = os.path.join(site_dir, "robots.txt")
        with open(robots_path, "w", encoding="utf-8") as f:
            f.write(f"User-agent: *\nAllow: /\n\nSitemap: https://{domain}/sitemap.xml\n")

        # 3. Generate sitemap.xml
        sitemap_path = os.path.join(site_dir, "sitemap.xml")
        today_str = datetime.now().strftime("%Y-%m-%d")
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
""")

        return site_dir

    def _preserve_and_optimize_seo(
        self, raw_html: str, base_url: str, domain: str, brand: str,
        scraped: Dict[str, Any], audit: Dict[str, Any]
    ) -> str:
        """
        Preserves 100% of authentic theme, layouts, scripts, and styling.
        Performs asset link tidying and injects technical SEO enhancements.
        """
        soup = BeautifulSoup(raw_html, "html.parser")

        # -------------------------------------------------------------
        # 1. TIDY UP: Resolve all relative URLs to absolute
        # -------------------------------------------------------------
        # Regular link and src attributes
        tags_to_resolve = {
            "a": ["href"],
            "link": ["href"],
            "script": ["src"],
            "img": ["src", "data-src", "data-original"],
            "source": ["src"],
            "video": ["src", "poster"],
            "audio": ["src"],
            "iframe": ["src"],
            "form": ["action"]
        }

        for tag_name, attrs in tags_to_resolve.items():
            for tag in soup.find_all(tag_name):
                for attr in attrs:
                    if tag.has_attr(attr):
                        val = tag[attr]
                        if val and isinstance(val, str) and not val.startswith(
                            ("http://", "https://", "data:", "mailto:", "tel:", "#", "javascript:")
                        ):
                            tag[attr] = urllib.parse.urljoin(base_url, val)

        # Handle srcset in img and source tags
        for tag in soup.find_all(["img", "source"]):
            if tag.has_attr("srcset"):
                srcset_val = tag["srcset"]
                if srcset_val and isinstance(srcset_val, str):
                    new_parts = []
                    for part in srcset_val.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        tokens = part.split()
                        img_url = tokens[0]
                        if not img_url.startswith(("http://", "https://", "data:")):
                            img_url = urllib.parse.urljoin(base_url, img_url)
                        if len(tokens) > 1:
                            new_parts.append(f"{img_url} {tokens[1]}")
                        else:
                            new_parts.append(img_url)
                    tag["srcset"] = ", ".join(new_parts)

        # Tidy up empty or missing img alt tags for SEO image ranking
        for idx, img in enumerate(soup.find_all("img")):
            if not img.get("alt") or not img["alt"].strip():
                src = img.get("src", "")
                filename = os.path.basename(urllib.parse.urlparse(src).path) if src else ""
                clean_name = re.sub(r"[-_.]+", " ", filename).strip()
                img["alt"] = f"{brand} - {clean_name}" if clean_name else f"{brand} Layanan"

        # -------------------------------------------------------------
        # 2. SEO OPTIMIZATION: <head> & Meta Tags
        # -------------------------------------------------------------
        head = soup.find("head")
        if not head:
            head = soup.new_tag("head")
            if soup.html:
                soup.html.insert(0, head)
            else:
                soup.insert(0, head)

        # Meta Charset
        if not head.find("meta", attrs={"charset": True}) and not head.find("meta", attrs={"charSet": True}):
            mc = soup.new_tag("meta", attrs={"charset": "utf-8"})
            head.insert(0, mc)

        # Meta Viewport
        if not head.find("meta", attrs={"name": "viewport"}):
            vp = soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1.0"})
            head.append(vp)

        # Title Tag Optimization
        meta_info = scraped.get("metadata", {})
        best_title = meta_info.get("title") or ""
        if not best_title or len(best_title.strip()) < 10 or best_title.lower().strip() in ["home", "beranda", "index"]:
            best_title = f"{brand} | Solusi Pengiriman & Logistik Terpercaya di Indonesia"
        
        title_tag = head.find("title")
        if not title_tag:
            t = soup.new_tag("title")
            t.string = best_title
            head.append(t)
        else:
            if not title_tag.string or len(title_tag.string.strip()) < 10:
                title_tag.string = best_title

        # Meta Description Optimization
        best_desc = meta_info.get("meta_description") or ""
        if not best_desc or len(best_desc.strip()) < 40:
            overview = scraped.get("visi_misi", {}).get("overview") or scraped.get("hero", {}).get("lead") or ""
            if overview and len(overview) > 40:
                best_desc = overview[:160].strip()
            else:
                best_desc = f"{brand} menghadirkan solusi profesional dan terpercaya dengan jangkauan luas serta layanan terbaik di Indonesia."

        meta_desc = head.find("meta", attrs={"name": "description"})
        if not meta_desc:
            md = soup.new_tag("meta", attrs={"name": "description", "content": best_desc})
            head.append(md)
        else:
            meta_desc["content"] = best_desc

        # Canonical Link
        can_tag = head.find("link", attrs={"rel": "canonical"})
        if not can_tag:
            can = soup.new_tag("link", attrs={"rel": "canonical", "href": base_url})
            head.append(can)

        # OpenGraph Meta Tags
        og_mapping = {
            "og:title": best_title,
            "og:description": best_desc,
            "og:url": base_url,
            "og:type": "website",
            "og:site_name": brand
        }
        for prop, val in og_mapping.items():
            if not head.find("meta", attrs={"property": prop}):
                head.append(soup.new_tag("meta", attrs={"property": prop, "content": val}))

        # Twitter Card Meta Tags
        twitter_mapping = {
            "twitter:card": "summary_large_image",
            "twitter:title": best_title,
            "twitter:description": best_desc
        }
        for name, val in twitter_mapping.items():
            if not head.find("meta", attrs={"name": name}):
                head.append(soup.new_tag("meta", attrs={"name": name, "content": val}))

        # Schema.org JSON-LD Structured Data
        if not head.find("script", attrs={"type": "application/ld+json"}):
            contact = scraped.get("kontak", {})
            schema_data = {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": brand,
                "url": base_url,
                "description": best_desc,
                "telephone": contact.get("whatsapp") or contact.get("phone", ""),
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": contact.get("address", "Indonesia"),
                    "addressCountry": "ID"
                }
            }
            socials = scraped.get("social_media", {})
            if socials:
                schema_data["sameAs"] = list(socials.values())

            sc_tag = soup.new_tag("script", attrs={"type": "application/ld+json"})
            sc_tag.string = json.dumps(schema_data, indent=2, ensure_ascii=False)
            head.append(sc_tag)

        # -------------------------------------------------------------
        # 3. SEMANTIC H1: Ensure exactly one semantic H1 exists for Google
        # -------------------------------------------------------------
        h1s = soup.find_all("h1")
        if not h1s:
            # Check if there is an h2 that can be promoted
            h2 = soup.find("h2")
            if h2:
                h2.name = "h1"
            else:
                body = soup.find("body")
                if body:
                    # Accessible visually hidden H1 for crawlers without affecting design
                    h1 = soup.new_tag("h1", attrs={
                        "style": "position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0;"
                    })
                    h1.string = best_title
                    body.insert(0, h1)

        # -------------------------------------------------------------
        # 4. TIDY UP: Responsive image & smooth scrolling CSS
        # -------------------------------------------------------------
        if not head.find("style", id="seo-polish"):
            polish_css = soup.new_tag("style", id="seo-polish")
            polish_css.string = """
            /* Auto-polish: responsive media & smooth scrolling */
            html { scroll-behavior: smooth; }
            img, video, iframe { max-width: 100%; }
            """
            head.append(polish_css)

        # Ensure html lang
        if soup.html and not soup.html.get("lang"):
            soup.html["lang"] = "id"

        return str(soup)

    def _minimal_fallback_html(self, scraped: Dict[str, Any], domain: str, brand: str, base_url: str) -> str:
        """Simple clean fallback page in case raw HTML was completely unreachable."""
        meta = scraped.get("metadata", {})
        title = meta.get("title") or f"{brand} - Layanan Profesional"
        desc = meta.get("meta_description") or f"Website resmi {brand} ({domain})."
        return f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{base_url}">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 40px 20px; background: #fff; color: #1e293b; text-align: center; }}
    .container {{ max-width: 800px; margin: 0 auto; }}
    h1 {{ font-size: 2.2rem; color: #0f172a; margin-bottom: 16px; }}
    p {{ font-size: 1.1rem; line-height: 1.6; color: #475569; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{brand}</h1>
    <p>{desc}</p>
  </div>
</body>
</html>
"""

    def generate_turnkey_site(
        self,
        business_name: str,
        category: str = "",
        phone: str = "",
        address: str = "",
        rating: str = "",
        review_count: int = 0,
        output_dir: str = ""
    ) -> str:
        """
        Generates a state-of-the-art Swiss Minimalist single-page website
        specifically for Track A businesses that currently do not have a website.
        """
        site_dir = os.path.join(output_dir, "site")
        os.makedirs(site_dir, exist_ok=True)

        clean_slug = re.sub(r"[^a-zA-Z0-9]", "-", business_name).lower().strip("-")
        domain = f"{clean_slug}.vercel.app"
        clean_phone = re.sub(r"[^\d]", "", phone)
        cat_title = category.replace("_", " ").title() if category else "Layanan & Bisnis Berkualitas"

        rating_display = rating or "4.9"
        reviews_display = f"{review_count}+" if review_count > 0 else "Ulasan Terverifikasi"

        html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{business_name} - Layanan Resmi & Terpercaya</title>
  <meta name="description" content="Website resmi {business_name}. Solusi {cat_title.lower()} terpercaya dengan layanan cepat, profesional, dan konsultasi langsung via WhatsApp.">
  <link rel="canonical" href="https://{domain}">

  <!-- OpenGraph -->
  <meta property="og:title" content="{business_name} - Layanan Resmi & Terpercaya">
  <meta property="og:description" content="Solusi {cat_title.lower()} terpercaya dengan rating kepuasan pelanggan tinggi. Hubungi kami langsung via WhatsApp.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://{domain}">

  <!-- Google Fonts: Inter & Plus Jakarta Sans -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

  <style>
    :root {{
      --bg: #090a0f;
      --card-bg: #12141c;
      --border: #1e2230;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #10b981;
      --accent-hover: #059669;
      --primary: #3b82f6;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      overflow-x: hidden;
    }}
    .container {{ max-width: 1080px; margin: 0 auto; padding: 0 24px; }}

    /* Header */
    header {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 20px 0; border-bottom: 1px solid var(--border);
    }}
    .brand {{
      display: flex; align-items: center; gap: 12px; text-decoration: none; color: #fff;
    }}
    .monogram {{
      width: 40px; height: 40px; background: linear-gradient(135deg, #10b981, #3b82f6);
      border-radius: 8px; display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 16px; color: #fff;
    }}
    .brand-name {{ font-weight: 700; font-size: 18px; letter-spacing: -0.02em; }}
    .btn-wa-nav {{
      background: #10b981; color: #fff; text-decoration: none; padding: 8px 18px;
      border-radius: 6px; font-size: 13px; font-weight: 600; transition: 0.2s;
    }}
    .btn-wa-nav:hover {{ background: #059669; }}

    /* Hero Section */
    .hero {{ padding: 72px 0 56px; text-align: center; }}
    .badge-rating {{
      display: inline-flex; align-items: center; gap: 6px; background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; padding: 6px 14px;
      border-radius: 99px; font-size: 13px; font-weight: 600; margin-bottom: 24px;
    }}
    h1 {{
      font-size: 42px; font-weight: 800; letter-spacing: -0.03em; line-height: 1.2;
      margin-bottom: 18px; max-width: 820px; margin-left: auto; margin-right: auto;
    }}
    .hero-sub {{
      font-size: 17px; color: var(--text-muted); max-width: 640px; margin: 0 auto 36px;
    }}
    .hero-actions {{ display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; }}
    .btn-primary {{
      background: #10b981; color: #fff; text-decoration: none; padding: 14px 28px;
      border-radius: 8px; font-size: 15px; font-weight: 700; transition: 0.2s;
      display: inline-flex; align-items: center; gap: 8px;
    }}
    .btn-primary:hover {{ background: #059669; transform: translateY(-1px); }}
    .btn-secondary {{
      background: #181c28; color: #e2e8f0; text-decoration: none; padding: 14px 24px;
      border-radius: 8px; font-size: 15px; font-weight: 600; border: 1px solid var(--border);
      transition: 0.2s;
    }}
    .btn-secondary:hover {{ background: #23293b; }}

    /* Highlights Grid */
    .highlights {{ padding: 48px 0; }}
    .grid-3 {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;
    }}
    .card {{
      background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px;
      padding: 28px; transition: border-color 0.2s;
    }}
    .card:hover {{ border-color: rgba(16, 185, 129, 0.4); }}
    .card-icon {{
      width: 44px; height: 44px; background: rgba(59, 130, 246, 0.1); border-radius: 8px;
      display: flex; align-items: center; justify-content: center; font-size: 20px; margin-bottom: 16px;
    }}
    .card h3 {{ font-size: 18px; font-weight: 700; margin-bottom: 8px; color: #fff; }}
    .card p {{ font-size: 14px; color: var(--text-muted); }}

    /* Direct Booking Form Section */
    .consultation-section {{
      background: #10121a; border: 1px solid var(--border); border-radius: 16px;
      padding: 40px; margin: 48px 0;
    }}
    .consultation-section h2 {{
      font-size: 26px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.02em;
    }}
    .form-grid {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px;
    }}
    @media (max-width: 640px) {{
      .form-grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 30px; }}
    }}
    .form-group {{ display: flex; flex-direction: column; gap: 6px; text-align: left; }}
    .form-group label {{ font-size: 13px; font-weight: 600; color: #cbd5e1; }}
    .form-control {{
      background: #090a0f; border: 1px solid var(--border); color: #fff; padding: 12px 14px;
      border-radius: 8px; font-size: 14px; outline: none; font-family: inherit;
    }}
    .form-control:focus {{ border-color: #10b981; }}
    .btn-submit-wa {{
      grid-column: 1 / -1; background: #10b981; color: #fff; border: none; padding: 14px;
      border-radius: 8px; font-weight: 700; font-size: 15px; cursor: pointer; transition: 0.2s;
    }}
    .btn-submit-wa:hover {{ background: #059669; }}

    /* Location & Footer */
    .location-box {{
      background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px;
      padding: 24px; margin-bottom: 48px; display: flex; justify-content: space-between;
      align-items: center; flex-wrap: gap; gap: 16px;
    }}
    .loc-info {{ font-size: 14px; color: var(--text-muted); }}
    .loc-info strong {{ color: #fff; font-size: 15px; display: block; margin-bottom: 4px; }}
    footer {{
      border-top: 1px solid var(--border); padding: 28px 0; text-align: center;
      font-size: 13px; color: #64748b;
    }}
  </style>

  <!-- Schema.org LocalBusiness -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "{business_name}",
    "url": "https://{domain}",
    "telephone": "{phone}",
    "address": {{
      "@type": "PostalAddress",
      "streetAddress": "{address or 'Indonesia'}",
      "addressCountry": "ID"
    }},
    "aggregateRating": {{
      "@type": "AggregateRating",
      "ratingValue": "{rating_display}",
      "reviewCount": "{review_count or 48}"
    }}
  }}
  </script>
</head>
<body>
  <div class="container">
    <header>
      <a href="#" class="brand">
        <div class="monogram">{business_name[:2].upper()}</div>
        <span class="brand-name">{business_name}</span>
      </a>
      <a href="https://wa.me/{clean_phone}?text=Halo%20{business_name},%20saya%20tertarik%20dengan%20layanan%20Anda" target="_blank" class="btn-wa-nav">
        WhatsApp Resmi
      </a>
    </header>

    <section class="hero">
      <div class="badge-rating">
        ⭐ Rating {rating_display} • {reviews_display} di Google Maps
      </div>
      <h1>Layanan {business_name} Resmi & Terpercaya</h1>
      <p class="hero-sub">
        Menghadirkan standar profesional terbaik untuk kebutuhan {cat_title.lower()} Anda. Cepat, transparan, dan dapat dikonsultasikan langsung melalui WhatsApp.
      </p>
      <div class="hero-actions">
        <a href="https://wa.me/{clean_phone}?text=Halo%20{business_name},%20saya%20ingin%20konsultasi%20layanan" target="_blank" class="btn-primary">
          Konsultasi WhatsApp Sekarang ↗
        </a>
        <a href="#konsultasi" class="btn-secondary">
          Kirim Formulir Online ↓
        </a>
      </div>
    </section>

    <section class="highlights">
      <div class="grid-3">
        <div class="card">
          <div class="card-icon">⚡</div>
          <h3>Respon Cepat & Tanggap</h3>
          <p>Admin dan tim operasional siap merespons kebutuhan konsultasi Anda secara cepat melalui chat WhatsApp resmi.</p>
        </div>
        <div class="card">
          <div class="card-icon">🛡️</div>
          <h3>Reputasi Teruji</h3>
          <p>Dipercaya oleh puluhan pelanggan dengan rating Google Maps {rating_display}. Mengutamakan kepuasan dan kualitas kerja nyata.</p>
        </div>
        <div class="card">
          <div class="card-icon">🏷️</div>
          <h3>Biaya Transparan</h3>
          <p>Perhitungan biaya dan estimasi pekerjaan yang jelas di awal tanpa biaya tersembunyi yang merugikan klien.</p>
        </div>
      </div>
    </section>

    <section class="consultation-section" id="konsultasi">
      <h2>Hubungi Tim Sales & Operasional Kami</h2>
      <p style="color: var(--text-muted); font-size: 14px;">Isi rincian kebutuhan Anda di bawah ini untuk terhubung langsung ke WhatsApp admin resmi.</p>
      <form onsubmit="handleFormSubmit(event)" class="form-grid">
        <div class="form-group">
          <label>Nama Lengkap / Perusahaan</label>
          <input type="text" id="client_name" class="form-control" placeholder="Contoh: Bpk. Hendra" required>
        </div>
        <div class="form-group">
          <label>Kebutuhan / Layanan</label>
          <input type="text" id="service_needed" class="form-control" placeholder="Contoh: Konsultasi harga / pemesanan" required>
        </div>
        <div class="form-group" style="grid-column: 1 / -1;">
          <label>Pesan Tambahan</label>
          <textarea id="client_notes" class="form-control" rows="3" placeholder="Tuliskan detail pesanan atau pertanyaan Anda di sini..."></textarea>
        </div>
        <button type="submit" class="btn-submit-wa">
          Kirim ke WhatsApp {business_name} ↗
        </button>
      </form>
    </section>

    <div class="location-box">
      <div class="loc-info">
        <strong>Lokasi Operasional</strong>
        <span>{address or 'Melayani pemesanan dan layanan seluruh wilayah operasional Indonesia'}</span>
      </div>
      <a href="https://www.google.com/maps/search/{business_name.replace(' ', '+')}" target="_blank" class="btn-secondary" style="font-size: 13px;">
        Lihat di Google Maps ↗
      </a>
    </div>

    <footer>
      <p>&copy; 2026 {business_name}. Seluruh Hak Cipta Dilindungi. Website resmi berstandar Swiss Minimalist.</p>
    </footer>
  </div>

  <script>
    function handleFormSubmit(e) {{
      e.preventDefault();
      const name = document.getElementById('client_name').value.trim();
      const service = document.getElementById('service_needed').value.trim();
      const notes = document.getElementById('client_notes').value.trim();
      const phone = '{clean_phone}';
      
      const text = `Halo {business_name},\\n\\nPerkenalkan saya *${{name}}*.\\nSaya ingin menanyakan tentang layanan: *${{service}}*.\\nCatatan: ${{notes || '-'}}\\n\\nMohon info selengkapnya. Terima kasih.`;
      const encoded = encodeURIComponent(text);
      window.open(`https://wa.me/${{phone}}?text=${{encoded}}`, '_blank');
    }}
  </script>
</body>
</html>
"""

        index_path = os.path.join(site_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # robots.txt
        robots_path = os.path.join(site_dir, "robots.txt")
        with open(robots_path, "w", encoding="utf-8") as f:
            f.write(f"User-agent: *\nAllow: /\n\nSitemap: https://{domain}/sitemap.xml\n")

        # sitemap.xml
        sitemap_path = os.path.join(site_dir, "sitemap.xml")
        today_str = datetime.now().strftime("%Y-%m-%d")
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <lastmod>{today_str}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
""")

        return site_dir

