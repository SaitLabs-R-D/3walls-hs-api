from crontab import CronTab
import getpass as gt


def create_all_cron_tesks():

    cron = CronTab(user=gt.getuser())
    cron.remove_all()

    import sys

    python_path = sys.executable

    crr_dir = sys.path[0]

    job = cron.new(
        command=format_cron_tasks(python_path, crr_dir, "delete_expired_lessons.py")
    )
    # run every day at 00:00
    job.setall("0 0 * * *")

    cron.write()

    print("cron tasks created")


def format_cron_tasks(python_path: str, crr_dir: str, cron_tesk_file_path: str):
    # create a command syntex that run a python script that uses the current python interpreter and the current directory
    return f"{python_path} {crr_dir}/services/cron/{cron_tesk_file_path} {crr_dir}"
