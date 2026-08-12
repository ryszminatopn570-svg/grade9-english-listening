from pathlib import Path

import qrcode


ROOT = Path(__file__).resolve().parents[1]
TRACK_NAME = "U01_Section-A_1b_The-Changing-World"
PUBLIC_URL = "https://ryszminatopn570-svg.github.io/grade9-english-listening/unit-01/section-a/1b/"

qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=12,
    border=4,
)
qr.add_data(PUBLIC_URL)
qr.make(fit=True)
image = qr.make_image(fill_color="#10233f", back_color="white")

for folder in (ROOT / "deliverables", ROOT / "docs" / "assets" / "images"):
    folder.mkdir(parents=True, exist_ok=True)
    image.save(folder / f"{TRACK_NAME}_QR.png")

print(PUBLIC_URL)
