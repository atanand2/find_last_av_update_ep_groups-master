import requests
import sys
from time import mktime, strptime
from datetime import datetime
import pytz
from prettytable import PrettyTable
from requests_toolbelt.multipart.encoder import MultipartEncoder

# PLEASE FILL YOUR API CREDENTIALS AND CLOUD DETAILS BELOW
Third_Party_API_Client_ID = "Your-AMP_Third_Party_API_Client_ID"  # 00xxxx00x00000x0x0x0
API_Key = "Your-AMP_API_Key"  # 0000xxx0-000x-00xx-0xx0-00xx00x00x00
Cloud = "AMP_Cloud-NAM_or_EU_or_APJC"  # NAM

# PLEASE FILL IN THE GROUP GUID DETAILS BELOW
# YOU CAN EDIT A GROUP ON AMP CONSOLE AND OBTAIN ITS GUID FROM THE ADDRESS-BAR OF THE BROWSER
group_uuid = "Enter_the_guid_of_the_group_you_want_to_monitor"

# PLEASE FILL IN THE HOURS BELOW
hour = 3

# VERIFYING INPUTS
if Cloud == "NAM" or Cloud == "nam" or Cloud == "Nam":
    cloud_base = "api.amp.cisco.com"
elif Cloud == "APJC" or Cloud == "apjc" or Cloud == "Apjc":
    cloud_base = "api.apjc.amp.cisco.com"
elif Cloud == "EU" or Cloud == "eu" or Cloud == "Eu":
    cloud_base = "api.eu.amp.cisco.com"
elif isinstance(hour, int) and 1 <= hour <= 24:
    pass
else:
    print(
        "ERROR: AMP Cloud or Requested Hours incorrect. Please Enter Correct Region for AMP Cloud: NAM/EU/APJC. or Hours beteen 1 to 24")
    sys.exit("Exiting...")

# QUERY URL
url = "https://"+Third_Party_API_Client_ID+":"+API_Key+"@"+cloud_base+"/v1/computers?group_guid%5B%5D="+group_uuid+"&limit=200&offset=0"

payload = {}
files = {}
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

response = requests.request("GET", url, headers=headers, data=payload, files=files)

# VERIFYING THE RESPONSE
if response.status_code != 200:
    print("ERROR: API Error with code " + str(response.status_code) + " and reason as " + str(
        response.reason) + ". Please re-verify the API credentials.")
    sys.exit("Exiting...")

jsondata = response.json()

# FETCHING THE HOSTNAME and LAST_SEEN LIST
host = []
lseen = []
avupdate = []
for item in range(0, len(jsondata['data'])):
    host.append(jsondata['data'][item].get("hostname"))
    lseen.append(jsondata['data'][item].get("last_seen"))
    if 'updated_at' in jsondata['data'][item].get("av_update_definitions"):
        avupdate.append(
            datetime.strptime(jsondata['data'][item].get("av_update_definitions").get('updated_at'),
                              '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%SZ'))
    else:
        avupdate.append(
            datetime.strptime(jsondata['data'][item].get("last_seen"),
                              '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%SZ'))

# FETCHING THE COMPUTERS WHICH HAVE LASTSEEN MORE THAN 2HOURS AGO
ctime = datetime.utcnow().isoformat()
server = {}
index = 0
while index < len(avupdate):
    a = strptime(avupdate[index], '%Y-%m-%dT%H:%M:%SZ')
    b = strptime(ctime, "%Y-%m-%dT%H:%M:%S.%f")
    a = mktime(a)
    b = mktime(b)
    d = b - a
    hours = int(d) / 3600
    time1 = datetime.fromisoformat(avupdate[index][:-1]).replace(tzinfo=pytz.utc)
    # FOLLOWING IS WHERE YOU SPECIFY THE HOURS AGO FOR LASTSEEN
    if hours < hour:
        # CONVERTING THE LAST SEEN TIME INTO PREFERRED TIMEZONE
        server[host[index]] = (
        str(time1.astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M%p')) + " IST",
        datetime.fromisoformat(lseen[index]).astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %I:%M%p %Z'))
    index = index + 1

# FORMATING THE OUTPUT IN MARKDOWN FOR TEAMS DISPLAY
if len(server) > 0:
    message = (str(len(
        server)) + " servers has updated the Tetra Definition within last {} hour in the Test Group.".format(hour))

    tab = PrettyTable(['Hostname', 'Last AV Update', 'Last Seen'])
    for key1, (last_av_update, last_seen) in server.items():
        tab.add_row([key1, last_av_update, last_seen])
    message = message + ("\n```\n")
    message = message + str(tab)
else:
    message = "No servers in Test Group are updated within {} hour.".format(hour)

# PLEASE INPUT THE DETAILS OF WEBEX ROOM AND WEBEX BOT
# YOU CAN USE THE roomid@webex.bot TO FIND THE ROOM ID
Room_id = 'Y2lzY29zcGFyazovL3VzL1JPT00vZDdiYWVhNjAtMmVlZS0xMWVmLWE1YmItYTVkNjgwOTJiMDQ0'
# YOU CAN CREATE A NEW WEBEX BOT AT https://developer.webex.com/my-apps/new/bot
bearer_token = "YWQwYzYxMDMtNjVlOS00ZjliLThkMzctZWRlN2VlYjJjMTFjNTM0ZWUxZWYtOGJi_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
auth_key = 'Bearer ' + bearer_token

send_message = 'https://api.ciscospark.com/v1/messages'

payload = MultipartEncoder({'roomId': Room_id, 'markdown': (message)})
headers0 = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': auth_key,
            'Content-Type': payload.content_type}
response = requests.post(send_message, headers=headers0, data=payload)

sys.exit("Exiting...")
