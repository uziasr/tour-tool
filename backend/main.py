from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright

from fpdf import FPDF
from PIL import Image

import os
import json
import hashlib
import base64
from fastapi.middleware.cors import CORSMiddleware

from tools.general import parse_locations_from_email, create_body
from pathlib import Path

from tools.open_route import call_api, OpenRouteDirections
from tools.open_trip import OpenTripInterface
import httpx

from dotenv import load_dotenv

from contants import DIRECTION_FILE_NAME, POI_FILE_NAME

load_dotenv()

FRONTEND_URL = os.environ.get('FRONTEND_URL')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
POSTMARK_API_KEY = os.environ.get('POSTMARK_API_KEY')
POSTMARK_EMAIL_URL = os.environ.get('POSTMARK_EMAIL_URL')

app = FastAPI()

# Allow your Next.js frontend
origins = [
    FRONTEND_URL
]

app.add_middleware(
    CORSMiddleware,
    # you can also use ["*"] for all (not recommended for production)
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}


@app.post("/inbound")
async def process_email(request: Request):
    """
    Processes an inbound email from Postmark, extracts trip details,
    Gets directions and POIs, generates screenshots,
    and sends a PDF back to the user.
    """
    data = await request.json()
    text = data.get("TextBody", "")
    sender = data.get("From", "")

    # Step 1: Parse from/to
    start, end = parse_locations_from_email(text)  # your logic here
    if not start or not end:
        return JSONResponse({"error": "Invalid format"}, status_code=400)

    # Step 2: Create hash
    hash_input = f"{start}_{end}"
    trip_hash = hashlib.sha1(hash_input.encode()).hexdigest()[:10]
    base_dir = Path(f"data/{trip_hash}/coordinates")
    base_output_dir = Path(f"data/{trip_hash}/output")

    base_dir.mkdir(parents=True, exist_ok=True)

    # Step 3: Get directions + POIs (pseudocode here)
    directions_json = await call_api(start, end)

    directions: OpenRouteDirections = OpenRouteDirections(directions_json)
    directions.get_coords_based_on_interval()

    trip_interface = OpenTripInterface(
        directions.stop_coordinates,  # contains the coordinates of the stops
        hash=hash_input
    )
    pois = trip_interface.get_places()
    total_stops = set([
        (poi['source_coord'][0], poi['source_coord'][1]) for
        poi in pois
    ])

    # pois = await get_pois_along_route(directions)

    # Save files
    with open(base_dir / DIRECTION_FILE_NAME, "w") as f:
        json.dump(directions_json, f)
    with open(base_dir / POI_FILE_NAME, "w") as f:
        json.dump(pois, f)

    # Step 4: Ping frontend
    frontend_url = f"{FRONTEND_URL}/map?hash={trip_hash}"

    # output_dir = "screenshots"
    os.makedirs(base_output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(frontend_url, wait_until="networkidle")

        screenshot_paths = []

        # Initial screenshot before any clicks
        path = f"{base_output_dir}/step-0.png"
        await page.screenshot(path=path, full_page=True)
        screenshot_paths.append(path)

        # this will be dynamic based on the number of steps in the tour
        for i in range(1, len(total_stops)):
            await page.click("#next-button")
            # Give time for UI updates (map, POIs)
            await page.wait_for_timeout(1000)
            path = f"{base_output_dir}/step-{i}.png"
            await page.screenshot(path=path, full_page=True)

            screenshot_paths.append(path)
        create_pdf(screenshot_paths, f"{base_output_dir}/tour.pdf")
        await browser.close()

    await send_email_with_pdf(
        to_email=sender,
        subject="Your Custom Travel Guide",
        body=create_body(frontend_url),
        pdf_path=f"{base_output_dir}/tour.pdf"
    )
    # removing from now, so that users can load up the frontend
    # clean_up_trip_data(trip_hash)  # Clean up trip data after processing
    # Clean up screenshots and coordinates directory

    return JSONResponse(content={"status": "complete"}, status_code=200)


@app.get("/inbound_test")
async def process_email_test(request: Request):
    """
    Processes an inbound email from Postmark, extracts trip details,
    Gets directions and POIs, generates screenshots,
    and sends a PDF back to the user.
    """
    # data = await request.json()
    # text = data.get("TextBody", "")
    # sender = data.get("From", "")

    # Step 1: Parse from/to
    text = 'from:  San Diego, California to: Mammoth, California'
    start, end = parse_locations_from_email(text)  # your logic here
    if not start or not end:
        return JSONResponse({"error": "Invalid format"}, status_code=400)

    # Step 2: Create hash
    hash_input = f"{start}_{end}"
    trip_hash = hashlib.sha1(hash_input.encode()).hexdigest()[:10]
    base_dir = Path(f"data/{trip_hash}/coordinates")
    base_output_dir = Path(f"data/{trip_hash}/output")

    base_dir.mkdir(parents=True, exist_ok=True)

    # Step 3: Get directions + POIs (pseudocode here)
    directions_json = call_api(start, end)

    directions: OpenRouteDirections = OpenRouteDirections(directions_json)
    directions.get_coords_based_on_interval()

    trip_interface = OpenTripInterface(
        directions.stop_coordinates,  # contains the coordinates of the stops
        hash=hash_input
    )
    pois = trip_interface.get_places()
    total_stops = set([
        (poi['source_coord'][0], poi['source_coord'][1]) for
        poi in pois
    ])

    # pois = await get_pois_along_route(directions)

    # Save files
    with open(base_dir / DIRECTION_FILE_NAME, "w") as f:
        json.dump(directions_json, f)
    with open(base_dir / POI_FILE_NAME, "w") as f:
        json.dump(pois, f)

    # Step 4: Ping frontend
    frontend_url = f"{FRONTEND_URL}/map?hash={trip_hash}"

    # output_dir = "screenshots"
    os.makedirs(base_output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(frontend_url, wait_until="networkidle")

        screenshot_paths = []

        # Initial screenshot before any clicks
        path = f"{base_output_dir}/step-0.png"
        await page.screenshot(path=path, full_page=True)
        screenshot_paths.append(path)

        # this will be dynamic based on the number of steps in the tour
        for i in range(1, len(total_stops)):
            await page.click("#next-button")
            # Give time for UI updates (map, POIs)
            await page.wait_for_timeout(2000)
            path = f"{base_output_dir}/step-{i}.png"
            await page.screenshot(path=path, full_page=True)

            screenshot_paths.append(path)
        create_pdf(screenshot_paths, f"{base_output_dir}/tour.pdf")
        await browser.close()

    return JSONResponse(content={"status": "complete"}, status_code=200)


def create_pdf(image_paths, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)  # Disable bottom margin

    for img_path in image_paths:
        pdf.add_page()
        page_width = pdf.w - 2 * pdf.l_margin
        page_height = pdf.h - 2 * pdf.t_margin

        img = Image.open(img_path)
        img_width, img_height = img.size
        aspect_ratio = img_height / img_width

        img_display_height = page_width * aspect_ratio

        # Center vertically if image height is smaller than page height
        y_position = pdf.t_margin
        if img_display_height < page_height:
            y_position += (page_height - img_display_height) / 2

        pdf.image(img_path, x=pdf.l_margin, y=y_position,
                  w=page_width, h=img_display_height)

    pdf.output(output_path)


async def send_email_with_pdf(
        to_email: str,
        subject: str,
        body: str,
        pdf_path: str
):
    """
    Sends an Email with a PDF of the tour attached using Postmark API.
    """
    # Read and encode the PDF
    pdf_file = Path(pdf_path)
    with pdf_file.open("rb") as f:
        encoded_pdf = base64.b64encode(f.read()).decode()

    payload = {
        "From": FROM_EMAIL,
        "To": to_email,
        "Subject": subject,
        "TextBody": body,
        "Attachments": [
            {
                "Name": pdf_file.name,
                "Content": encoded_pdf,
                "ContentType": "application/pdf"
            }
        ]
    }

    headers = {
        "X-Postmark-Server-Token": POSTMARK_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            POSTMARK_EMAIL_URL,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()


@app.get("/directions")
async def get_directions(hash: str = Query(...)):
    direction_path = Path(f"data/{hash}/coordinates/directions.json")
    try:
        with open(direction_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return JSONResponse(
            dict(error='Files no longer exist'),
            status_code=400,
            media_type='application/json'
        )
    return JSONResponse(
        data, status_code=200, media_type="application/json"
    )


@app.get("/pois")
async def get_pois(hash: str = Query(...)):
    poi_path = Path(f"data/{hash}/coordinates/pois.json")
    try:
        with open(poi_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return JSONResponse(
            dict(error='Files no longer exist'),
            status_code=400,
            media_type='application/json'
        )
    return JSONResponse(
        data, status_code=200, media_type="application/json"
    )
