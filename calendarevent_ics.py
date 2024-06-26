from icalendar import Calendar, Event, vCalAddress
from datetime import datetime, timedelta

# Create a calendar
cal = Calendar()

# Add calendar metadata
cal.add('prodid', '-//Your Organization//Your Product//EN')
cal.add('version', '2.0')
cal.add('method', 'REQUEST')

# Create an event
event = Event()
event.add('uid', '13257')
event.add('dtstamp', datetime(2024, 6, 6, 12, 0, 0))
event.add('dtstart', datetime(2024, 7, 13, 9, 0, 0))
event.add('dtend', datetime(2024, 7, 13, 10, 0, 0))
event.add('summary', 'Desc Sync Demo')
event.add('location', 'Virtual')
# event.add('description', 'Join the meeting: https://meet.google.com/frv-ejwm-tyc')
# event.add('status', 'CONFIRMED')
# event.add('description', 'Event has been Cancelled')
event.add('status', 'CANCELLED')
event.add('priority', 1)
event.add('transp', 'OPAQUE')
event.add('sequence', 1)

# # Add organizer
# organizer = vCalAddress('MAILTO:boopathig13@outlook.com')
# organizer.params['cn'] = 'Boopathi G'
# event['organizer'] = organizer

# Add attendees
attendee1 = vCalAddress('MAILTO:boopathiboopathi7647@outlook.com')
attendee1.params['cn'] = 'Boopathi'
attendee1.params['RSVP'] = 'TRUE'
# attendee1.params['PARTSTAT'] = 'CANCELLED'

attendee2 = vCalAddress('MAILTO:jbhuvanesh@outlook.com')
attendee2.params['cn'] = 'Bhuvanesh'
attendee2.params['RSVP'] = 'TRUE'

event.add('attendee', attendee1, encode=0)
# event.add('attendee', attendee2, encode=0)

# Add alarm
alarm = Event()
alarm.add('trigger', timedelta(minutes=-10))
alarm.add('action', 'DISPLAY')
alarm.add('description', 'Reminder')
event.add_component(alarm)

# Add the event to the calendar
cal.add_component(event)

# Write to an .ics file
with open('calendar_new.ics', 'wb') as f:
    # f.write(cal.to_ical().replace(b'\n', b'\r\n').decode('utf-8').encode('utf-8'))
    f.write(cal.to_ical().replace(b'\n', b'\r\n'))


print("calendar.ics file has been created")
