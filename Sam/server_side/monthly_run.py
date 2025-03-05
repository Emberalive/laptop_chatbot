from crontab import CronTab

cron = CronTab(user=True)
job = cron.new(command="python3 /home/samuel/Documents/2_Brighton/sem2/GroupProject/laptop_chatbot/Sam/server_side/run_all.py >> /home/samuel/Documents/2_Brighton/sem2/GroupProject/laptop_chatbot/Sam/server_side/out/output_.log 2>&1")
job.minute.every(5) # run every 5 minutes
# job.day.on(1) # runs every 1st of the month

cron.write() # saving the job