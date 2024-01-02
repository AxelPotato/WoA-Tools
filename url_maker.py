from collections import namedtuple
from flask import Flask, render_template, request, redirect, url_for, flash
from urllib.parse import urlencode, urlparse, urlunparse
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re, os, json

app = Flask(__name__)

# Path to your service account key file
SERVICE_ACCOUNT_FILE = "/home/AxelPotato/mysite/lecture_key.json"

# This access scope grants read-only access to the authenticated user's Drive
# account.
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
API_SERVICE_NAME = "drive"
API_VERSION = "v3"

DriveFileInfo = namedtuple('DriveFileInfo', ('id', 'name'))


def get_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    service = build("drive", "v3", credentials=credentials)
    return service


def get_file_name(file_id):
    service = get_service()
    file = (
        service.files()
        .get(fileId=file_id, fields="name", supportsAllDrives=True)
        .execute()
    )
    return file.get("name")


def validate_date(date_text):
    if not date_text:
        return True
    """Validate date format."""
    return re.match(r"^\d{4}-\d{2}$", date_text) is not None


def validate_language(lang_text):
    if not lang_text:
        return True
    """Validate language format (2 letters)."""
    return re.match(r"^[a-zA-Z]{2}$", lang_text) is not None


def handle_file_url(url):
    file_id = url.split("/d/")[1].split("/")[0]
    file_name = get_file_name(file_id)

    return DriveFileInfo(file_id, file_name)


def handle_folder_url(url):
    service = get_service()
    folder_id = url.split('/')[-1]

    drive_files = service.files().list(q=f"'{folder_id}' in parents",
                                       supportsAllDrives=True,
                                       includeItemsFromAllDrives=True,
                                       pageSize=1000).execute()['files']

    return [DriveFileInfo(drive_file['id'], drive_file['name']) for drive_file in drive_files]


def is_folder_url(url):
    return 'folders' in url


@app.route("/", methods=["GET", "POST"])
def index():
    final_url = None  # Variable to hold the final URL
    lang = base_url = event = date = location = ""

    if request.method == "POST":
        base_url = request.form.get("url")
        lang = request.form.get("lang").lower()
        event = request.form.get("event")
        date = request.form.get("date")
        location = request.form.get("location")

        if not validate_date(date):
            flash("Invalid date format. Please use YYYY-MM.")
        elif not validate_language(lang):
            flash("Invalid language format. Please use a 2-letter code.")
        else:
            params = {"lang": lang, "event": event, "date": date, "location": location}
            url_parts = list(urlparse(base_url))
            query = dict(urlparse(base_url).query)
            query.update(params)
            url_parts[4] = urlencode(query)
            final_url = urlunparse(url_parts)

    return render_template(
        "index.html",
        url=base_url,
        lang=lang,
        event=event,
        date=date,
        location=location,
        final_url=final_url,
    )


@app.route("/lectures", methods=["GET", "POST"])
def lectures():
    lectures = []

    if request.method == "POST":
        url = request.form["url"]

        if is_folder_url(url):
            lectures = handle_folder_url(url)
        else:
            lectures = [handle_file_url(url)]

        
    return render_template(
        "lecture_maker.html",
        lectures=lectures
    )


if __name__ == "__main__":
    app.run(debug=True)
