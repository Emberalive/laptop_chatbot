from crontab import CronTab

cron = CronTab(user=True)
job = cron.new(command="python3 /run_all.py")
job.minute.every(5) # run every 5 minutes
# job.day.on(1) # runs every 1st of the month

cron.write() # saving the job