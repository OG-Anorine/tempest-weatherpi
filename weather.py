# This is a heavily modified version of e_paper_weather_display
# All data has been tweaked to be pulled from TempestWX
# Additional APIs include NWS, freeastroapi, and US Naval Observatory

#Global settings:
wx_station = 'Station ID Here' # Tempest weather station ID
wx_token = 'Tempest API Token' # Tempest API token
nwszone = 'NWS County Zone' # Zones can be easily found at https://www.aprs-is.net/WX/NWSCodes.aspx - Note: Remove '_' from WX Code
moon_token = 'Free Astro API Token' # Token for https://www.freeastroapi.com, free account is plenty of lookups per day
latitude = 'Your Latitude'
longitude = 'Your Longitude'
tz_offset = 'Timezone offset not including DST' # Your standard timezone offset, not DST offset
phase = None # Declares the moon phase to allow limiting API calls
memes = 1 # Enter 1 for on, 0 (zero, not the letter O) for off
wind_thresh = 15 # Wind gust speed in MPH to trigger windy icon
super_cold = -10 # Triggers Ice King meme if feels like is equal to or lower than set value
tout = 3 # Timeout for accessing data. If the error screen comes up too often increase this time

import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
icondir = os.path.join(picdir, 'icon')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')

# Search lib folder for display driver modules
sys.path.append('lib')

#Import drivers for 7.5" e-ink display
from waveshare_epd import epd7in5_V2
epd = epd7in5_V2.EPD()

#Error control
ec = 0
with open('reboot.txt', 'r') as file:
    reboot = file.read()

from datetime import datetime, timedelta
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

import requests, urllib.request, json
from io import BytesIO

import re

#API URLs
wx_url = 'https://swd.weatherflow.com/swd/rest/better_forecast?station_id=' + wx_station + '&units_temp=f&units_wind=mph&units_pressure=inhg&units_precip=in&units_distance=mi&token=' + wx_token
nws_url = 'https://api.weather.gov/alerts/active?zone=' + nwszone
moon_date = current_date = datetime.now().strftime("%Y-%m-%d")
moon_b_url = 'https://aa.usno.navy.mil/api/rstt/oneday?date=' + moon_date + '&coords=' + latitude + ', ' + longitude + '&tz=' + tz_offset + '&dst=true'
moon_url = "https://astro-api-1qnc.onrender.com/api/v1/moon/phase"
params = {
    "lat": latitude,
    "lon": longitude,
    "include_eclipse": "true",
    "include_special": "true",
    "include_rise_set": "true"
}

headers = {
    "x-api-key": moon_token
}

#T+1 Lunar parameters
moon_date_p1 = (datetime.now() + timedelta(days=1))
params_p1 = {
    "date": moon_date_p1,
    "lat": latitude,
    "lon": longitude,
    "include_eclipse": "true",
    "include_special": "true",
    "include_rise_set": "true"
}

moon_bp1_url = 'https://aa.usno.navy.mil/api/rstt/oneday?date=' + (moon_date_p1.strftime("%Y-%m-%d")) + '&coords=' + latitude + ', ' + longitude + '&tz=' + tz_offset + '&dst=true'

class HTTPError(Exception):
    pass

# define funciton for writing image and sleeping for 5 min.
def write_to_screen(image, sleep_seconds):
    print(str(datetime.now()) + ' Writing to screen.')
    # Write to screen
    h_image = Image.new('1', (epd.width, epd.height), 255)
    # Open the template
    screen_output_file = Image.open(os.path.join(picdir, image))
    # Initialize the drawing context with template as background
    h_image.paste(screen_output_file, (0, 0))
    epd.init()
    epd.display(epd.getbuffer(h_image))
    # Sleep
    time.sleep(2)
    epd.sleep()
    print(str(datetime.now()) + ' Sleeping for ' + str(sleep_seconds) +' seconds.')
    time.sleep(sleep_seconds)

