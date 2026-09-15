import os
import pytest
from pipeline.pdf_generator import ProposalPdfGenerator


def test_pdf_generator_browser_executable_detection():
    """Verify that ProposalPdfGenerator can detect system browser or PATH binaries."""
    gen = ProposalPdfGenerator()
    assert hasattr(gen, "_find_browser_executable")
    assert hasattr(gen, "_convert_html_to_pdf")
    assert len(gen.edge_paths) >= 8


def test_pdf_conversion_execution(tmp_path):
    """Verify HTML to PDF conversion using the new Playwright engine with fallback."""
    gen = ProposalPdfGenerator()
    html_file = tmp_path / "sample.html"
    pdf_file = tmp_path / "sample.pdf"

    html_file.write_text(
        "<!DOCTYPE html><html><body><h1>Proposal Test</h1><p>Testing PDF output generation.</p></body></html>",
        encoding="utf-8"
    )

    success = gen._convert_html_to_pdf(str(html_file), str(pdf_file))
    assert success is True
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 1000


def test_pdf_generate_track_b_and_flexible_signature(tmp_path):
    """Verify that ProposalPdfGenerator accepts client_dir and generates Track B proposal."""
    gen = ProposalPdfGenerator()
    lead = {
        "business_name": "PT Equal Mandiri Jaya",
        "domain": "equalmandiri.com",
        "website_url": "https://equalmandiri.com",
        "outdated_signals": ["WordPress 4.8", "No SSL"],
        "track": "track_b_modernize"
    }

    # Test flexible generate kwargs
    res = gen.generate(lead, client_dir=str(tmp_path))
    assert isinstance(res, dict)
    assert os.path.exists(os.path.join(tmp_path, "client_proposal.pdf")) or os.path.exists(os.path.join(tmp_path, "client_proposal.html"))

