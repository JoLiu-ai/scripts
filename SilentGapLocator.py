"""

该脚本旨在解析SRT字幕文件中的时间戳，并检测连续字幕条目之间的间隔。如果间隔超过设定的阈值（默认为10秒），脚本会记录下该间隔的开始和结束时间，方便用户定位音频识别缺失或未捕捉的部分。


This script is designed to parse timestamps from SRT subtitle files and detect gaps between consecutive subtitle entries. 
If the gap exceeds a defined threshold (default is 10 seconds), 
the script logs the start and end times of the gap, allowing users to identify missing or unrecognized portions in the audio transcription.
"""

from datetime import datetime

# Parse timestamps from SRT file content
def parse_srt_timestamps(srt_text):
    timestamps = []  # List to store extracted timestamps
    lines = srt_text.split('\n')  # Split the content into lines
    
    # Loop through each line to find timestamp patterns
    for line in lines:
        if '-->' in line:  # Identify lines with timestamp ranges
            start, end = line.split(' --> ')  # Split start and end times
            timestamps.append((start.strip(), end.strip()))  # Store as tuples
    
    return timestamps

# Calculate gaps between consecutive subtitle timestamps
def calculate_gaps(timestamps, threshold_seconds=10):
    time_format = "%H:%M:%S,%f"  # Standard SRT timestamp format
    gaps = []  # List to store detected gaps
    
    # Iterate over the timestamps list to compare consecutive entries
    for i in range(len(timestamps) - 1):
        end_time = datetime.strptime(timestamps[i][1], time_format)  # End time of current entry
        next_start_time = datetime.strptime(timestamps[i+1][0], time_format)  # Start time of next entry
        
        gap = (next_start_time - end_time).total_seconds()  # Calculate gap in seconds
        if gap > threshold_seconds:  # Check if gap exceeds the threshold
            gaps.append((timestamps[i][1], timestamps[i+1][0], gap))  # Store end time, next start time, and gap duration
    
    return gaps

# Extract timestamps from SRT content
timestamps = parse_srt_timestamps(srt_content)
# Identify gaps exceeding 10 seconds
gaps = calculate_gaps(timestamps)

# Output the gaps list with start and end times along with the gap duration
gaps