# define function for displaying error
def display_error(error_source):
    if error_source == 'API':
        error_image = Image.open(os.path.join(picdir, 'api_error_template.png'))
        # Initialize the drawing
        draw = ImageDraw.Draw(error_image)
        current_time = datetime.now().strftime('%H:%M')
        draw.text((590, 430), 'Last Refresh: ' + str(current_time), font = font23, fill=black)
        error_image_file = 'error.png'
        error_image.save(os.path.join(picdir, error_image_file))
        error_image.close()
        write_to_screen(error_image_file, 300)
    if error_source == 'HTTP':
        error_image = Image.open(os.path.join(picdir, 'http_error_template.png'))
        # Initialize the drawing
        draw = ImageDraw.Draw(error_image)
        current_time = datetime.now().strftime('%H:%M')
        draw.text((590, 430), 'Last Refresh: ' + str(current_time), font = font23, fill=black)
        error_image_file = 'error.png'
        error_image.save(os.path.join(picdir, error_image_file))
        error_image.close()
        write_to_screen(error_image_file, 1800)        
    else:
        error_image = Image.open(os.path.join(picdir, 'error_template.png'))
        # Initialize the drawing
        draw = ImageDraw.Draw(error_image)
        current_time = datetime.now().strftime('%H:%M')
        draw.text((590, 430), 'Last Refresh: ' + str(current_time), font = font23, fill=black)
        error_image_file = 'error.png'
        error_image.save(os.path.join(picdir, error_image_file))
        error_image.close()
        write_to_screen(error_image_file, 30)

#Draw boxes for centering text
def create_image(size, bgColor, message, font, fontColor):
    W, H = size
    image = Image.new('RGB', size, bgColor)
    draw = ImageDraw.Draw(image)
    _, _, w, h = draw.textbbox((0, 0), message, font=font)
    draw.text(((W-w)/2, (H-h)/2), message, font=font, fill=fontColor)
    return image

#Draw boxes for centering text with image on right for World 2-Desert
def create_image_w2(size, bgColor, message, font, fontColor):
    W, H = size
    image = Image.new('RGB', size, bgColor)
    draw = ImageDraw.Draw(image)
    _, _, w, h = draw.textbbox((0, 0), message, font=font)
    draw.text((((W-w)/2)-20, (H-h)/2), message, font=font, fill=fontColor)
    return image

def create_feelslike_image(feels_file=None, paste_icon=False):
    center_feels = Image.new(mode='RGB', size=(514, 65), color='white')
    draw = ImageDraw.Draw(center_feels)
    x = (center_feels.width // 2) - 35 if feels_file else (center_feels.width // 2)
    y = center_feels.height // 2

    # Get accurate text size
    bbox = draw.textbbox((0, 0), string_feels_like, font=font50, anchor='lt')
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Draw centered text
    draw.text((x, y), string_feels_like, fill='black', font=font50, anchor='mm')

    # If there's an icon to paste, do it
    if paste_icon and feels_file:
        feels_image = Image.open(os.path.join(icondir, feels_file)).convert('RGBA')
        icon_y = (center_feels.height - feels_image.height) // 2
        icon_x = x + (text_width // 2) + 25  # 25 px margin right of text
        center_feels.paste(feels_image, (icon_x, icon_y), feels_image)

    return center_feels

# Set the fonts
font20 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 20)
font22 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 22)
font23 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 23)
font25 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 25)
font30 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 30)
font35 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 35)
font50 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 50)
font60 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 60)
font100 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 100)
font160 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 160)
#B fonts are for white text on black
font21b = ImageFont.truetype(os.path.join(fontdir, 'Helvetica-Bold.ttf'), 21)
font23b = ImageFont.truetype(os.path.join(fontdir, 'Helvetica-Bold.ttf'), 23)
font24b = ImageFont.truetype(os.path.join(fontdir, 'Helvetica-Bold.ttf'), 24)

