import re
from datetime import datetime, timedelta

from icalendar import Event, Alarm


class Course:

    def __init__(self, name, occur_time_str, teacher, course_id, credit, location, office_time_str, office):
        self.__occur_time_str = occur_time_str

        self.name = name
        self.location = location
        self.description = "Teacher: " + teacher + \
                           "\nCourse ID: " + course_id + \
                           "\nCredit: " + credit + \
                           "\nOffice Time: " + office_time_str + \
                           "\nOffice: " + office

        print("Course %s initialized: occur time: %s, location: %s, description: %s"
              % (name, occur_time_str, location, self.description))

    def __get_occur_weeks(self):
        weeks_match = re.search(pattern=r'\((.+?)周(.*?)\)', string=self.__occur_time_str)

        if weeks_match:
            weeks_str = weeks_match.group(1)
            weeks = re.findall(pattern=r'[0-9]+', string=weeks_str)

            if '-' in weeks_str:
                start_week = int(weeks[0])
                end_week = int(weeks[1])
                return list(range(start_week, end_week + 1))

            elif ',' in weeks_str or '第' in weeks_str:
                return [int(i) for i in weeks]

        else:
            return list(range(1, 11))

    def __get_occur_time_list(self, weekday_table, course_time_table):
        occur_time_list = []

        for split_time_string in self.__occur_time_str.split():
            weekday_chinese_str = split_time_string[0]
            try:
                weekday = weekday_table[weekday_chinese_str]
            except KeyError:
                continue

            occur_indexes = re.findall(pattern=r'[0-9]+', string=split_time_string)
            start_index = int(occur_indexes[0]) - 1
            end_index = int(occur_indexes[1]) - 1

            occur_time_list_in_a_day = [datetime.combine(date=weekday, time=course_time_table[i])
                                        for i in range(start_index, end_index + 1)]
            occur_time_list.append(occur_time_list_in_a_day)

        return occur_time_list

    def get_events(self, weekday_table, course_time_table):
        # Create a alarm which will notify user 20 minutes before the occur time.
        alarm = Alarm()
        alarm.add(name='action', value='DISPLAY')
        alarm.add(name='trigger', value=timedelta(minutes=-25))
        alarm.add(name='description', value='Event reminder')

        occur_weeks = self.__get_occur_weeks()
        occur_time_list = self.__get_occur_time_list(weekday_table=weekday_table, course_time_table=course_time_table)

        print("Occur weeks %s generated for %s" % (str(occur_weeks), self.__occur_time_str))
        print("Occur time list %s generated for %s" %
              (str([str([occur_time.strftime('%Y-%m-%d %H:%M') for occur_time in i]) for i in occur_time_list]),
               self.__occur_time_str))

        events = []
        for occur_time_list_in_a_day in occur_time_list:
            for occur_time in occur_time_list_in_a_day:
                event = Event()
                event.add(name='summary', value=self.name)
                event.add(name='dtstart', value=occur_time + timedelta(weeks=occur_weeks[0] - 1))
                event.add(name='duration', value=timedelta(minutes=45))
                event.add(name='location', value=self.location)
                event.add(name='description', value=self.description)

                if len(occur_weeks) > 1:
                    interval = occur_weeks[1] - occur_weeks[0]
                    repeat_rule = {"freq": "weekly", "count": len(occur_weeks), "interval": interval}
                    event.add(name='rrule', value=repeat_rule)

                if occur_time == occur_time_list_in_a_day[0]:
                    event.add_component(alarm)

                events.append(event)

        print("%d events generated for Course %s\n" % (len(events), self.name))

        return events
