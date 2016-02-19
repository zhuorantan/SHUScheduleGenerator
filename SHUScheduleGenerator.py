# -*- coding: utf-8 -*-
import urllib, urllib2, cookielib, os, re, getpass, datetime, pytz, icalendar

def init_calendar():
    global cal
    cal = icalendar.Calendar()
    cal.add("calscale", "GREGORIAN")
    cal.add("version", "2.0")
    cal.add("X-WR-CALNAME", "Course Content")
    cal.add("X-WR-TIMEZONE", "Asia/Shanghai")

def init_time_table(starting_date):
    global weekday_table, course_time_table
    monday = datetime.datetime.strptime(starting_date, "%Y.%m.%d").date()
    tuesday = monday + datetime.timedelta(1)
    wednesday = tuesday + datetime.timedelta(1)
    thursday = wednesday + datetime.timedelta(1)
    friday = thursday + datetime.timedelta(1)
    weekday_table = {"一": monday, "二": tuesday, "三": wednesday, "四": thursday, "五": friday}

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
    #This function logins using the given studentNo and password, and returns the opener

    def get_validate_code(validate_URL, directory):
        validate_code_image = opener.open(validate_URL).read()
        f = open(os.path.join(directory, "Validate Code Image.jpg"), "wb")
        f.write(validate_code_image)
        f.close()
        return raw_input("Please enter validate code: ")

    login_URL = "http://xk.autoisp.shu.edu.cn"
    validate_URL = "http://xk.autoisp.shu.edu.cn/Login/GetValidateCode?%20%20+%20GetTimestamp()"
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

    validate_code = get_validate_code(validate_URL, directory)
    login_data = urllib.urlencode({"txtUserName": studentNo, "txtPassword": password, "txtValiCode": validate_code})

    opener.open(login_URL, login_data)
    return opener

def get_data(opener, studentNo):
    course_table_URL = "http://xk.autoisp.shu.edu.cn/StudentQuery/CtrlViewQueryCourseTable"
    value = urllib.urlencode({"studentNo": studentNo})
    request = urllib2.Request(course_table_URL, value)
    data = opener.open(request).read()
    return data

def get_course_list(data):
    initial_data = re.findall(r"<tr>(.+?)</tr>", data, re.S)
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
    occur_time_list = []
    for splitted_time_string in time_string.split():
        occur_weeks = get_occur_weeks(splitted_time_string)
        start_week = occur_weeks[0]
        try:
            start_date = weekday_table[splitted_time_string[:3]] + datetime.timedelta(weeks = start_week - 1)
        except:
            start_date += datetime.timedelta(weeks = start_week - 1)
            del occur_time_list[-1]

        if get_occur_index(splitted_time_string):
            start_index, end_index = get_occur_index(splitted_time_string)
        course_time_list = course_time_table[start_index - 1: end_index]
        course_dates = []
        for time in course_time_list:
            course_dates.append(datetime.datetime.combine(start_date, time))

        occur_time_list.append((course_dates, occur_weeks))
    return occur_time_list

def get_occur_weeks(time_string):
    weeks = re.findall(r"\((.+?)周\)", time_string)
    if not weeks:
        weeks = re.findall(r"（(.+?)周）", time_string)
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
            start_week = int(week[0])
            end_week = int(week[2:])
            return list(range(start_week, end_week + 1))
        elif "," in week:
            repeat_weeks = []
            for week_index in week.split(","):
                repeat_weeks.append(int(week_index))
            return repeat_weeks
        elif "单" in week:
            return [1, 3, 5, 7, 9]
        elif "双" in week:
            return [2, 4, 6, 8, 10]
    except:
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
        name = course[2]
        location = course[7]
        occur_time_list = get_occur_time_list(course[6])
        description = "教师: " + course[4] + "\n课程号: " + course[1] + "\n学分: " + course[5] + "\n答疑时间: " + course[9] + "\n答疑地点: " + course[10]
        processed_course_list.append((name, location, occur_time_list, description))
    return processed_course_list

def create_events(course_list):
    def create_alarm():
        alarm = icalendar.Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("trigger", datetime.timedelta(minutes = -20))
        alarm.add("description", "Event reminder")
        return alarm

    def get_event(name, location, occur_time, description, rrule):
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
            interval = occur_weeks[1] - occur_weeks[0]
            for occur_time in occur_time_list[0]:
                rrule = {"freq": "weekly", "count": count, "interval": interval}
                event = get_event(course[0], course[1], occur_time, course[3], rrule)
                if is_first:
                    event.add_component(alarm)
                    is_first = False
                cal.add_component(event)



#-------- Program Interface ------------------
print u"""#---------------------------------------
#   Program:  SHUCouseContent
#   Version:  2.0
#   Author:   Jerome
#   Date:     2015.11.5
#   Language: Python 2.7
#---------------------------------------
"""
print """Please enter the starting date of your courses according to the following format:
yyyy.mm.dd"""
starting_date = raw_input("Starting Date: ")
print "Please enter the directory where you want to save your course table"
directory = raw_input("Directory: ")
print "Please enter your student ID and your password"
studentNo = raw_input("student ID: ")
password = getpass.getpass("Password: ")

opener = login(studentNo, password, directory)
data = get_data(opener, studentNo)

init_calendar()
init_time_table(starting_date)
course_list = get_course_list(data)
processed_course_list = process_course_list(course_list)
create_events(processed_course_list)

f = open(os.path.join(directory, "Course Content.ics"), "wb")
f.write(cal.to_ical())
f.close()
