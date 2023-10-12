import sys

main_path = sys.argv[1]

# change the current working directory to the project root folder
sys.path.insert(0, main_path)

from dotenv import load_dotenv

load_dotenv()


from db import queries, transactions


lessons_res = queries.get_expired_archive_lessons_ids()

if lessons_res.failure:
    print("Failed to get expired lessons ids")
    exit(1)

for lesson in lessons_res.value:
    # Maybe add logging here
    transactions.delete_archived_lesson(lesson)
