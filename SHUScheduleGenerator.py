# -*- coding: utf-8 -*-
import os
import datetime
import pytz
import urllib
import urllib2
import cookielib
import re
import icalendar
import getpass


class Course:
    __course_time_table = (datetime.time(8, 00, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(8, 55, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(10, 00, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(10, 55, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(12, 10, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(13, 05, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(14, 10, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(15, 05, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(16, 00, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(16, 55, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(18, 00, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(18, 55, tzinfo=pytz.timezone("Asia/Shanghai")),
                           datetime.time(19, 50, tzinfo=pytz.timezone("Asia/Shanghai")))

    def __init__(self, name, occur_time_str, teacher, course_id, credit, location, office_time_str, office):
        self.name = name
        self.location = location
        self.__occur_time_str = occur_time_str
        self.description = 'Teacher: ' + teacher + \
                           "\nCourse ID: " + course_id + \
                           "\nCredit: " + credit +\
                           "\nOffice Time: " + office_time_str +\
                           "\nOffice: " + office

    def __get_occur_weeks(self):
        search = re.search(r'\((.+?)周(.*?)\)', self.__occur_time_str)
        if search:
            match = search.group(1)
            weeks = re.findall(r'[0-9]+', match)
            if '-' in match:
                start_week = int(weeks[0])
                end_week = int(weeks[1])
                return list(range(start_week, end_week + 1))
            elif ',' in match or '第' in match:
                return [int(i) for i in weeks]
        else:
            return list(range(1, 11))

    def __get_occur_indexes(self, weekday_table):
        # Get a list of occur time.
        occur_indexes = []
        for split_time_string in self.__occur_time_str.split():
            try:
                weekday = weekday_table[split_time_string[:3]]
            except:
                continue

            match = re.findall(r'[0-9]+', split_time_string)
            start_index = int(match[0]) - 1
            end_index = int(match[1]) - 1

            occur_index = []
            for i in range(start_index, end_index + 1):
                course_index = self.__course_time_table[i]
                occur_index.append(datetime.datetime.combine(weekday, course_index))
            occur_indexes.append(occur_index)

        return occur_indexes

    def get_events(self, weekday_table):
        # Create a alarm which will notify user 20 minutes before the occur time.
        alarm = icalendar.Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("trigger", datetime.timedelta(minutes=-20))
        alarm.add("description", "Event reminder")

        weeks = self.__get_occur_weeks()
        indexes = self.__get_occur_indexes(weekday_table)

        events = []
        for index in indexes:
            for time in index:
                event = icalendar.Event()
                event.add('summary', self.name)
                event.add('dtstart', time + + datetime.timedelta(weeks=weeks[0] - 1))
                event.add('duration', datetime.timedelta(minutes=45))
                event.add('location', self.location)
                event.add('description', self.description)

                if len(weeks) > 1:
                    interval = weeks[1] - weeks[0]
                    repeat_rule = {"freq": "weekly", "count": len(weeks), "interval": interval}
                    event.add('rrule', repeat_rule)

                if time == index[0]:
                    event.add_component(alarm)

                events.append(event)

        return events


class SHUScheduleGenerator:

    def __init__(self, begin_date_str):
        """

        :rtype: SHUScheduleGenerator
        :type begin_date_str: str
        """
        assert isinstance(begin_date_str, str)

        self.__base_url = 'http://xk.autoisp.shu.edu.cn:8080'

        # Convert Chinese number to weekday represented by date.
        monday = datetime.datetime.strptime(begin_date_str, '%Y.%m.%d').date()
        tuesday = monday + datetime.timedelta(1)
        wednesday = tuesday + datetime.timedelta(1)
        thursday = wednesday + datetime.timedelta(1)
        friday = thursday + datetime.timedelta(1)
        self.__weekday_table = {'一': monday, '二': tuesday, '三': wednesday, '四': thursday, '五': friday}

        # Create a opener with the ability to record cookies.
        self.__opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

        self.__validate_img_path = os.path.join(os.getcwd(), "validate_code.jpg")

    def fetch_validate_code(self):
        validate_img_url = self.__base_url + '/Login/GetValidateCode?%20%20+%20GetTimestamp'
        validate_code_image = self.__opener.open(validate_img_url).read()

        # Request validate code image and write to the directory provided.
        f = open(self.__validate_img_path, "wb")
        f.write(validate_code_image)
        f.close()

        os.system('open \'' + self.__validate_img_path + '\'')

    def delete_validate_code_file(self):
        os.remove(self.__validate_img_path)

    def auth(self, student_id, password, validate_code):
        login_data = urllib.urlencode({"txtUserName": student_id, "txtPassword": password, "txtValiCode": validate_code})
        self.__opener.open(self.__base_url, login_data)

    def generate(self, student_id):
        # This is the URL where the source of schedule come from.
        course_table_url = self.__base_url + '/StudentQuery/CtrlViewQueryCourseTable'
        # Create the request to get the raw data of schedule.
        request = urllib2.Request(course_table_url, urllib.urlencode({"studentNo": student_id}))

        # Get and return the raw data.
        data = self.__opener.open(request).read()

        # First extract data from HTML.
        initial_data = re.findall(r"<tr>(.+?)</tr>", data, re.S)

        # Create a list of a list of course info.
        course_list = []
        for extracted_data in initial_data:
            items = re.findall(r"<td>(.*?)</td>", extracted_data, re.S)
            course_items = []
            for item in items:
                course_items.append(item.strip())
            if len(course_items) == 11:
                course = Course(course_items[2],
                                course_items[6],
                                course_items[4],
                                course_items[1],
                                course_items[5],
                                course_items[7],
                                course_items[9],
                                course_items[10])
                course_list.append(course)

        events = []
        for course in course_list:
            events += course.get_events(self.__weekday_table)

        cal = icalendar.Calendar()
        cal.add("calscale", "GREGORIAN")
        cal.add("version", "2.0")
        cal.add("X-WR-CALNAME", "Course Schedule")
        cal.add("X-WR-TIMEZONE", "Asia/Shanghai")

        for event in events:
            cal.add_component(event)

        cal_path = os.path.join(os.getcwd(), "Course Schedule.ics")
        f = open(cal_path, "wb")
        f.write(cal.to_ical())
        os.system('open \'' + cal_path + '\'')


# -------- Program Interface ------------------
print u"""#---------------------------------------
#   Program:  SHUCourseSchedule
#   Version:  3.0
#   Author:   Jerome Tan
#   Date:     2017.3.26
#   Language: Python 2.7
#---------------------------------------
"""

# starting_date is the date of the first of day in the term.
print """Please enter the starting date of your courses according to the following format:
yyyy.mm.dd"""
begin_date_str = raw_input("Starting Date: ")

generator = SHUScheduleGenerator(begin_date_str=begin_date_str)

print "Please enter your student ID and your password"
student_id = raw_input("Student ID: ")
password = getpass.getpass("Password: ")

generator.fetch_validate_code()

print "Please enter the validate code"
validate_code = raw_input("Validate code: ")

generator.auth(student_id, password, validate_code)
generator.generate(student_id)
generator.delete_validate_code_file()
