import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Starting Playwright...")

    p = await async_playwright().start()

    print("Playwright Started Successfully!")

    browser = await p.chromium.launch(headless=True)

    print("Chromium Launched Successfully!")

    await browser.close()
    await p.stop()

    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())