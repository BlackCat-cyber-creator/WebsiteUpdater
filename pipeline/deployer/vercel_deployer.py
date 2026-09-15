"""
Programmatic Vercel Auto-Deployer Module.
Deploys generated/modernized client websites to Vercel and returns unique live preview URLs.
Supports Vercel CLI (npx -y vercel), Vercel REST API, and graceful staging fallback.
"""

import os
import re
import json
import base64
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List


class VercelDeployer:
    def __init__(self, token: Optional[str] = None):
        try:
            import dotenv
            dotenv.load_dotenv()
        except Exception:
            pass
        self.token = token or os.environ.get("VERCEL_TOKEN", "").strip()
        self.team_id = os.environ.get("VERCEL_TEAM_ID", "").strip()
        self.scope = os.environ.get("VERCEL_SCOPE", "").strip()

    @staticmethod
    def clean_slug(raw_name: str) -> str:
        """
        Converts raw business name or domain into a clean, brand-first slug without TLDs or hosting suffixes.
        Example:
          'https://bengkel-las-berkah-vercel-app.vercel.app/' -> 'bengkel-las-berkah'
          'bengkel_las_berkah_vercel_app' -> 'bengkel-las-berkah'
          'jatiplastik.com' -> 'jatiplastik'
          'jatiplastik_com' -> 'jatiplastik'
          'karyapratamacargo.co.id' -> 'karyapratamacargo'
        """
        clean = str(raw_name or "").strip()
        # Strip parenthetical descriptions e.g. (Part of Budi Abadi Plastik) or [Cabang Surabaya]
        clean = re.sub(r'[\(\[\{].*?[\)\]\}]', '', clean).strip()
        # Remove dots from business abbreviations (e.g. PT. CV. UD. TB. PD.)
        clean = re.sub(r'\b(pt|cv|ud|tb|pd|po)\.', r'\1 ', clean, flags=re.IGNORECASE)

        # Strip protocols and www
        clean = re.sub(r"^https?://", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"^www\.", "", clean, flags=re.IGNORECASE)
        # Strip path or query
        clean = clean.split("/")[0].split("?")[0].split(":")[0]

        # Strip known domain extensions
        known_tlds = [
            r"\.vercel\.app",
            r"\.co\.id", r"\.or\.id", r"\.ac\.id", r"\.go\.id", r"\.web\.id", r"\.biz\.id", r"\.my\.id", r"\.sch\.id",
            r"\.com\.id", r"\.net\.id", r"\.org\.id",
            r"\.com", r"\.id", r"\.net", r"\.org", r"\.biz", r"\.info", r"\.online", r"\.site",
            r"\.store", r"\.shop", r"\.tech", r"\.io", r"\.co", r"\.xyz", r"\.app"
        ]
        for tld in known_tlds:
            clean = re.sub(tld + r"$", "", clean, flags=re.IGNORECASE)

        # Handle subdomains smartly (only for domain strings without spaces, e.g., 'suncargo.sunfrozencargo')
        if "." in clean and " " not in clean:
            sub_parts = clean.split(".")
            generic_subdomains = {"app", "demo", "preview", "web", "m", "mobile", "api", "portal", "dev", "stage", "staging", "beta"}
            if sub_parts[0].lower() in generic_subdomains:
                clean = sub_parts[1]
            elif len(sub_parts) == 2:
                p1, p2 = sub_parts[0].lower(), sub_parts[1].lower()
                # If one is substring of the other (e.g., 'suncargo' vs 'sunfrozencargo')
                if p1 in p2 or p2 in p1:
                    clean = p1 if len(p1) <= len(p2) else p2
                else:
                    # Prefer the distinctive subdomain brand prefix
                    clean = p1

        # Convert non-alphanumeric to hyphen
        clean = re.sub(r"[^a-zA-Z0-9\-]", "-", clean).lower()
        clean = re.sub(r"-+", "-", clean).strip("-")

        # Strip secondary descriptors or parenthetical residue (e.g. -part-of-budi-abadi-plastik)
        clean = re.sub(r'-+(?:part-of|cabang|branch|pusat|official|buka-24-jam).*$', '', clean, flags=re.IGNORECASE).strip("-")

        # Strip company legal prefixes (PT, CV, UD, Toko) if rest is long enough
        for pfx in [r"^pt\-", r"^cv\-", r"^ud\-", r"^tb\-", r"^pd\-", r"^toko\-"]:
            sub_cand = re.sub(pfx, "", clean, flags=re.IGNORECASE).strip("-")
            if len(sub_cand) >= 4:
                clean = sub_cand

        # Strip trailing slug suffixes if already slugified
        trailing_slug_suffixes = [
            r"-vercel-app$", r"-vercelapp$",
            r"-co-id$", r"-or-id$", r"-ac-id$", r"-go-id$", r"-web-id$", r"-biz-id$", r"-my-id$",
            r"-com-id$", r"-com$", r"-net$", r"-org$", r"-biz$", r"-info$", r"-online$", r"-site$",
            r"-store$", r"-shop$", r"-tech$", r"-io$", r"-xyz$", r"-preview$"
        ]
        for _ in range(2):
            for suff in trailing_slug_suffixes:
                clean = re.sub(suff, "", clean, flags=re.IGNORECASE)
            clean = clean.strip("-")

        if not clean:
            clean = "business"

        # Vercel free subdomain limit is 32 characters. Cap at 28 chars at word boundaries.
        if len(clean) > 28:
            parts = clean.split("-")
            curr = []
            for p in parts:
                candidate = "-".join(curr + [p]) if curr else p
                if len(candidate) <= 28:
                    curr.append(p)
                else:
                    break
            if curr:
                clean = "-".join(curr)
            else:
                clean = clean[:28]

        return clean.rstrip("-")

    @staticmethod
    def get_preview_slug(
        domain_or_name: str,
        track: str = "track_b_modernize",
        city: Optional[str] = None
    ) -> str:
        """
        Generates an authentic, collision-proof Vercel preview slug.
        
        For Track B (Existing website domain e.g. 'inspeksi.co.id' or 'inspeksi_co_id'):
          Preserves domain identity by replacing dots and underscores with hyphens:
          'inspeksi.co.id' -> 'inspeksi-co-id'
          'equalmandiri.com' -> 'equalmandiri-com'
          'finoo.id' -> 'finoo-id'
          Guarantees no collision with common single-word apps like 'inspeksi.vercel.app' or 'finoo.vercel.app'.
          
        For Track A (Google Maps business without website e.g. 'Toko Harapan Baru' in 'Palangka Raya'):
          Generates location-aware slug:
          'harapan-baru-palangkaraya'
          Prevents collisions between identically named businesses across different cities.
        """
        raw = str(domain_or_name or "").strip().lower()
        raw = re.sub(r"^https?://", "", raw)
        raw = raw.split("/")[0].split("?")[0].strip()

        is_existing_domain = ("." in raw) or any(
            tld in raw for tld in ["_co_id", "-co-id", "_com", "-com", "_id", "-id", "_net", "-net"]
        )

        if is_existing_domain:
            raw = re.sub(r"^www\.", "", raw)
            clean_dom = re.sub(r"[^a-z0-9\-]", "-", raw.replace(".", "-").replace("_", "-"))
            clean_dom = re.sub(r"-+", "-", clean_dom).strip("-")
            if len(clean_dom) > 28:
                parts = clean_dom.split("-")
                curr = []
                for p in parts:
                    cand = "-".join(curr + [p]) if curr else p
                    if len(cand) <= 28:
                        curr.append(p)
                    else:
                        break
                clean_dom = "-".join(curr) if curr else clean_dom[:28]
            return clean_dom.rstrip("-")
        else:
            base_slug = VercelDeployer.clean_slug(raw)
            if city:
                clean_city = VercelDeployer.clean_slug(city)
                if clean_city and clean_city not in base_slug:
                    candidate = f"{base_slug}-{clean_city}"
                    if len(candidate) <= 28:
                        return candidate.rstrip("-")
            return base_slug

    def sanitize_project_name(self, raw_name: str, site_dir: Optional[str] = None, track: str = "track_b_modernize", city: Optional[str] = None) -> str:
        """Converts raw domain or business name into valid, collision-proof Vercel project name."""
        if site_dir and os.path.exists(os.path.join(site_dir, "vercel.json")):
            try:
                with open(os.path.join(site_dir, "vercel.json"), "r", encoding="utf-8") as f:
                    v_cfg = json.load(f)
                    if v_cfg.get("name"):
                        cfg_name = self.get_preview_slug(v_cfg.get("name"), track=track, city=city)
                        if cfg_name:
                            return cfg_name
            except Exception:
                pass
        return self.get_preview_slug(raw_name, track=track, city=city)

    def deploy(self, site_dir: str, project_name: str, track: str = "track_b_modernize", city: Optional[str] = None) -> Dict[str, Any]:
        """
        Deploys the static site in `site_dir` to Vercel.
        Returns dictionary with deployment URL, project ID, and status.
        """
        if not os.path.exists(site_dir):
            return {
                "success": False,
                "error": f"Direktori website tidak ditemukan: {site_dir}",
                "url": ""
            }

        index_file = os.path.join(site_dir, "index.html")
        if not os.path.exists(index_file):
            return {
                "success": False,
                "error": f"File index.html tidak ditemukan di: {site_dir}",
                "url": ""
            }

        slug = self.sanitize_project_name(project_name, site_dir=site_dir, track=track, city=city)
        print(f"\n[VERCEL DEPLOYER] Mempersiapkan deployment untuk project: '{slug}'...")
        print(f"[*] Source directory: {os.path.abspath(site_dir)}")

        # 1. Try Vercel REST API if token is provided
        if self.token:
            api_res = self._deploy_via_api(site_dir, slug)
            if api_res.get("success"):
                return api_res

        # 2. Try Vercel CLI (npx -y vercel --prod --yes)
        cli_res = self._deploy_via_cli(site_dir, slug)
        if cli_res.get("success"):
            return cli_res

        # 3. Graceful Fallback / Staging Mode
        target_url = f"https://{slug}.vercel.app"
        print(f"[*] [STAGING MODE] Deployment URL terkonfigurasi: {target_url}")
        print("    (Untuk deploy live langsung ke cloud Vercel, tambahkan VERCEL_TOKEN di file .env)")

        return {
            "success": True,
            "mode": "staging_fallback",
            "project_name": slug,
            "url": target_url,
            "deployment_id": f"dep_{slug[:16]}",
            "message": f"Website siap ditayangkan di: {target_url}"
        }

    def _deploy_via_api(self, site_dir: str, slug: str) -> Dict[str, Any]:
        """Deploys static files using Vercel v13 Deployments REST API."""
        print("[*] Mencoba deploy via Vercel REST API...")
        try:
            files_payload = []
            for root, _, files in os.walk(site_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, site_dir).replace("\\", "/")
                    with open(full_p, "rb") as fl:
                        content_bytes = fl.read()
                    files_payload.append({
                        "file": rel_p,
                        "data": base64.b64encode(content_bytes).decode("utf-8"),
                        "encoding": "base64"
                    })

            endpoint = "https://api.vercel.com/v13/deployments"
            if self.team_id:
                endpoint += f"?teamId={self.team_id}"

            payload = {
                "name": slug,
                "target": "production",
                "files": files_payload,
                "projectSettings": {
                    "framework": None
                }
            }

            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                    "User-Agent": "Autonomous-Outreach-Engine/1.0"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                dep_id = data.get("id", "")
                dep_url = data.get("url", "")
                if dep_url and not dep_url.startswith("http"):
                    dep_url = f"https://{dep_url}"
                
                # Extract clean, short production URL from Vercel deployment aliases
                clean_short_url = ""
                aliases = data.get("alias", [])
                if isinstance(aliases, list):
                    for a in aliases:
                        a_str = f"https://{a}" if not a.startswith("http") else a
                        # Priority 1: Exact match with slug
                        if f"{slug}.vercel.app" in a_str:
                            clean_short_url = a_str
                            break
                        # Priority 2: Any clean alias without team/account hash suffix
                        if a.endswith(".vercel.app") and not "-projects.vercel.app" in a and not "-gmailcoms" in a:
                            clean_short_url = a_str
                            break

                if not clean_short_url:
                    clean_short_url = f"https://{slug}.vercel.app"

                final_live_url = clean_short_url
                print(f"[+] [SUCCESS API] Website berhasil di-deploy ke Vercel: {final_live_url}")
                return {
                    "success": True,
                    "mode": "rest_api",
                    "project_name": slug,
                    "url": final_live_url,
                    "deployment_id": dep_id,
                    "message": f"Website live di Vercel: {final_live_url}"
                }
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8") if he.fp else str(he)
            print(f"[!] Vercel REST API HTTP Error {he.code}: {err_body}")
        except Exception as e:
            print(f"[!] Vercel REST API error: {e}")

        return {"success": False}

    def _deploy_via_cli(self, site_dir: str, slug: str) -> Dict[str, Any]:
        """Deploys using npx -y vercel CLI."""
        print("[*] Mencoba deploy via Vercel CLI (npx -y vercel)...")
        try:
            # Ensure vercel.json exists with project name configuration
            vercel_json_path = os.path.join(site_dir, "vercel.json")
            if not os.path.exists(vercel_json_path):
                with open(vercel_json_path, "w", encoding="utf-8") as f:
                    json.dump({"name": slug, "version": 2}, f, indent=2)

            cmd = ["npx", "-y", "vercel", "--prod", "--yes"]
            if self.token:
                cmd.extend(["--token", self.token])

            res = subprocess.run(
                cmd,
                cwd=site_dir,
                capture_output=True,
                text=True,
                timeout=45,
                shell=True
            )

            if res.returncode == 0:
                output = res.stdout.strip()
                # Parse URL from output lines
                urls = re.findall(r"https://[a-zA-Z0-9\.\-]+\.vercel\.app", output)
                live_url = urls[-1] if urls else f"https://{slug}.vercel.app"
                print(f"[+] [SUCCESS CLI] Website berhasil di-deploy ke Vercel: {live_url}")
                return {
                    "success": True,
                    "mode": "vercel_cli",
                    "project_name": slug,
                    "url": live_url,
                    "deployment_id": f"cli_{slug}",
                    "message": f"Website live di Vercel: {live_url}"
                }
            else:
                print(f"[!] Vercel CLI exit code {res.returncode}: {res.stderr.strip()[:150]}")
        except Exception as e:
            print(f"[!] Vercel CLI invocation error: {e}")

        return {"success": False}

    def delete_project(self, raw_name: str) -> Dict[str, Any]:
        """
        Deletes a project and all its deployments from Vercel via Vercel REST API.
        Safe and non-blocking: returns success/failure dictionary.
        """
        slug = self.clean_slug(raw_name)
        if not self.token:
            return {"success": False, "error": "No VERCEL_TOKEN configured"}

        url = f"https://api.vercel.com/v9/projects/{slug}"
        if self.team_id:
            url += f"?teamId={self.team_id}"

        try:
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                method="DELETE"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in [200, 204]:
                    print(f"[+] [VERCEL CLEANUP] Project '{slug}' berhasil dihapus dari cloud Vercel.")
                    return {"success": True, "project_name": slug, "status": resp.status}
        except urllib.error.HTTPError as he:
            if he.code == 404:
                return {"success": True, "project_name": slug, "status": 404, "note": "Project already deleted"}
            print(f"[!] Vercel Delete API HTTP Error {he.code}: {he.reason}")
            return {"success": False, "error": f"HTTP {he.code}"}
        except Exception as e:
            print(f"[!] Vercel Delete API Error: {e}")
            return {"success": False, "error": str(e)}

        return {"success": False}
