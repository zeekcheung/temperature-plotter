from datetime import datetime, timedelta
import random
import subprocess


# Helper function to add small noise to temperature values
def add_noise(temp, noise_level=1.0):
    return temp + random.uniform(-noise_level, noise_level)


# Function to generate daily temperature segments
def generate_daily_temperature():
    # First segment: 08:00 - 12:00 (Increasing)
    start_time = "08:00"
    end_time1 = "12:00"
    slope1 = random.uniform(1, 5)  # Positive slope
    intercept1 = random.uniform(15, 25)

    # Generate start and end temperatures for the first segment
    temp_12 = slope1 * 12 + intercept1

    # Second segment: 12:00 - 16:00 (Constant temperature)
    start_time2 = "12:00"
    end_time2 = "16:00"
    temp_16 = temp_12  # Constant temperature equal to end of first segment

    # Third segment: 16:00 - 20:00 (Decreasing)
    start_time3 = "16:00"
    end_time3 = "20:00"
    slope3 = random.uniform(-5, -1)  # Negative slope
    intercept3 = temp_16 - slope3 * 16

    # Add noise level
    noise_level = random.uniform(0.5, 1.5)

    # Format the segments with noise
    segment1 = f"{start_time} {end_time1} {slope1}*t+{intercept1} {noise_level}"
    segment2 = f"{start_time2} {end_time2} 0*t+{temp_16} {noise_level}"
    segment3 = f"{start_time3} {end_time3} {slope3}*t+{intercept3} {noise_level}"

    return [segment1, segment2, segment3]


# Generate data for each day from Jan 1, 2024, to today
def generate_temperature_data(start_date, end_date):
    current_date = start_date
    all_data = []

    while current_date <= end_date:
        daily_segments = generate_daily_temperature()
        all_data.append((current_date.strftime("%Y-%m-%d"), daily_segments))
        current_date += timedelta(days=1)

    return all_data


# Define date range
start_date = datetime(2024, 11, 1)
end_date = datetime.now()

# Generate and print temperature data
temperature_data = generate_temperature_data(start_date, end_date)
for date, segments in temperature_data:
    # print(f"Date: {date}")
    # for segment in segments:
    #     print(f"  {segment}")
    # print()
    title = date + " 温度变化图"
    output_dir = "图片"
    args = [title, output_dir] + segments
    subprocess.run(["python", "main.py"] + args)
