import subprocess

# List of scripts in the order they should run
scripts = ["scrapers/pyScraper1.py", "scrapers/pyScraper2.py", "database_persistence.py"]

try:
    for script in scripts:
        print(f"Running {script}...")
        result = subprocess.run(["python3", script], capture_output=True, text=True)

        # Print the output of the script
        print(result.stdout)
        print(result.stderr)

        # Check if the script failed
        if result.returncode != 0:
            print(f"Error: {script} exited with code {result.returncode}. Stopping execution.")
            break
except Exception as e:
    print(f"An error occurred: {e}")

print("All scripts completed.")
