import getpass
from generator import Generator


print(u"""#---------------------------------------
#   Program:  SHUCourseSchedule
#   Version:  3.0
#   Author:   Jerome
#   Date:     2017.4.4
#   Language: Python 3.6
#---------------------------------------
""")

# starting_date is the date of the first of day in the term.
print("Entry the starting date of your courses in the following format:\nyyyy.mm.dd")
begin_date = input("Starting Date: ")

print("Input the port to get course table")
port = int(input("Port: "))

generator = Generator(begin_date_str=begin_date, port=port)

print("Enter student ID and password")
student_id = input("Student ID: ")
password = getpass.getpass("Password: ")

generator.fetch_validate_code()

print("Entry the validate code")
validate_code = input("Validate code: ")

generator.auth(student_id=student_id, password=password, validate_code=validate_code)
generator.generate(student_id=student_id)
generator.delete_validate_code_file()
