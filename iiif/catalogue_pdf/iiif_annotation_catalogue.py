#!/usr/bin/env python3
"""
Simple IIIF Annotation Catalogue

Given a IIIF Presentation 3 manifest, create a PDF where:

Page 1 (odd):
    Annotation crops + annotation text

Page 2 (even):
    Full image overview (vignette)

Page 3:
    More annotations (if necessary)

Page 4:
    Full image again

...

Dependencies:
    pip install requests pillow reportlab
"""

import io
import math
import argparse
import requests

from PIL import Image
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# ----------------------------------------------------------
# Utilities
# ----------------------------------------------------------

def download_json(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def download_image(url):
    r = requests.get(url)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def flatten_body(body):
    """Return a list of textual bodies."""

    if isinstance(body, dict):
        body = [body]

    texts = []

    for b in body:
        if not isinstance(b, dict):
            continue

        value = b.get("value")
        if value:
            purpose = b.get("purpose", "")
            if purpose:
                texts.append(f"[{purpose}] {value}")
            else:
                texts.append(value)

    return texts


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("manifest")

    parser.add_argument(
        "-o",
        "--output",
        default="catalogue.pdf"
    )

    args = parser.parse_args()

    manifest = download_json(args.manifest)

    pdf = canvas.Canvas(args.output)

    items = manifest["items"]

    for canvas_item in items:

        width = canvas_item["width"]
        height = canvas_item["height"]

        image_service = (
            canvas_item["items"][0]
            ["items"][0]
            ["body"]
            ["service"][0]
            ["id"]
        )

        # ---------------------------------------------
        # overview image
        # ---------------------------------------------

        overview_url = (
            f"{image_service}/full/700,/0/default.jpg"
        )

        overview = download_image(overview_url)

        # ---------------------------------------------
        # annotations
        # ---------------------------------------------

        annotation_pages = canvas_item.get("annotations", [])

        annotations = []

        for ap in annotation_pages:

            anno_json = download_json(ap["id"])

            for anno in anno_json["items"]:

                target = anno["target"]

                if "#xywh=" not in target:
                    continue

                xywh = target.split("#xywh=")[1]

                x, y, w, h = map(float, xywh.split(","))

                x0 = math.floor(x)
                y0 = math.floor(y)

                x1 = math.ceil(x + w)
                y1 = math.ceil(y + h)

                region = (
                    x0,
                    y0,
                    x1 - x0,
                    y1 - y0,
                )

                crop_url = (
                    f"{image_service}/"
                    f"{region[0]},{region[1]},"
                    f"{region[2]},{region[3]}"
                    f"/full/0/default.jpg"
                )

                try:
                    crop = download_image(crop_url)
                except Exception:
                    continue

                texts = flatten_body(anno.get("body", []))

                annotations.append(
                    {
                        "crop": crop,
                        "texts": texts,
                    }
                )

        # --------------------------------------------------
        # create pages
        # --------------------------------------------------

        index = 0

        while index < len(annotations):

            # ------------------------
            # Odd page
            # ------------------------

            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(
                2 * cm,
                28 * cm,
                "Annotations"
            )

            y = 25 * cm

            while index < len(annotations) and y > 5 * cm:

                anno = annotations[index]

                crop = anno["crop"]

                crop.thumbnail((220, 220))

                reader = ImageReader(crop)

                pdf.drawImage(
                    reader,
                    2 * cm,
                    y - 4 * cm,
                    width=4 * cm,
                    height=4 * cm,
                    preserveAspectRatio=True,
                )

                tx = 7 * cm
                ty = y

                pdf.setFont("Helvetica", 10)

                for line in anno["texts"]:
                    pdf.drawString(tx, ty, line[:120])
                    ty -= 0.5 * cm

                y -= 5 * cm
                index += 1

            pdf.showPage()

            # ------------------------
            # Even page
            # ------------------------

            reader = ImageReader(overview)

            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(
                2 * cm,
                28 * cm,
                "Image overview"
            )

            pdf.drawImage(
                reader,
                2 * cm,
                5 * cm,
                width=17 * cm,
                preserveAspectRatio=True,
            )

            pdf.showPage()

    pdf.save()

    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()