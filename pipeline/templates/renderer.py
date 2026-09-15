"""
Jinja2 template rendering engine for Website Updater Studio.
Renders Swiss Minimalist websites and executive PDF proposals.
"""

import os
import urllib.parse
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.dirname(__file__)

_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True
)
_jinja_env.globals["urllib"] = urllib
_jinja_env.filters["urlencode"] = urllib.parse.quote_plus


def render_template(template_rel_path: str, **context) -> str:
    """Renders a template relative to pipeline/templates/ with the given context variables."""
    template = _jinja_env.get_template(template_rel_path.replace("\\", "/"))
    return template.render(**context)
