from playwright.sync_api import sync_playwright, expect

def test_docs_ux(page):
    # Wait for server to start (it might be on 5173 by default for Vite)
    # We might need to retry connection if it's slow to start
    page.goto("http://localhost:5173")

    # Check title/content to ensure it loaded
    expect(page.get_by_text("The Singularity")).to_be_visible()

    # Verify Version Badge
    badge = page.get_by_text("v3.0.0 Now Available")
    expect(badge).to_be_visible()

    # Verify accessibility attributes
    # We can use css selectors to check attributes

    # 1. Background blobs - we added aria-hidden=true
    # The first div with absolute position and blur-120px
    blobs = page.locator("div.absolute.blur-\\[120px\\]")
    # Expect at least one to have aria-hidden
    expect(blobs.first).to_have_attribute("aria-hidden", "true")

    # 2. Ping animation container
    # It's a span with relative flex h-2 w-2
    ping_span = page.locator("span.relative.flex.h-2.w-2")
    expect(ping_span).to_have_attribute("aria-hidden", "true")

    # 3. Code block region
    code_region = page.get_by_role("region", name="Code example showing Qyro syntax")
    expect(code_region).to_be_visible()

    # Take screenshot
    page.screenshot(path="verification/docs_ux.png")
    print("Verification successful!")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            test_docs_ux(page)
        except Exception as e:
            print(f"Test failed: {e}")
            # print page content for debug
            # print(page.content())
        finally:
            browser.close()
