import requests
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
lines = []
annotations = []

datetimeformat = "%Y-%m-%dT%H:%M:%SZ"

user_ids = {
    "Matisse": {"id": 1385143, "color": "blue"},
    "Luka": {"id": 1345102, "color": "red"},
    "Erik": {"id": 815026, "color": "green"},
    "Mathias": {"id": 1167648, "color": "yellow"},
    "Jan-Willem": {"id": 1491301, "color": "pink"},
}

# Converts Timedelta to hours
def convert_to_total_minutes(td):
    return td.total_seconds() / 60 / 60

# For each user, plot each month's hours of online ATC
for user in user_ids.keys():
    print(f"Getting data for {user}")
    id = user_ids[user]["id"]
    url = f"https://api.vatsim.net/v2/members/{id}/atc?limit=100"

    payload = {}
    headers = {'Accept': 'application/json'}

    # Contains all data retrieved from API
    response = requests.request("GET", url, headers=headers, data=payload)
    data_json = json.loads(response.text)

    data_dict = []  # Contains only the data we want

    # For each connection to vatsim that this user made:
    for connection in data_json["items"]:
        connection = connection["connection_id"]

        # We are only interested in ATC connections
        if connection["callsign"].endswith(("_CTR", "_FSS", "_DEL", "_GND", "_TWR", "_APP", "_DEP")):
            date_start = datetime.strptime(connection["start"], datetimeformat)
            date_end = datetime.strptime(connection["end"], datetimeformat)

            length = date_end - date_start  # Get duration of ATC session

            data = {
                "start": date_start,  # Will be used to group sessions per month
                "Session_Duration_In_hours": convert_to_total_minutes(length)  # Session duration
            }

            data_dict.append(data)

    # Create a df from all the necessary data
    df = pd.DataFrame(data_dict)
    df.set_index('start', inplace=True)

    # Group by month using pd.Grouper
    df = df.groupby(pd.Grouper(freq='M')).sum()

    # Plot the data
    line, = ax.plot(df.index, df["Session_Duration_In_hours"], marker='o', linestyle='-', color=user_ids[user]["color"], label=user)
    lines.append(line)

    # Get data used for annotation
    max_value_index = df['Session_Duration_In_hours'].idxmax()
    max_value = df.loc[max_value_index, 'Session_Duration_In_hours']

    # Annotate user and year and month of highest total hours
    annotation = ax.annotate(f'{user}\n{max_value_index.strftime("%Y-%m")}', 
                xy=(max_value_index, max_value), 
                xytext=(max_value_index + pd.DateOffset(days=5), max_value + 5), 
                arrowprops=dict(facecolor='black', arrowstyle='->'),
                fontsize=8,
                horizontalalignment='left', verticalalignment='bottom')
    
    annotations.append((line,annotation))

# Create a function that toggles the visibility of lines and annotations
def on_pick(event):
    legline = event.artist
    origline = next(line for line in lines if line.get_label() == legline.get_label())
    visible = not origline.get_visible()
    origline.set_visible(visible)
    
    # Toggle the visibility of the corresponding annotation
    for line, annotation in annotations:
        if line == origline:
            annotation.set_visible(visible)
            break
    
    legline.set_alpha(1.0 if visible else 0.2)
    fig.canvas.draw()

# Create legend and set up the event connection
legend = ax.legend(loc='upper left', shadow=True)
for legline in legend.get_lines():
    legline.set_picker(5)  # Tolerance in points

fig.canvas.mpl_connect('pick_event', on_pick)

# Add general graph items
plt.title('Total Hours by Month')
plt.xlabel('Month')
plt.ylabel('Total hours')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()
