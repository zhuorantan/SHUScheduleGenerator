import getpass
from generator import Generator


print(u"""#---------------------------------------
#   Program:  SHUScheduleGenerator
#   Version:  3.0
#   Author:   Jerome
#   Date:     2017.4.4
#   Language: Python 3.6
#---------------------------------------
""")

# starting_date is the date of the first of day in the term.
print("Entry the starting date of your courses in the following format:\nyyyy.mm.dd")
begin_date = input("Starting Date: ")

generator = Generator(begin_date_str=begin_date)

print("Choose the term")
for index, term in enumerate(generator.get_terms()):
    print('%d. %s' % (index + 1, term))

term_index = int(input("Term: ")) - 1
generator.term_index = term_index
print(generator.term_index)

print("Enter student ID and password")
student_id = input("Student ID: ")
password = getpass.getpass("Password: ")

generator.fetch_validate_code()

print("Entry the validate code")
validate_code = input("Validate code: ")

generator.auth(student_id=student_id, password=password, validate_code=validate_code)
generator.generate(student_id=student_id)
generator.delete_validate_code_file()
