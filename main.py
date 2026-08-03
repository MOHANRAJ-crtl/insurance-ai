import sys
import asyncio

import playwright

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI()


PROXY_WEBSITE = "https://mohanraj-crtl.github.io/insurance-website/"

SELECTORS = {
    "memberId": "#memberId",
    "patientName": "#patientName",
    "claimNumber": "#claimNumber",
    "checkButton": "#checkStatus",
    "statusResult": "#statusResult"
}


class ClaimRequest(BaseModel):
    memberId: str
    patientName: str
    claimNumber: str


@app.post("/check-claim")
async def check_claim(req: ClaimRequest):

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ]
    )

    try:
        page = await browser.new_page()

        # Open proxy website
        await page.goto(PROXY_WEBSITE)

        # Fill the fields
        await page.fill(SELECTORS["memberId"], req.memberId)
        await page.fill(SELECTORS["patientName"], req.patientName)
        await page.fill(SELECTORS["claimNumber"], req.claimNumber)

        # Click button
        await page.click(SELECTORS["checkButton"])

        # Wait for result
        await page.wait_for_selector(
            SELECTORS["statusResult"],
            state="visible"
        )

        # Read status
        status = await page.text_content(
            SELECTORS["statusResult"]
        )

        return {
            "success": True,
            "memberId": req.memberId,
            "patientName": req.patientName,
            "claimNumber": req.claimNumber,
            "claimStatus": status.strip()
        }

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        await browser.close()
        await pw.stop()