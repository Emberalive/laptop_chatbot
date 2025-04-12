from crontab import CronTab

cron = CronTab(user=True)
job = cron.new(command="python /home/samuel/laptop_chat_bot/server_side/run_all.py >> /home/samuel/laptop_chat_bot/server_side/out/output_log.log 2>&1")
job.hour.every(5) # run every 2 hours
#job.day.on(1) # runs every 1st of the month

cron.write() # saving the job
print("crontab added successfully")
