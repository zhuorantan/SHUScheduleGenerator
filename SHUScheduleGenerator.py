# -*- coding: utf-8 -*-
import urllib, urllib2, cookielib, os, re, getpass, datetime, pytz, icalendar

def init_calendar():
    # Initialize the icalendar.
    global cal
    cal = icalendar.Calendar()
    cal.add("calscale", "GREGORIAN")
    cal.add("version", "2.0")
    cal.add("X-WR-CALNAME", "Course Schedule")
    cal.add("X-WR-TIMEZONE", "Asia/Shanghai")

def init_time_table(starting_date):
    global weekday_table, course_time_table

    # Convert Chinese number to weekday represented by date.
    monday = datetime.datetime.strptime(starting_date, "%Y.%m.%d").date()
    tuesday = monday + datetime.timedelta(1)
    wednesday = tuesday + datetime.timedelta(1)
    thursday = wednesday + datetime.timedelta(1)
    friday = thursday + datetime.timedelta(1)
    weekday_table = {"一": monday, "二": tuesday, "三": wednesday, "四": thursday, "五": friday}

    # Create a table containing the occur time of courses in a day.
    course_time_table = []
    course_time_table.append(datetime.time(8, 00, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(8, 55, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(10, 00, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(10, 55, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(12, 10, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(13, 05, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(14, 10, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(15, 05, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(16, 00, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(16, 55, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(18, 00, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(18, 55, tzinfo=pytz.timezone("Asia/Shanghai")))
    course_time_table.append(datetime.time(19, 50, tzinfo=pytz.timezone("Asia/Shanghai")))

def login(studentNo, password, directory):

    def get_validate_code(validate_URL, directory):
        # Request validate code image and write to the directory provided.
        validate_code_image = opener.open(validate_URL).read()
        f = open(os.path.join(directory, "Validate Code Image.jpg"), "wb")
        f.write(validate_code_image)
        f.close()
        # Return the validate code fetched from user's input.
        return raw_input("Please enter validate code: ")

    # These are the URLs used to login.
    login_URL = "http://xk.autoisp.shu.edu.cn"
    validate_URL = "http://xk.autoisp.shu.edu.cn/Login/GetValidateCode?%20%20+%20GetTimestamp"

    # Create a opener with the ability to record cookies.
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

    # Get validate code and post the information to login.
    validate_code = get_validate_code(validate_URL, directory)
    login_data = urllib.urlencode({"txtUserName": studentNo, "txtPassword": password, "txtValiCode": validate_code})
    opener.open(login_URL, login_data)
    return opener

def get_data(opener, studentNo):
    # This is the URL where the source of schedule come from.
    course_table_URL = "http://xk.autoisp.shu.edu.cn/StudentQuery/CtrlViewQueryCourseTable"
    # Create the request to get the raw data of schedule.
    request = urllib2.Request(course_table_URL, urllib.urlencode({"studentNo": studentNo}))

    # Get and return the raw data.
    data = opener.open(request).read()
    return data

def get_course_list(data):
    # First extract data from HTML.
    initial_data = re.findall(r"<tr>(.+?)</tr>", data, re.S)

    # Create a list of a list of course info.
    course_list = []
    for extracted_data in initial_data:
        items = re.findall(r"<td>(.*?)</td>", extracted_data, re.S)
        course = []
        for item in items:
            course.append(item.strip())
        if len(course) == 11:
            course_list.append(course)
    return course_list

def get_occur_time_list(time_string):
    # Get a list of occur time.
    occur_time_list = []
    for splitted_time_string in time_string.split():
        occur_weeks = get_occur_weeks(splitted_time_string)
        start_week = occur_weeks[0]
        try:
            # If the string is similar to 四3-4, then use [:3] to get the first Chinese character of the string which forms the index of weekday.
            start_date = weekday_table[splitted_time_string[:3]] + datetime.timedelta(weeks = start_week - 1)
        except:
            # The splitted_time_string can be something other than a string indicating time, maybe "男生篮球(基础)".
            start_date += datetime.timedelta(weeks = start_week - 1)
            # If splitted_time_string is something like "男生篮球(基础)", then the same time will be added again, so delete the time appended last time.
            del occur_time_list[-1]

        # If possible, get the index of the course in a day.
        if get_occur_index(splitted_time_string):
            start_index, end_index = get_occur_index(splitted_time_string)
        # Get the time according to the index.
        course_time_list = course_time_table[start_index - 1: end_index]

        # Combine time and date.
        course_dates = []
        for time in course_time_list:
            course_dates.append(datetime.datetime.combine(start_date, time))

        occur_time_list.append((course_dates, occur_weeks))
    return occur_time_list

def get_occur_weeks(time_string):
    # The most common time_string that include occur weeek are something like "四7-8 (1,6周)".
    weeks = re.findall(r"\((.+?)周\)", time_string)
    if not weeks:
        # There are some that use Chinese full width parenthese.
        weeks = re.findall(r"（(.+?)周）", time_string)

    # Some indicate odd or even weeks.
    if not weeks:
        try:
            weeks = [re.search(r"(.+?)单", time_string).group()[-3:]]
        except:
            pass
    if not weeks:
        try:
            weeks = [re.search(r"(.+?)双", time_string).group()[-3:]]
        except:
            pass
    try:
        week = weeks[0]
        if "-" in week:
            # If there is a "-" in the string, it means from start_week to end_week.
            start_week = int(week[0])
            end_week = int(week[2:])
            return list(range(start_week, end_week + 1))
        elif "," in week:
            # If there is a "," in the string, it means weekA and weekB.
            repeat_weeks = []
            for week_index in week.split(","):
                repeat_weeks.append(int(week_index))
            return repeat_weeks
        elif "单" in week:
            return [1, 3, 5, 7, 9]
        elif "双" in week:
            return [2, 4, 6, 8, 10]
    except:
        # Most courses don't include occur week which means every week in the term.
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

def get_occur_index(time_string):
    course_index_string = re.sub(r"\((.+?)\)", "", time_string[3:])
    is_start = True
    start_index = 0
    end_index = 0
    for course_index in course_index_string:
        try:
            if is_start:
                start_index = start_index * 10 + int(course_index)
            else:
                end_index = end_index * 10 + int(course_index)
        except:
            if course_index == "-":
                is_start = False
    if start_index and end_index:
        return (start_index, end_index)

def process_course_list(course_list):
    processed_course_list = []
    for course in course_list:
        # Get following information from course_list.
        name = course[2]
        location = course[7]
        occur_time_list = get_occur_time_list(course[6])
        description = "教师: " + course[4] + "\n课程号: " + course[1] + "\n学分: " + course[5] + "\n答疑时间: " + course[9] + "\n答疑地点: " + course[10]
        processed_course_list.append((name, location, occur_time_list, description))
    return processed_course_list

def create_events(course_list):
    def create_alarm():
        # Create a alarm which will notify user 20 minutes before the occur time.
        alarm = icalendar.Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("trigger", datetime.timedelta(minutes = -20))
        alarm.add("description", "Event reminder")
        return alarm

    def get_event(name, location, occur_time, description, rrule):
        # Create an calendar event with above information.
        event = icalendar.Event()
        event.add("summary", name)
        event.add("dtstart", occur_time)
        event.add("duration", datetime.timedelta(minutes = 45))
        event.add("location", location)
        event.add("description", description)
        event.add("rrule", rrule)
        return event

    alarm = create_alarm()
    for course in course_list:
        for occur_time_list in course[2]:
            is_first = True
            occur_weeks = occur_time_list[1]
            count = len(occur_weeks)
            # interval is the number of weeks between two occur time. If the course occurs every week, then the interval is 1.
            interval = occur_weeks[1] - occur_weeks[0]
            for occur_time in occur_time_list[0]:
                rrule = {"freq": "weekly", "count": count, "interval": interval}
                event = get_event(course[0], course[1], occur_time, course[3], rrule)

                # Most courses have two teaching periods, the alarm only notify before the first teaching period.
                if is_first:
                    event.add_component(alarm)
                    is_first = False
                cal.add_component(event)



#-------- Program Interface ------------------
print u"""#---------------------------------------
#   Program:  SHUCouseSchedule
#   Version:  2.1
#   Author:   Jerome Tan
#   Date:     2015.11.5
#   Language: Python 2.7
#---------------------------------------
"""

# starting_date is the date of the first of day in the term.
print """Please enter the starting date of your courses according to the following format:
yyyy.mm.dd"""
starting_date = raw_input("Starting Date: ")

# This directory will be used to store validate code image and output the .ics file.
print "Please enter the directory where you want to save your course table"
directory = raw_input("Directory: ")

print "Please enter your student ID and your password"
studentNo = raw_input("student ID: ")
password = getpass.getpass("Password: ")

# Login and get the URL opener with login information.
opener = login(studentNo, password, directory)
# Get raw data.
data = get_data(opener, studentNo)

# Initialize calendar and time table.
init_calendar()
init_time_table(starting_date)

# Abstract course list from raw HTML.
course_list = get_course_list(data)
# Process the data abstracted from raw HTML.
processed_course_list = process_course_list(course_list)
# Create calendar events.
create_events(processed_course_list)

# Write the .ics file to the directory provided by user.
f = open(os.path.join(directory, "Course Schedule.ics"), "wb")
f.write(cal.to_ical())
f.close()
