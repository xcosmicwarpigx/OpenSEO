import pytest

from tasks import competitive


@pytest.mark.asyncio
async def test_fetch_keyword_data_local_extraction(monkeypatch):
    sample_html = """
    <html>
      <head><title>SEO Tools</title></head>
      <body>
        <main>
          <h1>SEO tools and keyword research</h1>
          <p>SEO SEO SEO keyword research ranking analysis audit</p>
        </main>
      </body>
    </html>
    """

    async def fake_discover_pages(domain: str, max_pages: int = 10):
        return ["https://example.com"]

    async def fake_fetch_html(client, url: str):
        return sample_html

    monkeypatch.setattr(competitive, "_discover_pages", fake_discover_pages)
    monkeypatch.setattr(competitive, "_fetch_html", fake_fetch_html)

    result = await competitive.fetch_keyword_data("example.com", max_keywords=5)

    assert result.total_keywords > 0
    assert any(k.keyword == "seo" for k in result.keywords)
    assert result.total_traffic_estimate >= 0


def test_estimate_ctr_curve():
    assert competitive.estimate_ctr(1) > competitive.estimate_ctr(5)
    assert competitive.estimate_ctr(10) >= competitive.estimate_ctr(20)
    assert competitive.estimate_ctr(50) == 0.005


def test_extract_tokens_filters_noise():
    html = "<html><body><script>alert(1)</script><p>The best seo audit tool</p></body></html>"
    tokens = competitive._extract_tokens(html)

    assert "alert" not in tokens
    assert "the" not in tokens
    assert tokens["seo"] == 1
