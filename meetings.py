import requests
from datetime import datetime, timezone
import pytz

def get_invitations():

    url_scheduled_events = "https://api.calendly.com/scheduled_events"

    api_token = 'eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNzE4NTM3NjQ2LCJqdGkiOiJmYTU3NjY0Ni1mZWU2LTQ4N2MtODgxOS02ZDFmMjg0MGM4NzIiLCJ1c2VyX3V1aWQiOiI3NTc1ZDZhYi00ZmVlLTQ4OTEtODQzNy1iZGE3ZTRlMWYzNDIifQ.pC_keeeoA_JxCkOjgWfNptJv8Otw2TcLmWKNyeH8wLNLR7Mv2bm-EWAJ-N6Mr1IxhLPt1ihSLh4YyIdE4IJVgg'

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    current_time = datetime.now(timezone.utc)

    formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    params = {
        'organization': 'https://api.calendly.com/organizations/2c26523a-1ae6-413e-9ca5-5bb81918ebe4',
        'min_start_time': formatted_time,
        'status': 'active'
    }

    response_scheduled_events = requests.get(url_scheduled_events, headers=headers, params=params)

    total_invites = []
    invites_emails = []

    if response_scheduled_events.status_code == 200:
        scheduled_events = response_scheduled_events.json().get('collection', [])
        total_invitees = 0

        for event in scheduled_events:
            event_uuid = event['uri'].split('/')[-1]  # Extract event UUID from the event URI
            url_invitees = f"https://api.calendly.com/scheduled_events/{event_uuid}/invitees"

            response_invitees = requests.get(url_invitees, headers=headers)

            if response_invitees.status_code == 200:
                invitees = response_invitees.json().get('collection', [])
                total_invitees += len(invitees)

                # Get detailed information for each invitee
                for invitee in invitees:
                    invitee_uuid = invitee['uri'].split('/')[-1]  # Extract invitee UUID from the invitee URI
                    url_invitee_detail = f"https://api.calendly.com/scheduled_events/{event_uuid}/invitees/{invitee_uuid}"

                    response_invitee_detail = requests.get(url_invitee_detail, headers=headers)

                    if response_invitee_detail.status_code == 200:
                        invitee_detail = response_invitee_detail.json()
                        total_invites.append(invitee_detail['resource'])
                        invites_emails.append(invitee_detail['resource']['email'])
                    else:
                        print(f"Failed to retrieve details for invitee {invitee_uuid}")
            else:
                print(f"Failed to retrieve invitees for event {event_uuid}")

        print(f"Total Number of Invitees: {total_invitees}")
    else:
        print("Failed to retrieve scheduled events")

    # print(scheduled_events)
    # print(invites_emails)

    return total_invites, scheduled_events, invites_emails


def time_conversion_to_PST(date_string):
    dt_utc = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')

    utc_timezone = pytz.timezone('UTC')

    dt_utc = utc_timezone.localize(dt_utc)

    pkt_timezone = pytz.timezone('Asia/Karachi')
    dt_pkt = dt_utc.astimezone(pkt_timezone)

    formatted_date = dt_pkt.strftime('%dth %B %Y and %I %p')

    return formatted_date

def get_meeting_timings(total_invites, scheduled_events, successful_candidates, invites_emails):

    scheduled_timings = []
    successful_emails = []

    for candidate in successful_candidates:
        successful_emails.append(candidate[1])

    for index in range(len(scheduled_events)):
        if total_invites[index]['email'] in successful_emails:
            email_index = successful_emails.index(total_invites[index]['email'])
            if scheduled_events[index]['uri'] == total_invites[index]['event']:
                date_and_time = time_conversion_to_PST(scheduled_events[index]['start_time'])
                scheduled_timings.append([successful_candidates[email_index][0],total_invites[index]['email'], successful_candidates[email_index][2], date_and_time])
                # successful_emails.remove(total_invites[index]['email'])

    for index in range(len(successful_emails)):
        if successful_emails[index] not in invites_emails:
            scheduled_timings.append([successful_candidates[index][0], successful_emails[index], successful_candidates[index][2], 'Not Accepted'])


    return scheduled_timings