"""Keep the security policy easy to find from public project entry points."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_URL = "https://github.com/BlizzHacker/romarr/blob/main/SECURITY.md"


def test_repository_readme_links_to_security_reporting_policy():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "[security policy](SECURITY.md)" in readme
    assert "do not open a public issue for exploitable matters" in readme


def test_public_website_links_to_canonical_security_policy():
    page = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
    assert f'href="{POLICY_URL}"' in page
    assert ">Security policy</a>" in page
