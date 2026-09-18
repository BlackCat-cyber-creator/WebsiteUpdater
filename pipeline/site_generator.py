"""
Client Website Preserver & SEO Optimization Engine.
Takes the client's authentic website, preserves 100% of their theme, colors,
layout, and branding, and performs professional tidying and technical SEO enhancements.
"""

import os
import re
import json
import html
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from pipeline.deployer.vercel_deployer import VercelDeployer
from pipeline.researcher.business_researcher import BusinessResearcher
from pipeline.researcher.ui_ux_integrator import UIUXProMaxIntegrator
from pipeline.outreach.meta_wa_client import normalize_phone_e164


from pipeline.templates.renderer import render_template

# Load industry themes from external JSON data
_THEMES_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "data", "niche_themes.json"))
try:
    with open(_THEMES_PATH, "r", encoding="utf-8") as _tf:
        NICHE_THEMES = json.load(_tf)
except Exception:
    NICHE_THEMES = {}

class SiteGenerator:
    def __init__(self):
        pass

    @staticmethod
    def _resolve_card_image(niche_key: str, title: str) -> Optional[str]:
        """Resolves authentic, appetizing category visuals for consumer & F&B niches."""
        t_low = title.lower()
        if niche_key == "frozen_food":
            if any(w in t_low for w in ["daging", "sosis", "bakso", "beef", "burger"]):
                return "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80"
            if any(w in t_low for w in ["seafood", "ikan", "udang", "dimsum", "dumpling", "siomay", "tempura"]):
                return "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=600&auto=format&fit=crop&q=80"
            if any(w in t_low for w in ["kentang", "sayur", "fries", "potato", "vegetable"]):
                return "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=600&auto=format&fit=crop&q=80"
            if any(w in t_low for w in ["keju", "dairy", "mozzarella", "cheese", "mentega"]):
                return "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=600&auto=format&fit=crop&q=80"
            if any(w in t_low for w in ["nugget", "camilan", "snack", "pastry", "katsu", "kebab", "maryam"]):
                return "https://images.unsplash.com/photo-1562967914-608f82629710?w=600&auto=format&fit=crop&q=80"
            if any(w in t_low for w in ["bumbu", "saus", "sauce", "mayo", "sambal"]):
                return "https://images.unsplash.com/photo-1472476443507-c7a5948772fc?w=600&auto=format&fit=crop&q=80"
            return "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80"
        elif niche_key == "kuliner":
            if any(w in t_low for w in ["roti", "bakery", "pastry", "croissant"]):
                return "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&auto=format&fit=crop&q=80"
            if any(w in t_low for w in ["kue", "cake", "tart", "brownies"]):
                return "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&auto=format&fit=crop&q=80"
            if any(w in t_low for w in ["katering", "nasi", "tumpeng", "prasmanan", "ayam"]):
                return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"
            return "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"
        return None

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
        if base_url.startswith("http://"):
            base_url = "https://" + base_url[7:]

        domain = scraped.get("domain") or urllib.parse.urlparse(base_url).netloc.replace("www.", "")
        brand = scraped.get("brand_name") or scraped.get("name") or (domain.split(".")[0].capitalize() if domain else "Perusahaan")
        # Detect SPA or hollow DOM (pages relying on client JS that break statically)
        is_spa_or_broken = any(k in raw_html for k in ["data-capo", "__NUXT__", "__NEXT_DATA__", "react-root", "_next/static"])
        soup_test = BeautifulSoup(raw_html, "html.parser") if raw_html else None
        body_text_len = len(soup_test.body.get_text().strip()) if (soup_test and soup_test.body) else 0
        if body_text_len < 120:
            is_spa_or_broken = True

        if raw_html and len(raw_html.strip()) > 100 and not is_spa_or_broken:
            cleaned_html = self._preserve_and_optimize_seo(raw_html, base_url, domain, brand, scraped, audit)
        else:
            # Fallback to authentic rich turnkey generator with client's actual trade intelligence
            phone = scraped.get("kontak", {}).get("whatsapp") or scraped.get("kontak", {}).get("phone", "")
            address = scraped.get("kontak", {}).get("address", "")
            cat_name = ""
            if scraped.get("layanan") and isinstance(scraped["layanan"], list) and len(scraped["layanan"]) > 0:
                cat_name = scraped["layanan"][0].get("title", "")
            return self.generate_turnkey_site(
                business_name=brand,
                category=cat_name,
                phone=phone,
                address=address,
                output_dir=output_dir
            )

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

        # 4. Generate vercel.json for Edge delivery and Clean URLs
        vercel_cfg_path = os.path.join(site_dir, "vercel.json")
        with open(vercel_cfg_path, "w", encoding="utf-8") as f:
            json.dump({
                "name": VercelDeployer.get_preview_slug(domain, track="track_b_modernize"),
                "version": 2,
                "cleanUrls": True,
                "headers": [
                    {
                        "source": "/(.*)",
                        "headers": [
                            {"key": "X-Content-Type-Options", "value": "nosniff"},
                            {"key": "X-Frame-Options", "value": "DENY"},
                            {"key": "X-XSS-Protection", "value": "1; mode=block"},
                            {"key": "Content-Security-Policy", "value": "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; script-src 'self' https: 'unsafe-inline' 'unsafe-eval'; style-src 'self' https: 'unsafe-inline'; font-src 'self' https: data:; img-src 'self' https: data: blob:;"}
                        ]
                    }
                ]
            }, f, indent=2)

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
        # 1. TIDY UP: Resolve all relative URLs to absolute and upgrade to HTTPS
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
                        if val and isinstance(val, str):
                            if not val.startswith(
                                ("http://", "https://", "data:", "mailto:", "tel:", "#", "javascript:")
                            ):
                                tag[attr] = urllib.parse.urljoin(base_url, val)
                            elif val.startswith("http://"):
                                # Upgrade to https to prevent mixed active content block on Vercel
                                tag[attr] = "https://" + val[7:]

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
                        elif img_url.startswith("http://"):
                            img_url = "https://" + img_url[7:]
                        if len(tokens) > 1:
                            new_parts.append(f"{img_url} {tokens[1]}")
                        else:
                            new_parts.append(img_url)
                    tag["srcset"] = ", ".join(new_parts)

        # Resolve relative url(...) in all <style> tags and inline style attributes to absolute HTTPS
        def _rewrite_css_urls(css_text: str) -> str:
            if not css_text or "url(" not in css_text:
                return css_text
            def _replace_url(match):
                raw_u = match.group(1).strip("'\" \t\r\n")
                if not raw_u or raw_u.startswith(("http://", "https://", "data:", "#")):
                    return match.group(0)
                abs_u = urllib.parse.urljoin(base_url, raw_u)
                if abs_u.startswith("http://"):
                    abs_u = "https://" + abs_u[7:]
                return f'url("{abs_u}")'
            return re.sub(r'url\s*\(\s*([^)]+)\s*\)', _replace_url, css_text)

        for s_tag in soup.find_all("style"):
            if s_tag.string:
                s_tag.string = _rewrite_css_urls(s_tag.string)

        for el in soup.find_all(attrs={"style": True}):
            el["style"] = _rewrite_css_urls(el["style"])

        # Tidy up empty or missing img alt tags for SEO image ranking
        # and inject Core Web Vitals optimizations (loading=lazy, decoding=async)
        for idx, img in enumerate(soup.find_all("img")):
            if not img.get("alt") or not img["alt"].strip():
                src = img.get("src", "")
                filename = os.path.basename(urllib.parse.urlparse(src).path) if src else ""
                clean_name = re.sub(r"[-_.]+", " ", filename).strip()
                img["alt"] = f"{brand} - {clean_name}" if clean_name else f"{brand} Layanan"

            # PageSpeed 95+ Core Web Vitals: Below-the-fold images get lazy load
            if idx > 1 and not img.has_attr("loading"):
                img["loading"] = "lazy"
            if not img.has_attr("decoding"):
                img["decoding"] = "async"

        # Optimize external scripts for sub-second First Contentful Paint (FCP)
        for s in soup.find_all("script"):
            src = s.get("src", "")
            if src and not s.has_attr("async") and not s.has_attr("defer"):
                if not any(crit in src.lower() for crit in ["polyfill", "require", "jquery"]):
                    s["defer"] = "true"

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
            services = scraped.get("layanan", [])
            svc_name = services[0].get("title") if services and services[0].get("title") else "Produk & Layanan"
            best_title = f"{brand} | Solusi {svc_name} Terpercaya di Indonesia"
        
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

        # Schema.org JSON-LD Structured Data: Clean up legacy Microdata & duplicate JSON-LD across document
        for old_sc in soup.find_all("script", attrs={"type": "application/ld+json"}):
            old_sc.decompose()
        for attr in ["itemscope", "itemtype", "itemprop"]:
            for item in soup.find_all(attrs={attr: True}):
                del item[attr]

        contact = scraped.get("kontak", {})
        raw_contact_ph = contact.get("whatsapp") or contact.get("phone", "")
        clean_contact_ph = f"+{normalize_phone_e164(raw_contact_ph)}" if raw_contact_ph else ""
        schema_data = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": brand,
            "url": base_url,
            "description": best_desc,
            "telephone": clean_contact_ph,
            "priceRange": "Rp",
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
        output_dir: str = "",
        partner_info: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generates an authentic, rich Swiss Minimalist single-page website backed by
        trade intelligence research for Track A businesses, ensuring the site has
        concrete services, narrative about us, advantages, and trade FAQs (tidak kopong).
        """
        site_dir = os.path.join(output_dir, "site")
        os.makedirs(site_dir, exist_ok=True)

        researcher = BusinessResearcher()
        city_extracted = researcher.extract_city(address, business_name)
        clean_slug = VercelDeployer.get_preview_slug(business_name, track="track_a_new_web", city=city_extracted)
        domain = f"{clean_slug}.vercel.app"
        clean_phone = normalize_phone_e164(phone) if phone else "628123456789"

        # Quick Trade Research & Semantic Synthesis
        profile = researcher.research_business(
            business_name=business_name,
            category=category,
            address=address,
            phone=phone,
            rating=rating,
            review_count=review_count
        )

        # Check authentic logo from assets
        has_logo = False
        site_assets_img = os.path.join(site_dir, "assets", "images")
        os.makedirs(site_assets_img, exist_ok=True)
        if output_dir:
            src_logo = os.path.join(output_dir, "assets", "logo.png")
            if os.path.exists(src_logo):
                import shutil
                try:
                    shutil.copy2(src_logo, os.path.join(site_assets_img, "logo.png"))
                    has_logo = True
                except Exception:
                    pass

        # Smart Monogram
        clean_biz = re.sub(r'^(PT\.?|CV\.?|TOKO\s+BANGUNAN|TOKO\s+BAHAN\s+BANGUNAN|TOKO|TB\.?|BENGKEL\s+LAS|BENGKEL|WARUNG|DISTRIBUTOR|KLINIK|APOTEK)\s+', '', business_name, flags=re.I).strip()
        parts = clean_biz.split()
        if len(parts) >= 2:
            monogram = (parts[0][0] + parts[1][0]).upper()
        elif len(parts) == 1 and len(parts[0]) >= 2:
            monogram = parts[0][:2].upper()
        else:
            monogram = business_name[:2].upper()

        logo_html = '<img src="assets/images/logo.png" alt="Logo" style="height: 42px; width: auto; object-fit: contain; border-radius: 8px;">' if has_logo else f'<div class="monogram">{monogram}</div>'

        rating_display = profile["rating_display"]
        reviews_display = profile["reviews_display"]
        headline = profile["headline"]
        tagline = profile["tagline"]
        trade_name = profile["trade_name"]
        city = profile["city"]
        about_p1 = profile["about_p1"]
        about_p2 = profile["about_p2"]
        hours = profile["operating_hours"]

        # Autonomous UI/UX Pro Max Intelligence Engine
        ui_ux = UIUXProMaxIntegrator()
        ds = ui_ux.resolve_design_system(business_name, category, profile.get("trade_name", ""))
        colors = ds["colors"]
        typo = ds["typography"]

        # Honest ratings via UI/UX Pro Max Sanitizer
        sanitized = profile.get("sanitized_ratings") or ui_ux.sanitize_ratings(rating, review_count)
        rating_display = sanitized["rating_display"]
        reviews_display = sanitized["reviews_display"]
        trust_badge_text = sanitized["trust_badge_text"]

        # Dynamic Color Theme & Industry Psychology
        niche_key = profile.get("niche_key", "modern_clean")
        raw_theme = NICHE_THEMES.get(niche_key, NICHE_THEMES.get("modern_clean", {}))
        theme = {}
        for tk, tv in raw_theme.items():
            if isinstance(tv, str):
                try:
                    theme[tk] = tv.format(city=city, business_name=business_name)
                except Exception:
                    theme[tk] = tv
            elif isinstance(tv, list):
                theme[tk] = [item.format(city=city, business_name=business_name) if isinstance(item, str) else item for item in tv]
            else:
                theme[tk] = tv

        # Apply WCAG AA color tokens from UI/UX Pro Max and Niche Themes
        # Prioritize raw_theme accents if explicitly configured for industry
        accent_color = raw_theme.get("accent") or colors["accent"]
        theme["accent"] = accent_color
        theme["accent_hover"] = raw_theme.get("accent_hover") or colors.get("accent_hover") or ui_ux._adjust_hex_brightness(accent_color, -0.15)
        theme["accent_light"] = raw_theme.get("accent_light") or colors.get("accent_light") or ui_ux._adjust_hex_tint(accent_color, 0.92)
        theme["accent_border"] = raw_theme.get("accent_border") or colors.get("accent_border") or ui_ux._adjust_hex_tint(accent_color, 0.70)
        theme["accent_dark"] = raw_theme.get("accent_dark") or colors.get("accent_dark") or ui_ux._adjust_hex_brightness(accent_color, -0.25)
        try:
            r = int(accent_color[1:3], 16)
            g = int(accent_color[3:5], 16)
            b = int(accent_color[5:7], 16)
            theme["accent_shadow"] = raw_theme.get("accent_shadow") or f"rgba({r}, {g}, {b}, 0.25)"
            theme["accent_rgb"] = f"{r}, {g}, {b}"
        except Exception:
            theme["accent_shadow"] = "rgba(14, 165, 233, 0.25)"
            theme["accent_rgb"] = "14, 165, 233"

        theme["primary"] = raw_theme.get("theme_color") or colors["primary"]
        theme["theme_color"] = raw_theme.get("theme_color") or accent_color
        theme["secondary"] = raw_theme.get("secondary") or colors["secondary"]
        theme["background"] = colors.get("background", "#f8fafc")
        theme["card"] = colors.get("card", "#ffffff")
        theme["border"] = colors.get("border", "#e2e8f0")
        theme["foreground"] = colors.get("foreground", "#0f172a")
        theme["muted_foreground"] = colors.get("muted_foreground", "#64748b")
        theme["ring"] = colors.get("ring", accent_color)
        theme["wa_green"] = colors["wa_green"]
        theme["wa_green_hover"] = colors["wa_green_hover"]
        theme["wa_green_light"] = colors["wa_green_light"]
        theme["wa_green_dark"] = colors["wa_green_dark"]
        theme["dark_bg"] = colors.get("dark_bg", "#090d16")
        theme["dark_surface"] = colors.get("dark_surface", "#111827")
        theme["dark_surface_subtle"] = colors.get("dark_surface_subtle", "#1e293b")
        theme["dark_border"] = colors.get("dark_border", "rgba(255, 255, 255, 0.08)")
        theme["dark_border_strong"] = colors.get("dark_border_strong", "rgba(255, 255, 255, 0.15)")
        theme["dark_foreground"] = colors.get("dark_foreground", "#f8fafc")
        theme["dark_muted_foreground"] = colors.get("dark_muted_foreground", "#94a3b8")
        theme["google_fonts_url"] = typo["google_fonts_url"]
        theme["heading_font"] = typo["heading_font"]
        theme["body_font"] = typo["body_font"]
        theme["motion_preset"] = ds.get("motion", {})

        # Clean city & address logic to prevent "Lokal & Sekitarnya & Sekitarnya"
        clean_city_name = re.sub(r'\s*&\s*sekitarnya\b', '', city, flags=re.I).strip()
        if not clean_city_name or clean_city_name.lower() in ["lokal", "wilayah", "seluruh"]:
            area_service_label = "Wilayah Layanan & Sekitarnya"
            footer_city_display = "Seluruh Wilayah Layanan, Indonesia"
        else:
            area_service_label = f"Area {clean_city_name} & Sekitarnya"
            footer_city_display = f"Kota {clean_city_name}, Indonesia"

        if address and address.strip():
            addr_str = address.strip()
            if re.match(r'^melayani\b', addr_str, re.I):
                clean_address_display = addr_str
            elif any(w in addr_str.lower() for w in ["jl.", "jalan", "komplek", "ruko", "blok", "no.", "rt/rw"]):
                clean_address_display = addr_str
            else:
                clean_address_display = f"Melayani {addr_str}"
        else:
            clean_address_display = f"Melayani {area_service_label}"

        # Highlight city in headline if present
        h1_html = headline
        if city and city in headline:
            h1_html = headline.replace(city, f'<span class="highlight">{city}</span>')

        # SVG Icons from UI/UX Pro Max Vector Engine
        wa_svg = ui_ux.get_svg_icon("whatsapp", size=18, cls="ui-svg")
        map_pin_svg = ui_ux.get_svg_icon("map-pin", size=15, cls="ui-svg")
        phone_svg = ui_ux.get_svg_icon("phone", size=15, cls="ui-svg")
        truck_svg = ui_ux.get_svg_icon("truck", size=15, cls="ui-svg")
        clock_svg = ui_ux.get_svg_icon("clock", size=15, cls="ui-svg")
        help_svg = ui_ux.get_svg_icon("help-circle", size=18, cls="faq-svg")
        check_svg = ui_ux.get_svg_icon("check", size=14, cls="bullet-svg")
        sun_svg = ui_ux.get_svg_icon("sun", size=18, cls="theme-toggle-icon sun-icon")
        moon_svg = ui_ux.get_svg_icon("moon", size=18, cls="theme-toggle-icon moon-icon")
        search_svg = ui_ux.get_svg_icon("search", size=16, cls="search-svg")
        filter_svg = ui_ux.get_svg_icon("filter", size=14, cls="filter-svg")
        sparkles_svg = ui_ux.get_svg_icon("sparkles", size=16, cls="ui-svg")

        # 1. Top Utility Notice Bar (Vector SVG, Zero Emojis)
        top_bar_html = f"""
  <!-- Top Utility Notice Bar -->
  <div class="top-bar">
    <div class="container top-bar-inner">
      <div class="top-bar-item">
        <span class="top-icon">{map_pin_svg}</span> <span>{clean_address_display} | Buka {hours}</span>
      </div>
      <div class="top-bar-item">
        <span class="top-icon">{truck_svg if niche_key in ['frozen_food', 'kuliner', 'konstruksi', 'logistik_kargo'] else phone_svg}</span> <span>{theme.get("top_bar_label", "Layanan Cepat")}: <a href="tel:{clean_phone}">{phone}</a></span>
      </div>
    </div>
  </div>"""

        # 2. Key Metrics Bar (Intelligent Niche-Aware Fallback)
        default_lbl_2 = "Produk & Layanan Resmi"
        default_lbl_3 = "Standar Mutu Teruji"
        default_lbl_4 = f"Area Layanan {city}"
        if niche_key in ["layanan_profesional"]:
            default_lbl_2 = "Kerahasiaan Terjamin (NDA)"
            default_lbl_3 = "Tim Ahli Berlisensi"
            default_lbl_4 = "Konsultasi Cepat"
        elif niche_key in ["kesehatan", "fisioterapi_klinik"]:
            default_lbl_2 = "Tenaga Medis Berlisensi"
            default_lbl_3 = "Higienis & Terstandar"
            default_lbl_4 = f"Siap Melayani Warga {city}"
        elif niche_key in ["edukasi"]:
            default_lbl_2 = "Kurikulum & Modul Teruji"
            default_lbl_3 = "Tutor Berpengalaman"
            default_lbl_4 = "Kelas Interaktif"
        elif niche_key in ["logistik_kargo"]:
            default_lbl_2 = "Armada Sendiri Terawat"
            default_lbl_3 = "Jaminan Asuransi Muatan"
            default_lbl_4 = "Jangkauan Antarkota"
        elif niche_key in ["jasa_teknik"]:
            default_lbl_2 = "Teknisi Berpengalaman"
            default_lbl_3 = "Garansi Pengerjaan"
            default_lbl_4 = f"Panggilan Cepat Area {city}"
        elif niche_key in ["properti"]:
            default_lbl_2 = "Legalitas SHM Aman"
            default_lbl_3 = "Lokasi Bernilai Tinggi"
            default_lbl_4 = "Survey Lokasi Fleksibel"
        elif niche_key in ["frozen_food", "kuliner"]:
            default_lbl_2 = "100% Halal & Segar"
            default_lbl_3 = "Kualitas Rasa Higienis"
            default_lbl_4 = f"Kirim Cepat Area {city}"
        elif niche_key in ["konstruksi"]:
            default_lbl_2 = "Material Standar SNI"
            default_lbl_3 = "Stok Gudang Siap Kirim"
            default_lbl_4 = "Armada Angkut Proyek"

        metrics = profile.get("metrics") or [
            {"val": f"{rating_display} ★", "lbl": "Google Maps Terverifikasi"},
            {"val": "100% Asli", "lbl": default_lbl_2},
            {"val": "Resmi", "lbl": default_lbl_3},
            {"val": "Terpercaya", "lbl": default_lbl_4}
        ]
        metrics_bar_items = "".join([f"""
          <div class="metric-item">
            <div class="metric-val">{m['val']}</div>
            <div class="metric-lbl">{m['lbl']}</div>
          </div>""" for m in metrics[:4]])
        metrics_bar_html = f"""
        <div class="metrics-bar">
          {metrics_bar_items}
        </div>"""

        # 3. Rich Catalog Cards with bullet items, search attributes & dual action buttons
        catalog_cards_html = ""
        structured_catalog = []
        badge_labels = theme.get("badge_labels", [
            "100% Asli & Teruji",
            "Kualitas Terbaik",
            "Stok Siap",
            "Standar Mutu",
            "Pilihan Favorit",
            "Layanan Profesional"
        ])
        categories = []
        for idx, s in enumerate(profile.get("services", [])):
            stitle = s.get("title", "Layanan")
            sdesc = s.get("desc", "")
            sbadge = badge_labels[idx % len(badge_labels)]
            sicon_svg = ui_ux.resolve_catalog_icon(stitle, s.get("icon", ""))
            if niche_key in ["frozen_food", "konstruksi", "kuliner", "flora_fauna"]:
                item_1 = f"{stitle} Grade A Teruji"
                item_2 = f"Ketersediaan Pasokan & Stok {city}"
            elif niche_key in ["kesehatan", "fisioterapi_klinik"]:
                item_1 = f"Standar Klinis {stitle} Resmi"
                item_2 = f"Fasilitas Higienis & Steril {city}"
            elif niche_key in ["layanan_profesional"]:
                item_1 = f"Konsultasi {stitle} Berlisensi"
                item_2 = f"Kerahasiaan & Standar Etika Profesi"
            elif niche_key in ["jasa_teknik"]:
                item_1 = f"Pengerjaan {stitle} Bergaransi"
                item_2 = f"Teknisi Berpengalaman Area {city}"
            elif niche_key in ["edukasi"]:
                item_1 = f"Kurikulum {stitle} Teruji"
                item_2 = f"Pendampingan Tutor Berpengalaman"
            elif niche_key in ["logistik_kargo"]:
                item_1 = f"Layanan {stitle} Terjadwal"
                item_2 = f"Jaminan Asuransi & Lacak Kiriman"
            elif niche_key in ["estetika"]:
                item_1 = f"Treatment {stitle} Steril"
                item_2 = f"Terapis Berpengalaman & Bersertifikat"
            elif niche_key in ["otomotif"]:
                item_1 = f"Servis {stitle} Standar Pabrikan"
                item_2 = f"Suku Cadang Teruji Area {city}"
            elif niche_key in ["properti"]:
                item_1 = f"Unit {stitle} Lokasi Strategis"
                item_2 = f"Legalitas Aman & Bebas Sengketa"
            else:
                item_1 = f"Layanan {stitle} Terstandar"
                item_2 = f"Pelayanan Profesional Area {city}"

            items = s.get("items") or [
                item_1,
                item_2,
                "Konsultasi & Garansi Kepuasan"
            ]
            items_html = "".join([f'<li><span class="bullet">{check_svg}</span> {item}</li>' for item in items])
            
            prompt_template = theme.get("card_wa_prompt_template")
            if prompt_template:
                card_wa_prompt = prompt_template.replace("{business_name}", business_name).replace("{title}", stitle).replace("{city}", city)
            elif niche_key in ["frozen_food", "konstruksi", "kuliner", "flora_fauna"]:
                card_wa_prompt = (
                    f"Halo Manajemen {business_name},\n\n"
                    f"Saya tertarik dengan produk/layanan *{stitle}* dari katalog website resmi Anda.\n"
                    f"Boleh minta info spesifikasi, ketersediaan stok, dan penawaran harganya untuk area {city}? Terima kasih!"
                )
            else:
                card_wa_prompt = (
                    f"Halo Manajemen {business_name},\n\n"
                    f"Saya tertarik dengan layanan *{stitle}* dari website resmi Anda.\n"
                    f"Boleh minta info detail layanan, prosedur, dan penawaran biayanya untuk area {city}? Terima kasih!"
                )
            wa_text = urllib.parse.quote(card_wa_prompt)
            structured_catalog.append({
                "title": stitle,
                "desc": sdesc,
                "badge": sbadge,
                "items": items
            })
            if stitle not in categories:
                categories.append(stitle)
            escaped_stitle = html.escape(stitle, quote=True)
            card_img_url = self._resolve_card_image(niche_key, stitle)
            if card_img_url:
                card_fallback_url = "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80" if niche_key == "frozen_food" else "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80"
                card_img_html = (
                    f'<div class="catalog-card-image">'
                    f'<img src="{card_img_url}" alt="{escaped_stitle}" loading="lazy" decoding="async" '
                    f'width="600" height="338" style="aspect-ratio: 16 / 9;" '
                    f'onerror="this.onerror=null; this.src=\'{card_fallback_url}\'; this.onerror=function(){{this.style.opacity=\'0\'; this.parentElement.classList.add(\'img-fallback-active\');}}; ">'
                    f'<span class="card-glass-badge">{sbadge}</span>'
                    f'</div>'
                )
                header_html = f"""
          <div class="catalog-header-clean">
            <h3 class="catalog-title">{stitle}</h3>
          </div>"""
            else:
                card_img_html = ""
                header_html = f"""
          <div class="catalog-header">
            <div class="catalog-icon">{sicon_svg}</div>
            <div class="catalog-title-wrap">
              <h3 class="catalog-title">{stitle}</h3>
              <span class="catalog-badge">{sbadge}</span>
            </div>
          </div>"""

            catalog_cards_html += f"""
        <div class="catalog-card" data-category="{stitle.lower()}" data-search="{stitle.lower()} {sdesc.lower()} {' '.join(items).lower()}">
          {card_img_html}{header_html}
          <p class="catalog-desc">{sdesc}</p>
          <ul class="catalog-items">
            {items_html}
          </ul>
          <div class="catalog-card-footer">
            <a href="https://wa.me/{clean_phone}?text={wa_text}" target="_blank" rel="noopener noreferrer" class="btn-card-wa">
              <span>{theme.get("card_btn_text", "Pesan via WA ↗")}</span>
            </a>
            <button type="button" class="btn-card-estimate" data-service-title="{escaped_stitle}" onclick="selectServiceForEstimate(this.dataset.serviceTitle)">
              <span>{theme.get("card_estimate_btn", "Minta Estimasi ↓")}</span>
            </button>
          </div>
        </div>"""

        # Filter pills for catalog
        filter_pills_html = '<button type="button" class="filter-pill active" onclick="filterCatalog(\'all\', this)">Semua Kategori</button>'
        for cat in categories[:6]:
            cat_safe = cat.replace("'", "\\'").replace('"', '&quot;')
            filter_pills_html += f'<button type="button" class="filter-pill" onclick="filterCatalog(\'{cat.lower()}\', this)">{cat}</button>'

        # 4. Advantages Boxes (Vector SVGs)
        adv_boxes_html = ""
        for idx, a in enumerate(profile.get("advantages", [])):
            adv_svg = ui_ux.resolve_advantage_icon(idx)
            adv_boxes_html += f"""
        <div class="adv-box">
          <div class="adv-icon-badge">{adv_svg}</div>
          <div class="adv-content">
            <h4>{a['title']}</h4>
            <p>{a['desc']}</p>
          </div>
        </div>"""

        # 5. Reviews Section (Authentic Niche-Adaptive Fallback or Quality Commitment)
        has_real_reviews = bool(sanitized.get("has_real_reviews", False))
        reviews = profile.get("reviews") or []
        if has_real_reviews and reviews:
            reviews_cards_html = ""
            for r in reviews[:3]:
                rname = r.get("name", "Pelanggan Terverifikasi")
                # Robust initial extraction: strip non-alphanumeric chars (parentheses, brackets, symbols)
                clean_words = [re.sub(r'[^A-Za-z0-9]', '', w) for w in rname.split() if re.sub(r'[^A-Za-z0-9]', '', w)]
                if len(clean_words) >= 2:
                    rinitials = (clean_words[0][0] + clean_words[1][0]).upper()
                elif clean_words:
                    rinitials = clean_words[0][:2].upper()
                else:
                    rinitials = "PL"
                rbadge = r.get("badge", f"Pelanggan Google Maps {city}")
                rstars = r.get("stars", rating_display or "★★★★★")
                rtext = r.get("text", "")
                reviews_cards_html += f"""
        <div class="review-card">
          <div class="review-stars">{rstars}</div>
          <p class="review-text">"{rtext}"</p>
          <div class="reviewer-meta">
            <div class="reviewer-avatar">{rinitials}</div>
            <div>
              <span class="reviewer-name">{rname}</span>
              <span class="reviewer-badge">✓ {rbadge}</span>
            </div>
          </div>
        </div>"""

            # Niche-aware social proof description
            if niche_key in ["frozen_food", "kuliner"]:
                social_proof_desc = f"Dipercaya oleh pemilik resto, kafe, katering, dan pelanggan setia di {city} dengan reputasi terdaftar di Google Maps."
            elif niche_key in ["kesehatan", "fisioterapi_klinik", "estetika"]:
                social_proof_desc = f"Dipercaya oleh pasien, keluarga, dan pelanggan setia di {city} dengan reputasi terdaftar di Google Maps."
            elif niche_key in ["konstruksi", "jasa_teknik"]:
                social_proof_desc = f"Dipercaya oleh kontraktor, mandor, dan pemilik bangunan di {city} dengan reputasi terdaftar di Google Maps."
            else:
                social_proof_desc = f"Dipercaya oleh pelanggan dan mitra usaha di {city} dengan reputasi terdaftar di Google Maps."

            reviews_section_html = f"""
  <!-- Google Reviews & Social Proof -->
  <section id="ulasan" class="reviews-section">
    <div class="container">
      <div class="section-header">
        <span class="section-tag">BUKTI KEPUASAN PELANGGAN</span>
        <h2 class="section-title">Ulasan Pembeli di Google Maps</h2>
        <p class="section-desc">{social_proof_desc}</p>
      </div>
      <div class="reviews-grid">
        {reviews_cards_html}
      </div>
    </div>
  </section>"""
        else:
            # Honest Service Guarantee & Credibility Section (Niche-Aware & Leak-Free)
            guarantees = theme.get("review_guarantees") or [
                {"title": "Komitmen Mutu Terpercaya", "desc": f"Standar mutu dan pelayanan teruji untuk kepuasan pelanggan di {city}.", "badge": "Mutu Terjamin", "role": "Tim Mutu"},
                {"title": "Layanan Profesional & Cepat", "desc": "Kemudahan konsultasi dengan respon cepat dan penjelasan ramah terbuka.", "badge": "Respon Cepat", "role": "Customer Care"},
                {"title": "Kejujuran & Ketepatan Layanan", "desc": f"Dedikasi melayani seluruh pelanggan di {city} dengan amanah dan tepat waktu.", "badge": "Tepat Waktu", "role": "Operasional"}
            ]
            
            guarantee_cards_html = ""
            for g in guarantees[:3]:
                gtitle = g.get("title", "Standar Mutu")
                gdesc = g.get("desc", f"Layanan resmi terstandar bagi pelanggan di {city}.")
                gbadge = g.get("badge", "Kualitas Terjamin")
                grole = g.get("role", "Tim Layanan")
                gwords = [w for w in grole.split() if w]
                ginitial = (gwords[0][0] + (gwords[1][0] if len(gwords) > 1 else "")).upper()
                guarantee_cards_html += f"""
        <div class="review-card">
          <div class="review-stars">★★★★★</div>
          <p class="review-text">"{gdesc}"</p>
          <div class="reviewer-meta">
            <div class="reviewer-avatar">{ginitial}</div>
            <div>
              <span class="reviewer-name">{gtitle}</span>
              <span class="reviewer-badge">✓ {gbadge}</span>
            </div>
          </div>
        </div>"""

            reviews_section_html = f"""
  <!-- Service Commitment & Quality Assurance -->
  <section id="ulasan" class="reviews-section">
    <div class="container">
      <div class="section-header">
        <span class="section-tag">KOMITMEN LAYANAN RESMI</span>
        <h2 class="section-title">Standar Mutu & Kepuasan Pelanggan</h2>
        <p class="section-desc">Dedikasi memberikan layanan profesional, respon cepat, dan kepuasan penuh bagi pelanggan di {city}.</p>
      </div>
      <div class="reviews-grid">
        {guarantee_cards_html}
      </div>
    </div>
  </section>"""

        # 6. FAQs (Vector SVG)
        faqs_html = ""
        for f in profile.get("faqs", []):
            faqs_html += f"""
        <div class="faq-card">
          <div class="faq-q">{help_svg} <span>{f['q']}</span></div>
          <div class="faq-a">{f['a']}</div>
        </div>"""

        # 7. Form Dropdowns
        options_html = "".join([f'<option value="{opt}">{opt}</option>' for opt in profile["service_options"]])
        options_html += '<option value="Paket Campuran / Kebutuhan Komplit">Paket Campuran / Kebutuhan Komplit</option>'

        raw_area_options = theme.get("form_area_options")
        if raw_area_options and isinstance(raw_area_options, list):
            area_options = [opt.replace("{city}", city) for opt in raw_area_options]
        elif niche_key in ["konstruksi", "bengkel_las"]:
            area_options = [
                f"Area Pusat {city}",
                f"Area Sekitar {city}",
                f"Wilayah Penyangga / Titik Proyek",
                "Ambil Mandiri di Gudang"
            ]
        elif niche_key in ["frozen_food", "kuliner"]:
            area_options = [
                f"Area Pusat {city}",
                f"Area Sekitar {city}",
                f"Luar Kota / Ekspedisi Berpendingin",
                "Ambil Langsung di Toko / Outlet"
            ]
        elif niche_key in ["kesehatan", "fisioterapi_klinik"]:
            area_options = [
                f"Area Pusat {city}",
                f"Area Sekitar {city}",
                "Kunjungan / Datang ke Lokasi Pasien",
                "Datang Langsung ke Klinik"
            ]
        elif niche_key in ["layanan_profesional"]:
            area_options = [
                f"Area Pusat {city}",
                f"Area Sekitar {city}",
                "Pertemuan di Kantor Klien",
                "Konsultasi Daring / Online"
            ]
        elif niche_key in ["jasa_teknik"]:
            area_options = [
                f"Area Pusat {city}",
                f"Area Sekitar {city}",
                "Panggilan ke Rumah / Kantor",
                "Bawa Unit ke Workshop"
            ]
        else:
            area_options = [
                f"Area Pusat {city}",
                f"Area Sekitar {city}",
                f"Wilayah Sekitar {city}",
                "Layanan di Lokasi / Kantor"
            ]
        area_options_html = "".join([f'<option value="{area}">{area}</option>' for area in area_options])

        form_name_label = theme.get("form_name_label", "Nama Lengkap / Instansi")
        form_name_placeholder = theme.get("form_name_placeholder", "Contoh: Pak Anton / Ibu Maya")
        form_category_label = theme.get("form_category_label", "Kategori Kebutuhan Utama")
        form_area_label = theme.get("form_area_label", "Lokasi Pengiriman / Layanan")
        form_urgency_label = theme.get("form_urgency_label", "Jadwal Kebutuhan")
        urgency_options = theme.get("form_urgency_options") or [
            "Segera / Hari Ini",
            "Dalam 1-3 Hari Ini",
            "Jadwalkan Pekan Depan",
            "Tanya Estimasi / Konsultasi Dulu"
        ]
        urgency_options_html = "".join([f'<option value="{u}">{u}</option>' for u in urgency_options])
        form_notes_label = theme.get("form_notes_label", "Rincian Kebutuhan / Pertanyaan (Opsional)")
        form_notes_placeholder = theme.get("form_notes_placeholder", "Tuliskan produk atau layanan yang dicari, jumlah, atau pertanyaan spesifik lain...")
        form_submit_text = theme.get("form_submit_text", "Kirim Rincian ke WhatsApp Resmi ↗")

        hero_wa_text = urllib.parse.quote(
            f"Halo Manajemen {business_name},\n\n"
            f"Saya menemukan kontak Anda melalui website resmi ({clean_slug}.vercel.app).\n"
            f"Saya ingin berkonsultasi mengenai kebutuhan produk/layanan untuk wilayah {city}. Boleh minta info katalog & penawaran harga terbarunya? Terima kasih!"
        )

        # Structured Schema.org JSON-LD (Python Serialized for 100% Syntax & Type Safety)
        schema_dict = {
            "@context": "https://schema.org",
            "@type": theme.get("schema_type", "LocalBusiness"),
            "name": business_name,
            "description": headline,
            "url": f"https://{domain}",
            "telephone": f"+{clean_phone}" if clean_phone else "",
            "priceRange": "Rp",
            "openingHours": hours or "Mo-Sa 08:00-17:00",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": clean_address_display or address or "Indonesia",
                "addressLocality": city,
                "addressCountry": "ID"
            }
        }

        # Only inject aggregateRating if real rating and reviews exist (Google Search Essentials compliance)
        if sanitized.get("has_real_rating", False) and sanitized.get("has_real_reviews", False):
            schema_dict["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": f"{sanitized['rating_float']:.1f}",
                "reviewCount": str(sanitized["review_count_int"])
            }

        if structured_catalog:
            schema_dict["hasOfferCatalog"] = {
                "@type": "OfferCatalog",
                "name": f"Katalog Resmi {business_name}",
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "itemOffered": {
                            "@type": "Service",
                            "name": cat["title"],
                            "description": cat["desc"]
                        }
                    }
                    for cat in structured_catalog
                ]
            }

        schema_dict["creator"] = {
            "@type": "Organization",
            "name": "Website Updater Studio",
            "url": "https://websiteupdater.vercel.app"
        }

        schema_json_ld = json.dumps(schema_dict, indent=2, ensure_ascii=False)

        footer_area_icon_svg = truck_svg if niche_key in ['frozen_food', 'kuliner', 'konstruksi', 'logistik_kargo', 'flora_fauna'] else map_pin_svg
        footer_area_coverage_raw = theme.get("footer_area_coverage_template") or "Melayani kebutuhan dan pemesanan area {city} dan sekitarnya."
        footer_area_coverage = footer_area_coverage_raw.replace("{city}", city or "lokal")

        html_content = render_template(
            "site/turnkey.html",
            business_name=business_name,
            headline=headline,
            tagline=tagline,
            phone=phone,
            clean_phone=clean_phone,
            rating_display=rating_display,
            reviews_display=reviews_display,
            trust_badge_text=trust_badge_text,
            has_real_reviews=has_real_reviews,
            schema_json_ld=schema_json_ld,
            schema_rating_value=sanitized.get("schema_rating_value", "4.5"),
            schema_review_count=sanitized.get("schema_review_count", "50"),
            wa_svg=wa_svg,
            map_pin_svg=map_pin_svg,
            phone_svg=phone_svg,
            truck_svg=truck_svg,
            clock_svg=clock_svg,
            domain=domain,
            theme=theme,
            top_bar_html=top_bar_html,
            logo_html=logo_html,
            trade_name=trade_name,
            city=city,
            h1_html=h1_html,
            hero_wa_text=hero_wa_text,
            metrics_bar_html=metrics_bar_html,
            about_p1=about_p1,
            about_p2=about_p2,
            catalog_cards_html=catalog_cards_html,
            adv_boxes_html=adv_boxes_html,
            reviews_section_html=reviews_section_html,
            faqs_html=faqs_html,
            options_html=options_html,
            area_options_html=area_options_html,
            form_name_label=form_name_label,
            form_name_placeholder=form_name_placeholder,
            form_category_label=form_category_label,
            form_area_label=form_area_label,
            form_urgency_label=form_urgency_label,
            urgency_options_html=urgency_options_html,
            form_notes_label=form_notes_label,
            form_notes_placeholder=form_notes_placeholder,
            form_submit_text=form_submit_text,
            address=address,
            clean_address_display=clean_address_display,
            footer_city_display=footer_city_display,
            footer_area_icon_svg=footer_area_icon_svg,
            footer_area_coverage=footer_area_coverage,
            hours=hours,
            filter_pills_html=filter_pills_html,
            sun_svg=sun_svg,
            moon_svg=moon_svg,
            search_svg=search_svg,
            filter_svg=filter_svg,
            sparkles_svg=sparkles_svg,
            structured_catalog=structured_catalog
        )

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

        powered_by = f"{partner_info.get('name', 'Digital Agency')} Turn-Key Engine" if partner_info else "Website Updater Studio (websiteupdater.vercel.app)"
        vercel_cfg_path = os.path.join(site_dir, "vercel.json")
        with open(vercel_cfg_path, "w", encoding="utf-8") as f:
            json.dump({
                "name": clean_slug,
                "version": 2,
                "cleanUrls": True,
                "headers": [
                    {
                        "source": "/(.*)",
                        "headers": [
                            {"key": "X-Content-Type-Options", "value": "nosniff"},
                            {"key": "X-Frame-Options", "value": "DENY"},
                            {"key": "X-XSS-Protection", "value": "1; mode=block"},
                            {"key": "Content-Security-Policy", "value": "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; script-src 'self' https: 'unsafe-inline' 'unsafe-eval'; style-src 'self' https: 'unsafe-inline'; font-src 'self' https: data:; img-src 'self' https: data: blob:;"},
                            {"key": "X-Powered-By", "value": powered_by}
                        ]
                    }
                ]
            }, f, indent=2)

        return site_dir

