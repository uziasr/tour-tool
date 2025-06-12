import os
from datetime import datetime
import re
import shutil
from pathlib import Path


def meters_to_miles(meters: float) -> float:
    """Convert meters to miles."""
    return meters / 1609.344


def generate_unique_id():
    # Option 1: timestamp
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")


def save_pdf_for_user(pdf_bytes, uid):
    folder = f"generated_pdfs/{uid}"
    os.makedirs(folder, exist_ok=True)

    pdf_path = os.path.join(folder, "trip_summary.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return pdf_path


def parse_locations_from_email(body: str):
    # Normalize newlines and remove excessive whitespace
    body = body.replace('\r', '').strip()

    # Pattern for multiline or inline
    from_match = re.search(r'from:\s*(.+?)(?=\s*to:|$)', body, re.IGNORECASE)
    to_match = re.search(r'to:\s*(.+)', body, re.IGNORECASE)

    if from_match and to_match:
        start = from_match.group(1).strip()
        end = to_match.group(1).strip()
        return start, end

    raise ValueError("Could not parse 'from' and 'to' in email body.")


def clean_up_trip_data(trip_hash: str):
    """
    Deletes all data associated with a trip hash from 
    both `data/` and `output/` directories.
    """
    data_path = Path(f"data/{trip_hash}")
    output_path = Path(f"output/{trip_hash}")

    deleted = []

    for path in [data_path, output_path]:
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
                deleted.append(str(path))
                print(f"[✓] Deleted: {path}")
            except Exception as e:
                print(f"[!] Error deleting {path}: {e}")
        else:
            print(f"[-] Path not found or not a directory: {path}")

    if not deleted:
        print("[i] No files were deleted.")
    return deleted


def create_body(frontend_url: str):
    body = f""" -> str
    Your trip has been successfully created! Find details laid out in the PDF.
    Additionally, You may visit the following link to view your trip:
    {frontend_url}
    """
    return body
