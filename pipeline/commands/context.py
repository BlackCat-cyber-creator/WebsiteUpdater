"""
Shared command execution context and dependency container.
Provides lazy-loaded access to pipeline services so commands only initialize what they need.
"""

import os
import sys
import subprocess
from typing import Optional


def execute_pipeline_for_client(url: str, output_dir: str, partner_info: Optional[dict] = None) -> bool:
    """Executes the complete 7-step website modernization pipeline as a subprocess."""
    print(f"\n[PIPELINE] Running modernization & proposal generation for: {url}")
    cmd = [
        sys.executable,
        "run_pipeline.py",
        "--url", url,
        "--output", output_dir
    ]
    if partner_info:
        cmd.append("--whitelabel")
        if partner_info.get("name"):
            cmd.extend(["--partner-name", partner_info["name"]])
        if partner_info.get("whatsapp"):
            cmd.extend(["--partner-wa", partner_info["whatsapp"]])
        if partner_info.get("logo"):
            cmd.extend(["--partner-logo", partner_info["logo"]])
        if partner_info.get("url"):
            cmd.extend(["--partner-url", partner_info["url"]])
    res = subprocess.run(cmd, capture_output=False)
    return res.returncode == 0


class CommandContext:
    """Lazy-loaded container for pipeline orchestrator services."""

    def __init__(self, is_live: bool = False):
        self.is_live = is_live
        self.dry_run = not is_live

        self._tracker = None
        self._scanner = None
        self._enricher = None
        self._email_disp = None
        self._wa_disp = None
        self._site_gen = None
        self._vercel_dep = None
        self._code_pkg = None
        self._pdf_gen = None
        self._pay_gw = None

    @property
    def tracker(self):
        if self._tracker is None:
            from pipeline.outreach.tracker import OutreachTracker
            self._tracker = OutreachTracker()
        return self._tracker

    @property
    def scanner(self):
        if self._scanner is None:
            from pipeline.scanner.business_scanner import IndonesianBusinessScanner
            self._scanner = IndonesianBusinessScanner()
        return self._scanner

    @property
    def enricher(self):
        if self._enricher is None:
            from pipeline.scanner.agent_reach_enricher import AgentReachContactEnricher
            self._enricher = AgentReachContactEnricher()
        return self._enricher

    @property
    def email_disp(self):
        if self._email_disp is None:
            from pipeline.outreach.email_dispatcher import EmailDispatcher
            self._email_disp = EmailDispatcher()
        return self._email_disp

    @property
    def wa_disp(self):
        if self._wa_disp is None:
            from pipeline.outreach.whatsapp_dispatcher import WhatsAppDispatcher
            self._wa_disp = WhatsAppDispatcher()
        return self._wa_disp

    @property
    def site_gen(self):
        if self._site_gen is None:
            from pipeline.site_generator import SiteGenerator
            self._site_gen = SiteGenerator()
        return self._site_gen

    @property
    def vercel_dep(self):
        if self._vercel_dep is None:
            from pipeline.deployer.vercel_deployer import VercelDeployer
            self._vercel_dep = VercelDeployer()
        return self._vercel_dep

    @property
    def code_pkg(self):
        if self._code_pkg is None:
            from pipeline.delivery.code_packager import CodePackager
            self._code_pkg = CodePackager()
        return self._code_pkg

    @property
    def pdf_gen(self):
        if self._pdf_gen is None:
            from pipeline.pdf_generator import ProposalPdfGenerator
            self._pdf_gen = ProposalPdfGenerator()
        return self._pdf_gen

    @property
    def pay_gw(self):
        if self._pay_gw is None:
            from pipeline.payment.payment_gateway import PaymentGateway
            self._pay_gw = PaymentGateway()
        return self._pay_gw
