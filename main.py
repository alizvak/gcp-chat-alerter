# main.py
import os
import json
import requests
from google.cloud import bigquery

### !!! SECURITY WARNING !!! ###
# Hardcoding secrets like a webhook URL is not recommended for production.
# Anyone with access to this code can see and use your webhook.
# It is best practice to store this in Google Secret Manager.
CHAT_WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAAA.../messages?key=AIza..."

def send_dataform_alert(cloudevent):
    """
    Triggered by a BigQuery job completion event via Eventarc.
    Queries the newly created table and sends a Google Chat message if it's not empty.
    """
    # --- 1. Parse the event to get the created table name ---
    try:
        payload = cloudevent.data.get("protoPayload", {})
        resource_name = payload.get("resourceName", "")
        parts = resource_name.split("/")
        if len(parts) < 6 or not parts[-1].startswith("flagged_alerting_tables_"):
            print(f"Ignoring irrelevant event for resource: {resource_name}")
            return "Event ignored.", 204

        table_id = f"{parts[1]}.{parts[3]}.{parts[5]}"
        run_date_str = parts[5][-8:] # Extracts the YYYYMMDD part
        print(f"Processing alert for table: {table_id}")

    except Exception as e:
        print(f"Error parsing CloudEvent payload: {e}")
        return "Payload parsing failed.", 400

    # --- 2. Query BigQuery to get the flagged reports ---
    client = bigquery.Client()
    try:
        results = list(client.query(f"SELECT flagged_table_name FROM `{table_id}` ORDER BY 1"))
    except Exception as e:
        print(f"Error querying BigQuery table {table_id}: {e}")
        return "BigQuery query failed.", 500

    if not results:
        print(f"Table {table_id} is empty. No alert needed.")
        return "No alert sent.", 204

    # --- 3. Format the results into a Google Chat message ---
    flagged_reports = [row['flagged_table_name'] for row in results]
    report_list_str = "\n".join([f"• `{report}`" for report in flagged_reports])

    message = {
        "text": (
            f"🚨 *Dataform Anomaly Alert*\n\n"
            f"The following *{len(flagged_reports)}* reports have new flagged data for run date: *{run_date_str}*\n\n"
            f"{report_list_str}"
        )
    }

    # --- 4. Send the message to the hardcoded webhook URL ---
    try:
        response = requests.post(CHAT_WEBHOOK_URL, headers={"Content-Type": "application/json"}, data=json.dumps(message))
        response.raise_for_status()
        
        print("Google Chat message sent successfully.")
        return "Alert sent.", 200
    except Exception as e:
        print(f"Error sending Google Chat message: {e}")
        return "Failed to send alert.", 500