# Set the colors
black = 'rgb(0,0,0)'
white = 'rgb(255,255,255)'
grey = 'rgb(235,235,235)'

# Initialize and clear screen
print(str(datetime.now()) + ' Initializing and clearing screen.')
epd.init()
epd.Clear()

while True:
    # Ensure there are no errors with connection
    error_connect = True
    while error_connect == True:
        try:
            #Tempest API request
            wx_response = requests.get(wx_url, timeout = tout)
            wxdata = wx_response.json()
            wx_check = wx_response.status_code
            print(str(datetime.now()) + ' Attempting to connect to Tempest WX. Status code: ' + str(wx_response.status_code))

            #NWS API request
            nws_response = requests.get(nws_url, timeout = tout)
            nws = nws_response.json()
            nws_check = nws_response.status_code
            print(str(datetime.now()) + ' Attempting to connect to NWS API. Status code: ' + str(nws_response.status_code))

            #Moon API request
            moon_limit = datetime.now().time()
            moon_hour = (moon_limit.hour % 2)
            if (moon_hour == 0 and moon_limit.minute <= 4) or phase == None:
                moon_response = requests.get(moon_url, headers=headers, params=params, timeout = tout)
                moon_api = moon_response.json()
                moon_check = moon_response.status_code
                print(str(datetime.now()) + ' Attempting to connect to Free Astro API. Status code: ' + str(moon_response.status_code))
                #Connect to US Naval Observatory
                moon_b_response = requests.get(moon_b_url, timeout = tout)
                moon_b_api = moon_b_response.json()
                moon_b_check = moon_b_response.status_code
                print(str(datetime.now()) + ' Attempting to connect to US Naval Observatory API. Status code: ' + str(moon_b_response.status_code))

            if wx_check == 200 and nws_check == 200 and moon_check == 200 and moon_b_check == 200:
                print(str(datetime.now()) + ' All API connections successful.')
                error_connect = None
            else:
                raise HTTPError("Request failed.")

        except requests.Timeout:
            # Call function to display connection error
            print(str(datetime.now()) + ' Connection error.')
            display_error('CONNECTION') 
            #Add to error counter
            from subprocess import call
            ec += 1
            #Reboot screen after 10 connection attempts
            if ec == 10 and reboot == '0':
                file = open("reboot.txt", "w")
                file.write(str(1))
                file.close()
                #from subprocess import call
                call("sudo reboot", shell=True)
            #If rebooting did not fix issue, clear screen and shutdown
            elif ec == 5 and reboot == '1':
                epd.init()
                epd.Clear()
                file = open("reboot.txt", "w")
                file.write(str(0))
                file.close()
                #from subprocess import call
                call("sudo shutdown -h now", shell=True)
        except HTTPError:
            print(str(datetime.now()) + ' HTTP error.')
            display_error('HTTP')

    error = None
    while error == None:
            # Check status of code request
        if wx_check == 200 and nws_check == 200 and moon_check == 200 and moon_b_check == 200:
            try:
                file = open("reboot.txt", "w")
                file.write(str(0))
                file.close()
                ec = 0
                print(str(datetime.now()) + ' API JSON acquisitions successful.')

                # get current dict block
                current = wxdata['current_conditions']
                # get current
                temp_current = current['air_temperature']
                # get feels like
                feels_like = current['feels_like']
                # get humidity
                humidity = current['relative_humidity']
                #get dew point
                dewpt = current['dew_point']
                # get wind speed
                wind = current['wind_avg']
                windcard = current['wind_direction_cardinal']
                gust =  current['wind_gust']
                # get description
                weather = current['conditions']
                report = current['conditions']

                #get pressure trend
                baro = current['sea_level_pressure']
                trend = current['pressure_trend']

                #Meme Mode Mod
                icon_code = current['icon']
                if memes == 0 and icon_code != 'thunderstorm' and icon_code != 'snow' and icon_code != 'sleet' and icon_code != 'rainy' and gust >= wind_thresh:
                    icon_code = 'windy'
                elif memes == 1 and icon_code != 'thunderstorm' and icon_code != 'snow' and icon_code != 'sleet' and icon_code != 'rainy' and gust >= wind_thresh:
                    icon_code = 'windy-meme'
                elif memes ==1 and dewpt >= 76:
                    icon_code = 'death-meme'
                    report = 'Death'
                elif memes ==1 and feels_like >= 95 and (humidity >= 60 or dewpt >= 70) :
                    icon_code = 'angry-sun-meme'
                    report = 'World 2-'
                elif memes ==1 and feels_like <= super_cold:
                    icon_code = 'iceking'
                    report = 'Embrace the Freeze'
                else:
                    icon_code = current['icon']

                #Lighning strikes in the last 3 hours
                strikesraw = current['lightning_strike_count_last_3hr']
                strikes = f"{strikesraw:,}"

                #Check for Thundersnow
                if icon_code == 'snow' and strikesraw > 1 and memes == 1:
                    icon_code = 'thundersnow'

                #Lightning distance message
                lightningdist = current['lightning_strike_last_distance_msg']

                # get daily dict block
                daily = wxdata['forecast']['daily'][0]

                # get daily precip
                daily_precip_percent = daily['precip_probability']
                picon = daily['precip_icon']
                total_rain = current['precip_accum_local_day']
                rain_time = current['precip_minutes_local_day']
                if rain_time > 0 and total_rain <= 0:
                    total_rain = 1000
                if rain_time >= 61:
                    hours = rain_time // 60
                    minutes = rain_time % 60
                    if hours >1:
                        rain_time = "{} hrs {} min".format(hours, minutes)
                    else:
                        rain_time = "{}hr {} min".format(hours, minutes)
                else:
                    rain_time = "{} min".format(rain_time)

                # get min and max temp
                daily_temp = current['air_temperature']
                temp_max = daily['air_temp_high']
                temp_min = daily['air_temp_low']
                sunriseepoch = daily['sunrise']
                sunsetepoch = daily['sunset']
                #Convert epoch to readable time
                sunrise = datetime.fromtimestamp(sunriseepoch)
                sunset = datetime.fromtimestamp(sunsetepoch)
            except KeyError:
                print(str(datetime.now()) + ' Tempest API Key Error.')
                display_error('API')

            #Get Severe weather data from NWS
            alert = None
            string_event = None
            try:
                alert = nws['features'][int(0)]['properties']
                event = alert['event']
                urgency = alert['urgency']
                severity = alert['severity']
                #swstitle = alert['parameters']['NWSheadline']
            except IndexError:
                alert = None

            if alert != None: #and event != 'Special Weather Statement':
                string_event = event
           
            #Moon API JSON block
            try:
                phase = moon_api['phase']['name']
                moon_lux = moon_api['phase']['illumination']
                super = moon_api['special_moon']['is_supermoon']
                micro = moon_api['special_moon']['is_micromoon']
                blue = moon_api['special_moon']['is_blue_moon']
                black = moon_api['special_moon']['is_black_moon']
                harvest = moon_api['special_moon']['is_harvest_moon']
                hunter = moon_api['special_moon']['is_hunter_moon']
                special = moon_api['special_moon']['labels']
                eclipse = moon_api['eclipse']['is_eclipse']
                blood_moon = moon_api['eclipse']['is_blood_moon']
                try:
                    e_type = moon_api['eclipse']['type']
                    e_check = moon_api['eclipse']['is_eclipse']
                    e_date = moon_api['eclipse']['date']
                    e_vis = moon_api['eclipse']['visibility']
                    e_count = moon_api['eclipse']['days_from_query']
                except KeyError:
                    e_check = False
                    print(str(datetime.now()) + ' No current eclipse data.')
                if moon_b_api['properties']['data']['moondata'][0]['phen'] == 'Rise':
                    risekey = 0
                else:
                    risekey = 1
                moonrise = moon_b_api['properties']['data']['moondata'][risekey]['time']
                moonrise = moonrise[:-3]
                if risekey == 0:
                    try:
                        moonset = moon_b_api['properties']['data']['moondata'][2]['time']
                        moonset = moonset[:-3]
                    except IndexError:
                        print(str(datetime.now()) + ' Moonset occurs past 12am, pulling data T+1 from US Naval Observatory.')
                        try:
                            moon_bp1_response = requests.get(moon_bp1_url, timeout = tout)
                            moon_bp1_check = (moon_bp1_response.status_code == requests.codes.ok)
                            moon_bp1_api = moon_bp1_response.json()
                            print(str(datetime.now()) + ' Moonset for T+1 from US Naval Observatory API successful. Status code: ' + str(moon_bp1_response.status_code))
                            moonset = moon_bp1_api['properties']['data']['moondata'][0]['time']
                            moonset = moonset[:-3]
                        except:
                            print(str(datetime.now()) + ' US Naval Observatory API Error.')
                            display_error('API')
                else:
                    print(str(datetime.now()) + ' Moonset occurs past 12am, pulling data T+1 from US Naval Observatory.')
                    try:
                        moon_bp1_response = requests.get(moon_bp1_url, timeout = tout)
                        moon_bp1_check = (moon_bp1_response.status_code == requests.codes.ok)
                        moon_bp1_api = moon_bp1_response.json()
                        print(str(datetime.now()) + ' Moonset for T+1 from US Naval Observatory API successful. Status code: ' + str(moon_bp1_response.status_code))
                        moonset = moon_bp1_api['properties']['data']['moondata'][0]['time']
                        moonset = moonset[:-3]
                    except:
                        print(str(datetime.now()) + ' US Naval Observatory API Error.')
                        display_error('API')
                        
            #On key error activate backup moon API to US Navy Observatory
            except KeyError:
                print(str(datetime.now()) + ' Free Astro API Key error, using US Naval Observatory.')
                try:
                    #Manual override to drop eclipse data
                    e_check = False
                    phase = moon_b_api['properties']['data']['curphase']
                    moon_lux_raw = moon_b_api['properties']['data']['fracillum']
                    moon_lux = float(moon_lux_raw.strip('%')) / 100                        
                except KeyError:
                    print(str(datetime.now()) + ' Backup moon API Key Error.')
                    display_error('API')

            # Set strings to be printed to screen
            string_temp_current = format(temp_current, '.0f') + u'\N{DEGREE SIGN}F'
            string_feels_like = 'Feels like: ' + format(feels_like, '.0f') +  u'\N{DEGREE SIGN}F'
            string_humidity = 'Humidity: ' + str(humidity) + '%'
            string_dewpt = 'Dew Point: ' + format(dewpt, '.0f') +  u'\N{DEGREE SIGN}F'
            string_wind = 'Wind: ' + format(wind, '.1f') + ' MPH ' + windcard
            if report.title() == 'Wintry Mix Possible':
                string_report = ''
                string_reportaux = report.title()
            elif report == 'World 2-':
                string_report = report
            else:
                string_report = report.title()
            string_baro = 'Pressure: ' + str(baro) + ' inHg'
            string_temp_max = 'High: ' + format(temp_max, '>.0f') + u'\N{DEGREE SIGN}F'
            string_temp_min = 'Low:  ' + format(temp_min, '>.0f') + u'\N{DEGREE SIGN}F'
            string_precip_percent = 'Precip: ' + str(format(daily_precip_percent, '.0f'))  + '%'
            if total_rain < 1000:
                string_total_rain = 'Total: ' + str(format(total_rain, '.2f')) + ' in | Duration: ' + str(rain_time)
            else:
                string_total_rain = 'Total: Trace | Duration: ' + str(rain_time)
            string_rain_time = str(rain_time)
            if e_check == True:
                if e_count == 1:
                    string_e_count = ' in ' + str(e_count) + ' day' #format(e_count, '>.0f') + ' day'
                elif e_count < 1:
                    string_e_count = ' at ' + str(e_date)
                else:
                    string_e_count = ' in ' + str(e_count) + ' days' #format(e_count, '>.0f') + ' days'
                if blood_moon == True:
                    mooncast = 'Blood Moon (total eclipse)' + string_e_count
                else:
                    mooncast = e_type.title() + ' lunar eclipse' + string_e_count 

            # Set error code to false
            error = False

        else:
            # Call function to display HTTP error
            display_error('HTTP')

    # Open template file
    template = Image.open(os.path.join(picdir, 'template.png'))
    # Initialize the drawing context with template as background
    draw = ImageDraw.Draw(template)

    # Draw top left box
    #Logic for nighttime....DAYTIME
    nowcheck = datetime.now()
    if icon_code.startswith('possibly') or icon_code == 'thundersnow' or icon_code  == 'cloudy' or icon_code == 'foggy' or icon_code == 'windy' or icon_code == 'iceking' or icon_code.startswith('clear') or icon_code.startswith('partly') or icon_code.endswith('-meme'):
        icon_file = icon_code + '.png'
    elif nowcheck >= sunrise and nowcheck < sunset:
        icon_file = icon_code + '-day.png'
    else:
        icon_file = icon_code + '-night.png'
    icon_image = Image.open(os.path.join(icondir, icon_file))
    template.paste(icon_image, (52, 15))
    if string_report == 'World 2-':
        now_center = create_image_w2((249, 35), 'white', string_report, font23, 'black')
        template.paste(now_center, (12,175))
        w2d_file = 'w2d.png'
        w2d_image = Image.open(os.path.join(icondir, w2d_file))
        template.paste(w2d_image, (160,180))
    else:
        now_center = create_image((249, 35), 'white', string_report, font23, 'black')
        template.paste(now_center, (12,175))

    #Barometer trend logic block
    if trend == 'falling':
        baro_file = 'barodown.png'
    elif trend == 'steady':
        baro_file = 'barosteady.png'
    else:
        baro_file = 'baroup.png'
    baro_image = Image.open(os.path.join(icondir, baro_file))
    template.paste(baro_image, (12, 213)) #15, 218
    draw.text((62, 223), string_baro, font=font22, fill=black) #65,228

    #Precipitation Logic
    if picon == 'chance_sleet':
        precip_file = 'mix.png'
    elif picon == 'chance_snow':
        precip_file = 'chance_snow.png'
    else:
        precip_file = 'precip.png'
    precip_image = Image.open(os.path.join(icondir, precip_file))
    template.paste(precip_image, (12, 263)) #15, 260
    draw.text((62, 271), string_precip_percent, font=font22, fill=black) #65, 268
    #Rh, Dew Point and Wind
    rh_file = 'rh.png'
    rh_image = Image.open(os.path.join(icondir, rh_file))
    template.paste(rh_image, (12, 313))
    draw.text((62, 323), string_humidity, font=font22, fill=black) #345, 340
    dp_file = 'dp.png'
    dp_image = Image.open(os.path.join(icondir, dp_file))
    template.paste(dp_image, (12, 363))
    draw.text((62, 373), string_dewpt, font=font22, fill=black)
    wind_file = 'wind.png'
    wind_image = Image.open(os.path.join(icondir, wind_file))
    template.paste(wind_image, (12, 413))
    draw.text((62, 423), string_wind, font=font22, fill=black) #345, 400

    #Main temp centered
    temp_center = create_image((514, 190), 'white', string_temp_current, font160, 'black') #365, 190
    template.paste(temp_center, (278,20)) #580,35
    difference = int(feels_like) - int(temp_current)

    #Center Feels Like
    if memes == 0 and dewpt >= 76:
        img_out = create_feelslike_image('death.png', paste_icon=True)
        template.paste(img_out, (278, 195))  # Add this if you want to always paste here

    elif (report != 'Death' and report != 'World 2-') and difference >= 5:
        img_out = create_feelslike_image('feelshot.png', paste_icon=True)
        template.paste(img_out, (278, 195))

    elif difference <= -5:
        img_out = create_feelslike_image('feelscold.png', paste_icon=True)
        template.paste(img_out, (278, 195))

    else:
        img_out = create_feelslike_image()
        template.paste(img_out, (278, 195))

    #High/Low temps
    draw.text((320, 310), string_temp_max, font=font50, fill=black) #35,325
    draw.line((455, 370, 550, 370), fill=black, width=4)
    draw.text((320, 375), string_temp_min, font=font50, fill=black) #35,390
    
    #Sunrise/Sunset/Moonrise/Moonset logic
    sunrise_t = sunrise.strftime("%H:%M")
    sunset_t = sunset.strftime("%H:%M")

    if datetime.now().strftime("%H:%M") >= sunrise_t and datetime.now().strftime("%H:%M") <= sunset_t:
        sunrise_file = 'sunrise.png'
        sunrise_image = Image.open(os.path.join(icondir, sunrise_file))
        template.paste(sunrise_image, (318, 430))
        draw.text((368, 440), str(sunrise_t), font=font22, fill=black)
        sunset_file = 'sunset.png'
        sunset_image = Image.open(os.path.join(icondir, sunset_file))
        template.paste(sunset_image, (448, 430))
        draw.text((498, 440), str(sunset_t), font=font22, fill=black)
    else:
        moonrise_file = 'moonrise.png'
        moonrise_image = Image.open(os.path.join(icondir, moonrise_file))
        template.paste(moonrise_image, (318, 430))
        draw.text((368, 440), str(moonrise), font=font22, fill=black)
        moonset_file = 'moonset.png'
        moonset_image = Image.open(os.path.join(icondir, moonset_file))
        template.paste(moonset_image, (448, 430))
        draw.text((498, 440), str(moonset), font=font22, fill=black)

    #Begin Lightning/Moon mod
    if strikesraw >= 1:
        strike_file = 'strike.png'
        strike_image = Image.open(os.path.join(icondir, strike_file))
        template.paste(strike_image, (605, 305))
        draw.text((690, 330), 'Strikes', font=font23b, fill=white)
        draw.line((685, 355, 770, 355), fill =white, width=3)
        strikeimg = Image.new(mode='RGB', size=(50, 20), color='black') 
        draw1 = ImageDraw.Draw(strikeimg)
        x0 = (strikeimg.width // 2)
        y0 = (strikeimg.height // 2)
        draw1.text((x0, y0), strikes, fill='white', font=font21b, anchor='mm')
        template.paste(strikeimg, (703, 360))
        draw.text((680, 400), 'Distance', font=font23b, fill=white)
        draw.line((675, 425, 778, 425), fill =white, width=3)
        draw.text((680, 430), lightningdist, font=font21b, fill=white)
    else:
        if super == True:
            moon_file == 'full.png'
            phase == special
        elif micro == True:
            moon_file == 'full.png'
            phase == special
        elif blue == True:
            moon_file == 'full.png'
            phase == special
        elif black == True:
            moon_file == 'new.png'
            phase == special
        elif harvest == True:
            moon_file == 'full.png'
            phase == special
        elif hunter == True:
            moon_file == 'full.png'
            phase == special
        else:
            if phase == 'New Moon':
                moon_file = 'new.png'
            elif phase == 'Waxing Crescent':
                moon_file = 'waxing_crescent.png'
            elif phase == 'First Quarter':
                moon_file = 'first_quarter.png'
            elif phase == 'Waxing Gibbous':
                moon_file = 'waxing_gibbous.png'
            elif phase == 'Full Moon' or moon_lux >= .99:
                phase = 'Full Moon'
                moon_file = 'full.png'
            elif phase == 'Waning Gibbous':
                moon_file = 'waning_gibbous.png'
            elif phase == 'Third Quarter':
                moon_file = 'third_quarter.png'
            elif phase == 'Waning Crescent':
                moon_file = 'waning_crescent.png'
            else:
                moon_file = 'waxing_crescent.png'
        moon_image = Image.open(os.path.join(icondir, moon_file))
        template.paste(moon_image, (640, 337))
        phase_center = create_image((195, 30), 'black', phase, font24b, 'white') #365, 190
        template.paste(phase_center, (600,310)) #580,35
        current_time = datetime.now().strftime('%H:%M')
        draw.text((627, 450), 'Updated: ' + current_time, font = font21b, fill=white)

    #Precipitaton mod
    if total_rain > 0 or total_rain == 1000:
        center_precip = Image.new(mode='RGB', size=(514, 50), color='white')
        draw = ImageDraw.Draw(center_precip)
        x = (center_precip.width // 2) + 25
        y = (center_precip.height // 2) #- 10

        # Get bounding box for accurate text size
        bbox = draw.textbbox((0, 0), string_total_rain, font=font23, anchor='lt')
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Draw centered text
        draw.text((x, y), string_total_rain, fill='black', font=font23, anchor='mm')

        # Prepare the icon
        train_file = 'totalrain.png'
        train_image = Image.open(os.path.join(icondir, train_file)).convert('RGBA')
        icon_y = (center_precip.height - train_image.height) // 2
        icon_x = x - (text_width // 2) - train_image.width - 10  # 10 px margin

        # Paste icon, respecting transparency
        center_precip.paste(train_image, (icon_x, icon_y), train_image)

        # Paste result where you want it on the template
        template.paste(center_precip, (278, 15))

    #Severe Weather/Eclipse Mod
    try:
        if string_event is not None:
            # Center the warning data at the bottom of the screen
            warning_img = Image.new(mode='RGB', size=(514, 40), color='white')
            draw = ImageDraw.Draw(warning_img)

            # Select alert image and x offset
            if 'Statement' in string_event:
                x = (warning_img.width // 2) + 25
                alert_file = 'info.png'
            elif 'Extreme Heat' in string_event:
                x = (warning_img.width // 2)
                alert_file = 'extreme.png'
            else:
                x = (warning_img.width // 2)
                alert_file = 'warning.png'
            y = (warning_img.height // 2)

            # Calculate accurate text bounding box
            bbox = draw.textbbox((0, 0), string_event, font=font23, anchor='lt')
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Draw text
            draw.text((x, y), string_event, fill='black', font=font23, anchor='mm')

            # Load alert image with transparency
            alert_image = Image.open(os.path.join(icondir, alert_file)).convert('RGBA')
            icon_y = (warning_img.height - alert_image.height) // 2
            left_icon_x = x - (text_width // 2) - alert_image.width - 10  # 10 px space left

            warning_img.paste(alert_image, (left_icon_x, icon_y), alert_image)

            # For non-Special, also paste an icon at the right end of the text
            #if 'Watch' or 'Warning' in string_event:
            if alert_file == 'warning.png' or alert_file == 'extreme.png':
                right_icon_x = x + (text_width // 2) + 10  # 10 px space right
                warning_img.paste(alert_image, (right_icon_x, icon_y), alert_image)

            # Paste the final composite image onto the template
            template.paste(warning_img, (278, 255))
        else:
            if e_count <= 7 and e_count >= 0:
                mooncast_center = create_image((514, 40), 'white', mooncast, font23, 'black')
                template.paste(mooncast_center, (278,255)) #580,35 
    except NameError:
        print(str(datetime.now()) + ' No Severe Weather')

   # Save the image for display as PNG
    screen_output_file = os.path.join(picdir, 'screen_output.png')
    template.save(screen_output_file)
    # Close the template file
    template.close()

    # Write to screen
    write_to_screen(screen_output_file, 300)
