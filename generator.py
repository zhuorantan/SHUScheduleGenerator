import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, time
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPCookieProcessor, Request

from icalendar import Calendar
from pytz import timezone

from course import Course


def cros_platopen(filepath):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filepath))
    elif os.name == 'nt':
        os.startfile(filepath)  # IDE will notice u that os.py under Linux doesn't have this function support.
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))


class Generator:

    def __init__(self, begin_date_str):
        self.__base_url = "http://xk.autoisp.shu.edu.cn"

        monday = datetime.strptime(begin_date_str, '%Y.%m.%d').date()
        tuesday = monday + timedelta(days=1)
        wednesday = tuesday + timedelta(days=1)
        thursday = wednesday + timedelta(days=1)
        friday = thursday + timedelta(days=1)
        self.__weekday_table = {'一': monday, '二': tuesday, '三': wednesday, '四': thursday, '五': friday}

        self.__course_time_table = (time(hour=8, minute=0, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=8, minute=55, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=10, minute=0, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=10, minute=55, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=12, minute=10, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=13, minute=5, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=14, minute=10, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=15, minute=5, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=16, minute=0, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=16, minute=55, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=18, minute=0, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=18, minute=55, tzinfo=timezone("Asia/Shanghai")),
                                    time(hour=19, minute=50, tzinfo=timezone("Asia/Shanghai")))

        # Create a opener with the ability to record cookies.
        self.__opener = build_opener(HTTPCookieProcessor(CookieJar()))

        self.__validate_img_path = os.path.join(os.getcwd(), "validate_code.jpg")

        self.term_index = 0
        self.terms_and_ports = []

        ports = (80, 8080)
        for port in ports:
            url = '%s:%d' % (self.__base_url, port)
            data = self.__opener.open(url).read().decode('utf-8')
            term = re.search(pattern=r'<div style="color: Red; font-size: 26px; text-align: center;">(.+?)</div>',
                             string=data).group(1)
            self.terms_and_ports.append((term, port))

    def __get_url(self):
        port = self.terms_and_ports[self.term_index][1]
        return '%s:%d' % (self.__base_url, port)

    def get_terms(self):
        return [term_and_port[0] for term_and_port in self.terms_and_ports]

    def fetch_validate_code(self):
        validate_img_url = self.__get_url() + "/Login/GetValidateCode?%20%20+%20GetTimestamp"
        validate_code_image = self.__opener.open(validate_img_url).read()

        # Request validate code image and write to the directory provided.
        f = open(file=self.__validate_img_path, mode="wb")
        f.write(validate_code_image)
        f.close()

        print("Validate image saved to %s" % self.__validate_img_path)

        cros_platopen(self.__validate_img_path)

    def delete_validate_code_file(self):
        os.remove(path=self.__validate_img_path)

    def auth(self, student_id, password, validate_code):
        login_data = urlencode({'txtUserName': student_id,
                                'txtPassword': password,
                                'txtValiCode': validate_code}).encode('utf-8')
        self.__opener.open(fullurl=self.__get_url(), data=login_data)

    def generate(self, student_id):
        # This is the URL where the source of schedule come from.
        course_table_url = self.__get_url() + "/StudentQuery/CtrlViewQueryCourseTable"
        # Create the request to get the raw data of schedule.
        request = Request(url=course_table_url, data=urlencode({'studentNo': student_id}).encode('utf-8'))

        # Get and return the raw data.
        data = self.__opener.open(request).read().decode('utf-8')

        # First extract data from HTML.
        initial_data = re.findall(pattern=r"<tr>(.+?)</tr>", string=data, flags=re.S)

        # Create a list of a list of course info.
        course_list = []
        for extracted_data in initial_data:
            items = re.findall(pattern=r"<td>(.*?)</td>", string=extracted_data, flags=re.S)
            course_items = [item.strip() for item in items]

            if len(course_items) != 11:
                continue

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
            events += course.get_events(self.__weekday_table, self.__course_time_table)

        cal = Calendar()
        cal.add("calscale", "GREGORIAN")
        cal.add("version", "2.0")
        cal.add("X-WR-CALNAME", "SHU Course Schedule")
        cal.add("X-WR-TIMEZONE", "Asia/Shanghai")

        for event in events:
            cal.add_component(event)

        cal_path = os.path.join(os.getcwd(), "Course Schedule.ics")
        f = open(cal_path, "wb")
        f.write(cal.to_ical())
        f.close()
        cros_platopen(cal_path)
