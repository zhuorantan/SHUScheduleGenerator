import os
import datetime
import re
import icalendar
import getpass
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPCookieProcessor, Request
from http.cookiejar import CookieJar
from pytz import timezone
from Course import Course


course_time_table = (datetime.time(hour=8, minute=0, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=8, minute=55, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=10, minute=0, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=10, minute=55, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=12, minute=10, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=13, minute=5, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=14, minute=10, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=15, minute=5, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=16, minute=0, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=16, minute=55, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=18, minute=0, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=18, minute=55, tzinfo=timezone("Asia/Shanghai")),
                     datetime.time(hour=19, minute=50, tzinfo=timezone("Asia/Shanghai")))


class SHUScheduleGenerator:

    def __init__(self, begin_date_str):
        """

        :rtype: SHUScheduleGenerator
        :type begin_date_str: str
        """
        assert isinstance(begin_date_str, str)

        self.__base_url = 'http://xk.autoisp.shu.edu.cn:8080'

        monday = datetime.datetime.strptime(begin_date_str, '%Y.%m.%d').date()
        tuesday = monday + datetime.timedelta(1)
        wednesday = tuesday + datetime.timedelta(1)
        thursday = wednesday + datetime.timedelta(1)
        friday = thursday + datetime.timedelta(1)
        self.__weekday_table = {'一': monday, '二': tuesday, '三': wednesday, '四': thursday, '五': friday}

        # Create a opener with the ability to record cookies.
        self.__opener = build_opener(HTTPCookieProcessor(CookieJar()))

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

    def auth(self, student_id, student_password, validate_code):
        login_data = urlencode({"txtUserName": student_id, "txtPassword": student_password, "txtValiCode": validate_code}).encode("utf-8")
        self.__opener.open(self.__base_url, login_data)

    def generate(self, student_id):
        # This is the URL where the source of schedule come from.
        course_table_url = self.__base_url + '/StudentQuery/CtrlViewQueryCourseTable'
        # Create the request to get the raw data of schedule.
        request = Request(course_table_url, urlencode({"studentNo": student_id}).encode("utf-8"))

        # Get and return the raw data.
        data = self.__opener.open(request).read().decode("utf-8")

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
            events += course.get_events(self.__weekday_table, course_time_table)

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
print(u"""#---------------------------------------
#   Program:  SHUCourseSchedule
#   Version:  3.0
#   Author:   Jerome Tan
#   Date:     2017.3.26
#   Language: Python 2.7
#---------------------------------------
""")

# starting_date is the date of the first of day in the term.
print("""Please enter the starting date of your courses according to the following format:
yyyy.mm.dd""")
begin_date = input("Starting Date: ")

generator = SHUScheduleGenerator(begin_date_str=begin_date)

print("Please enter your student ID and your password")
identifier = input("Student ID: ")
password = getpass.getpass("Password: ")

generator.fetch_validate_code()

print("Please enter the validate code")
code = input("Validate code: ")

generator.auth(identifier, password, code)
generator.generate(identifier)
generator.delete_validate_code_file()
