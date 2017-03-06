#!/usr/bin/env python
import requests
import sys
from dateutil.parser import parse
from datetime import datetime
from datetime import timedelta
import pytz
from tzlocal import get_localzone
import time
from math import trunc

# Pulled from proxying the Southwest iOS App
headers = {'Host': 'mobile.southwest.com', 'Content-Type': 'application/vnd.swacorp.com.mobile.reservations-v1.0+json', 'X-API-Key': 'l7xxab4b3533b8d54bad9df230deb96a6f90', 'Accept': '*/*'}

def checkin(first_name, last_name, reservation_number):
    # Find our existing record
    url = "https://mobile.southwest.com/api/extensions/v1/mobile/reservations/record-locator/{}?first-name={}&last-name={}".format(reservation_number, first_name, last_name)

    r = requests.get(url, headers=headers)
    body = r.json()

    # Confirm this reservation is found
    if 'httpStatusCode' in body and body['httpStatusCode'] == 'NOT_FOUND':
        print(body['message'])
    else:
        now = datetime.now(pytz.utc).astimezone(get_localzone())
        tomorrow = now + timedelta(days=1)
        date = now

        airport = ""

        # Get the correct flight information
        for leg in body['itinerary']['originationDestinations']:
            departure_time = leg['segments'][0]['departureDateTime']
            airport = leg['segments'][0]['originationAirportCode']
            date = parse(departure_time)
            # Stop when we reach a future flight
            if date > now:
                break

        print("Flight information found, departing {} at {}".format(airport, date.strftime('%b %d %I:%M%p')))

        # Wait until checkin time
        if date > tomorrow:
            delta = (date-tomorrow).total_seconds()
            m, s = divmod(delta, 60)
            h, m = divmod(m, 60)
            print("Too early to check in.  Waiting {} hours, {} minutes, {} seconds".format(trunc(h), trunc(m), s))
            time.sleep(delta)

        print("Attempting check-in...")

        # Get our passengers to get boarding passes for
        passengers = []
        for passenger in body['passengers']:
            passengers.append({'firstName': passenger['secureFlightName']['firstName'], 'lastName': passenger['secureFlightName']['lastName']})

        # Check in
        headers['Content-Type'] = 'application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json'
        url = "https://mobile.southwest.com/api/extensions/v1/mobile/reservations/record-locator/{}/boarding-passes".format(reservation_number)
        r = requests.post(url, headers=headers, json={'names': passengers})

        body = r.json()

        if 'httpStatusCode' in body and body['httpStatusCode'] == 'FORBIDDEN':
            print(body['message'])
        else:
            # Spit out info about boarding number
            for checkinDocument in body['passengerCheckInDocuments']:
                for doc in checkinDocument['checkinDocuments']:
                    print("You got {}{}!".format(doc['boardingGroup'], doc['boardingGroupNumber']))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
