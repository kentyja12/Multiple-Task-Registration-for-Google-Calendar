import datetime
import googleapiclient.discovery
import google.auth
import json
import csv

# Load configuration from JSON file
with open("config.json", "r") as file:
    config = json.load(file)

# Define scopes, calendar ID, and authentication path
SCOPES = [config["googleAPI"]["SCOPES"]]
calendar_id = config["googleAPI"]["calendar_id"]
auth_path = config["googleAPI"]["auth_path"]

# Load Google API credentials from authentication file
gapi_creds = google.auth.load_credentials_from_file(auth_path, SCOPES)[0]

# Build Google Calendar service
service = googleapiclient.discovery.build('calendar', 'v3', credentials=gapi_creds)

# Initialize events list and event data dictionary
events = []
event_data_corrected = {}

# Read event data from CSV file
with open("event_manager.csv", 'r') as file:
    for line in file:
        parts = [part.replace('"', '').strip() for part in line.split(',')]
        key = parts[0]
        value = parts[1] if len(parts) > 1 else None

        # Parse event attributes
        if key == 'title':
            if event_data_corrected:
                events.append(event_data_corrected)
            event_data_corrected = {'title': value}
        elif key == 'year':
            event_data_corrected['year'] = value
        elif key == 'month':
            event_data_corrected['month'] = value
        elif key == 'day':
            event_data_corrected['days'] = value.split(',')
        elif key == 'range':
            event_data_corrected['range'] = [value, parts[2] if len(parts) > 2 else None]
        elif key == 'Considering breaks every 6 hours?':
            event_data_corrected['breaks'] = value.lower() == 'yes'

# Append last event if exists
if event_data_corrected:
    events.append(event_data_corrected)

# Create events in Google Calendar
for event in events:
    start_hour, start_minute = map(int, event["range"][0].split(':'))
    end_hour, end_minute = map(int, event["range"][1].split(':'))
    range_hours = end_hour - start_hour

    # Adjust end time if breaks are considered and duration is 6 hours or more
    if event.get("breaks", False) and range_hours >= 6:
        end_hour += 1

    timezone = 'Japan'
    colorId = "10"

    # Create event for each specified day
    for day in event["days"]:
        day = int(day)
        year = int(event["year"])  
        month = int(event["month"])
        body = {
            "summary": f"({range_hours}h) {event['title']}",
            "start": {
                "dateTime": datetime.datetime(year, month, day, start_hour, start_minute).isoformat(),
                "timeZone": timezone
            },
            "end": {
                "dateTime": datetime.datetime(year, month, day, end_hour, end_minute).isoformat(),
                "timeZone": timezone
            },
            "colorId": colorId
        }

        # Insert event into Google Calendar
        inserted_event = service.events().insert(calendarId=calendar_id, body=body).execute()
