# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""

@author: oklui
"""

from flask import Flask, send_file, request
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from arcgis.features import FeatureLayer
import io
import requests
from datetime import datetime
app = Flask(__name__)
# =========================
# ArcGIS Layer
# =========================
layer = [FeatureLayer("https://services2.arcgis.com/0Q7l03Ls62VG0fy4/arcgis/rest/services/Map2_WFL1/FeatureServer/1"),
         FeatureLayer("https://services2.arcgis.com/0Q7l03Ls62VG0fy4/arcgis/rest/services/Map2_WFL1/FeatureServer/2"),
         FeatureLayer("https://services2.arcgis.com/0Q7l03Ls62VG0fy4/arcgis/rest/services/Map2_WFL1/FeatureServer/3"),
         FeatureLayer("https://services2.arcgis.com/0Q7l03Ls62VG0fy4/arcgis/rest/services/Map2_WFL1/FeatureServer/4"),
         FeatureLayer("https://services2.arcgis.com/0Q7l03Ls62VG0fy4/arcgis/rest/services/Map2_WFL1/FeatureServer/5")]
# =========================
#VDOT Excel Call For Length And 
# MAP IMAGE FUNCTION
# =========================
def get_map_image(geometry):
    from PIL import Image as PILImage, ImageDraw
    from io import BytesIO

    x = geometry["x"]
    y = geometry["y"]

    delta = 400
    width, height = 800, 600
    bbox = f"{x - delta},{y - delta},{x + delta},{y + delta}"

    base_url = "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export"
    ref_url = "https://services.arcgisonline.com/arcgis/rest/services/Reference/World_Transportation/MapServer/export"

    params = {
        "bbox": bbox,
        "bboxSR": 3857,
        "imageSR": 3857,
        "size": f"{width},{height}",
        "f": "image"
    }

    try:
        # --- Base imagery ---
        base_resp = requests.get(base_url, params={**params, "format": "jpg"})
        base_img = PILImage.open(BytesIO(base_resp.content)).convert("RGBA")

        # --- Labels overlay ---
        ref_resp = requests.get(ref_url, params={
            **params,
            "format": "png32",
            "transparent": "true"
        })
        ref_img = PILImage.open(BytesIO(ref_resp.content)).convert("RGBA")

        # --- Combine ---
        combined = PILImage.alpha_composite(base_img, ref_img)

        # =========================
        #  DRAW RED DOT AT CENTER
        # =========================
        draw = ImageDraw.Draw(combined)

        cx = width // 2
        cy = height // 2
        r = 6  # radius of dot

        draw.ellipse(
            [(cx - r, cy - r), (cx + r, cy + r)],
            fill=(255, 0, 0),
            outline=(0, 0, 0)
        )

        # --- Save to buffer ---
        output = BytesIO()
        combined.save(output, format="PNG")
        output.seek(0)

        return output

    except Exception as e:
        print("Map generation failed:", e)
        return None
# =========================
# PDF FUNCTION
# =========================
def create_pdf(data):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=1 * inch,
        leftMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch
    )

    document = []

    # --- Title ---
    document.append(Paragraph(
        "<b>Speed Study Summary</b>",
        ParagraphStyle(name="Title", fontSize=14, alignment=TA_CENTER)
    ))

    document.append(Paragraph(
        f"<b>{data['location']} {data['type']} - Route {data['route']}</b>",
        ParagraphStyle(name="Title", fontSize=12, alignment=TA_CENTER)
    ))

    document.append(Paragraph(
        f"<b>{data['end_date']}</b>",
        ParagraphStyle(name="Title", fontSize=12, alignment=TA_CENTER)
    ))

    document.append(Spacer(1, 12))
    pstyle = ParagraphStyle(name="Normal", fontSize=10)
    document.append(Paragraph(
        f"At the request of residents living on {data['location']} {data['type']}, Prince William County Department of Transportation (PWC DOT) conducted a speed\
        study on {data['location']} {data['type']}. The study took place from {data['start_date']} to {data['start_date']}, near {data['nearest_address']}. \
        The posted speed limit for {data['location']} {data['type']} is {data['posted_speed']} MPH. At the study location, {data['location']} {data['type']} is {data['length']} miles long and is approximately {data['width']} feet wide.", pstyle))
    document.append(Spacer(1, 12))
    # --- Paragraphs ---
    document.append(Paragraph(
        f"{data['location']} {data['type']} is a local residential road and the 2024 VDOT average daily traffic count for {data['location']} {data['type']} is. "
        f"The attached map shows the approximate location where the study was conducted. "
        f"At the study location, the counters recorded an average daily traffic count of {data['pwc_adt']} vehicles per day with "
        f"speeds of {data['pwc_1_average']} MPH (85th percentile = {data['pwc_1_85th']} MPH) in the {data['direction_1']} Lane and {data['pwc_2_average']} MPH"
        f"(85th percentile = {data['pwc_2_85th']} MPH) in the {data['direction_2']} Lane.", pstyle))
    document.append(Spacer(1, 10))
    
    document.append(Paragraph(
        f"Based on this information, {data['location']} {data['type']} is {data['answer2']} for traffic calming measures as it {data['answer']} meet the "
        "required range of average daily traffic count of 600-4000 vehicles per day and the average speed of 5 MPH "
        "over the posted speed limit in one or more direction.", pstyle))
    document.append(Spacer(1, 10))

    document.append(Paragraph(
        f"<b>Recommendation:</b> PWC {data['answer']} recommend installing traffic calming measures on {data['location']} {data['type']}. "
        "The speed study results have been forwarded to the Prince William County Police Department for enforcement.", pstyle))
   
    document.append(Spacer(1, 10))
    # --- Criteria bullets ---
    bullets = [
        "25 MPH posted speed limit",
        "Two lane roadway",
        "Do not serve as primary access to any significant commercial or industrial sites",
        "Have a documented speeding problem (Recorded average speed of 5 MPH or greater than the posted speed limit in one direction)",
        "Average daily traffic of 600 – 4000 vehicles per day",
        "Identified community support for the traffic calming plan",
        "No more than four (4) traffic calming devices on emergency response routes"
    ]
    document.append(Paragraph("The following criteria shall be met for consideration of traffic calming measures", pstyle))
    bullet_style = ParagraphStyle(
    name="Bullet",
    fontSize=10,
    leftIndent=20,     # pushes entire bullet line right
    bulletIndent=10,   # controls bullet position
    spaceAfter=4
)

    for b in bullets:
        document.append(Paragraph(f"<bullet>&bull;</bullet> {b}", bullet_style))
    document.append(Spacer(1, 10))

    # --- Eligible streets ---
    eligible_text = (
        "<b>Eligible streets:</b> Local residential streets with posted speed limits of 35 MPH can be considered for "
        "traffic calming if they meet the traffic calming criteria. A local residential street provides direct access "
        "to abutting residences (driveways) and provides mobility within the neighborhood. Traffic on these streets is "
        "expected to be entering or exiting residences."
    )
    document.append(Paragraph(eligible_text, pstyle))
    document.append(Spacer(1, 10))

    collector_text = (
        "Certain residential collector streets, although classified as collector roads may have the characteristics "
        "of local residential streets. These streets may be considered for traffic calming measures, if they meet "
        "the established criteria."
    )
    document.append(Paragraph(collector_text, pstyle))
    document.append(Spacer(1, 10))
    # --- Image (optional) ---
    if data.get("picture"):
        try:
            document.append(Image(data["picture"], 6 * inch, 4 * inch))
            document.append(Paragraph(f"<b>Figure 1:</b> Map showing approximate location of speed study at marked point near {data['nearest_address']}.", ParagraphStyle(name="Normal", fontSize=9, alignment=TA_CENTER)))
        except:
            pass  # prevents crash if image fails

    doc.build(document)
    buffer.seek(0)
    return buffer

# =========================
# ROUTE
# =========================
@app.route("/")
def home():
    objectid = request.args.get("id")
    layer_name=request.args.get("layer_name")
    l_index=int(layer_name)
    if not objectid:
        return "Missing id parameter", 400
   # Query feature
    result = layer[l_index-1].query(
        where=f"OBJECTID = {objectid}",
        out_fields="*",
        return_geometry=True
    )

    if not result.features:
        return "Feature not found", 404

    feature = result.features[0]
    attrs = feature.attributes
    geom = feature.geometry
    # =========================
    # FIELD MAPPING
    # =========================
    #=========================
    #LOOP DETECTOR DICTIONARY
    #=========================
    if l_index==1:
        data = {
            "location": (attrs.get("StreetName").title()),
            "length": round(attrs.get("True_length")/5280,2) or "",
            "width": round(attrs.get("Road_width")) or "",
            "route": str(attrs.get("VDOTRouteNumber") or ""),
            "start_date": datetime.fromtimestamp(attrs.get("Date")/1000).strftime("%B %d, %Y"),
            "end_date": datetime.fromtimestamp(attrs.get("Date")/1000+259200).strftime("%B %d, %Y") or "N/A",
            "nearest_address": (attrs.get("Location__exact_address_")).title(),
            "vdot_adt": "***insert vdot_adt here",
            "posted_speed": attrs.get("SpeedLimit") or 0,
            "pwc_adt": attrs.get("Cumulative_ADT"),
            "pwc_1_average": attrs.get("Average") or 0,
            "pwc_2_average": attrs.get("Average_1") or 0,
            "pwc_1_85th": attrs.get("F85th_percentile") or 0,
            "pwc_2_85th": attrs.get("F85th_percentile_1") or 0,
            "direction_1": (attrs.get("Lane")).title() or "",
            "direction_2": (attrs.get("Lane_1")).title() or "",
            "type": (attrs.get("StreetType")).capitalize(),
            "picture": get_map_image(geom),
            "answer":"1",
            "answer2":"1",
            }
        if l_index==2:
            data = {
                "location": (attrs.get("StreetName").title()),
                "length": round(attrs.get("True_length")/5280,2),
                "width": round(attrs.get("Road_width")),
                "route": str(attrs.get("VDOTRouteNumber") or ""),
                "start_date": datetime.fromtimestamp(attrs.get("Date")/1000).strftime("%B %d, %Y"),
                "end_date": datetime.fromtimestamp(attrs.get("Date")/1000+259200).strftime("%B %d, %Y") or "N/A",
                "nearest_address": (attrs.get("Location__exact_address_")).title(),
                "vdot_adt": "***insert vdot_adt here",
                "posted_speed": attrs.get("SpeedLimit") or 0,
                "pwc_adt": attrs.get("Vehicle_Vol_"),
                "pwc_1_average": attrs.get("Average") or 0,
                "pwc_2_average": attrs.get("Average_1") or 0,
                "pwc_1_85th": attrs.get("F85th_percentile") or 0,
                "pwc_2_85th": attrs.get("F85th_percentile_1") or 0,
                "direction_1": (attrs.get("Lane")).title() or "",
                "direction_2": (attrs.get("Lane_1")).title() or "",
                "type": (attrs.get("StreetType")).capitalize(),
                "picture": get_map_image(geom),
                "answer":"1",
                "answer2":"1",
                }
            #=========================
            #RADAR DETECTOR DICTIONARY
            #=========================
        if l_index==3:
            data = {
                "location": (attrs.get("StreetName").title()),
                "length": round(attrs.get("True_length")/5280,2),
                "width": round(attrs.get("Road_width")),
                "route": str(attrs.get("VDOTRouteNumber") or ""),
                "start_date": datetime.fromtimestamp(attrs.get("Date")/1000).strftime("%B %d, %Y"),
                "end_date": datetime.fromtimestamp(attrs.get("Date")/1000+259200).strftime("%B %d, %Y") or "N/A",
                "nearest_address": (attrs.get("Location__exact_address_")).title(),
                "vdot_adt": "***insert vdot_adt here",
                "posted_speed": attrs.get("SpeedLimit") or 0,
                "pwc_adt": attrs.get("Vehicle_Vol_"),
                "pwc_1_average": attrs.get("Average") or 0,
                "pwc_2_average": attrs.get("Average_1") or 0,
                "pwc_1_85th": attrs.get("F85th_percentile") or 0,
                "pwc_2_85th": attrs.get("F85th_percentile_1") or 0,
                "direction_1": (attrs.get("Lane")).title() or "",
                "direction_2": (attrs.get("Lane_1")).title() or "",
                "type": (attrs.get("StreetType")).capitalize(),
                "picture": get_map_image(geom),
                "answer":"1",
                "answer2":"1",
                }
    # =========================
    # LOGIC
    # =========================
    if (
        (data["pwc_2_average"] >= 30 and data["pwc_1_average"] >= 30) and
        (data["pwc_adt"]>=600 and data["pwc_adt"]<=4000)
    ):
        data["answer"] = "does"
        data["answer2"] = "eligible"
    else:
        
        data["answer"] = "does not"
        data["answer2"] = "ineligible"

    # =========================
    # GENERATE PDF
    # =========================
    pdf_buffer = create_pdf(data)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        download_name=f"SpeedStudy_{objectid}.pdf"
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
