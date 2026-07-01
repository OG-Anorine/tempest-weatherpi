<h1>Tempest E-paper Weather Display</h1>
<br>
  Raspberry Pi weather display using Waveshare e-paper 7.5 inch display, Tempest Weather Station data, and Python.
<img src="https://github.com/OG-Anorine/Tempest-7.5-E-Paper-Display/blob/master/photos/screen_output.png" width=40% height=40%>
<br>
<img src="https://github.com/OG-Anorine/Tempest-7.5-E-Paper-Display/blob/master/photos/IMG_6607.jpeg" width=40% height=40%>
<h1>Versions</h1>
  <h2>Version 2.2</h2>
    <ul>
		<li>New error handling for non 200 status from APIs</li>
		<li>New error screens for missing JSON keys and non-200 status</li>
		<li>New flame icons for Extreme Heat Warnings to replace standard hazard triangles</li>
	</ul>
  <h2>Version 2.1.1</h2>
    <ul>
		<li>Corrected icon logic for special weather statement vs watch/warnings</li>
		<li>Removed NWS Headline - the headlines tend to be too long for the 7.5" screen</li>
	</ul>
  <h2>Version 2.1</h2>
    <ul>
		<li>Removed pytz module requirement</li>
		<li>Removed UTC to local timezone conversion definition</li>
		<li>Removed API call to Free Astro API for moonrise/moonset data due to observed inconsistencies.</li>
		<li>Created logic to traverse moonrise/moonset API changes based on dates</li>
		<li>General cleanup of legacy code</li>
	</ul>
  <h2>Version 2.0.1</h2>
    <ul>
		<li>Added more error handling on backup lunar API</li>
		<li>Worked with Free Astro API dev to clarify Eclipse keys, changes reflected in code</li>
		<li>Added lookup against US Naval Observatory in the event moonset ocurrs the next day.  This will keep Free Astro API hits low.</li>
	</ul>
  <h2>Version 2.0</h2>
    <ul>
		<li>Complete redesign of the original layout</li>
		<li>Additional APIs for lunar phases (includes eclipse data)</li>
		<li>Improved error handling</li>
		<li>Improved logging when redirecting screen output to file</li>
		<li>Additional error screen for API key errors (major source of blank screen flashing previously)</li>
		<li>More memes - who doesn't enjoy a good meme?</li>
		<li>Precipitation follows Tempest WX icon codes rather than temperature</li>
		<li>Added Sunrise/Sunset and Moonrise/Moonset data</li>
	</ul>  
  <h2>Version 1.5</h2>
    <ul>
		<li>Updated compatability for Debian 13 (Trixie)</li>
		<li>Removed deprecated Pillow centering methods</li>
		<li>Cleaned up development comments</li>
	</ul>
  <h2>Version 1.4</h2>
    <ul>
	    <li>Easier configuration - All inputs at top of script</li>
	    <li>New Chrome dinosaur inspiried Error screen</li>
	    <li>Meme mode - simply change 1 or 0 to toggle on/off at the top of script</li>
	    <ul>
		    <li>Angry Sun from Super Mario Bros. 3 if feels like >95 and humidity >=60 or dew point >=70</li>
		    <li>Skull and cross bones if dew point is >=76</li>
		    <li>Ron Paul "It's Hapenening" meme for Thundersnow</li>
		    <li>Windy icon replaced with "IT HECKIN WIMDY" Fox meme (configured from wind gust speed at beginning of script)</li>
	    </ul>
	    <li>Better error handling - no more doom loops</li>
	    <li>Better centering of data</li>
    </ul>
  <h2>Version 1.3</h2>
    <ul>
	    <li>Corrected error handling for API - Upon reconnection the screen will reset as expected, no more failure loop</li>
	    <li>Centered precipitation info</li>
	    <li>Fixed feels like logic centering</li>
    </ul>
  <h2>Version 1.2</h2>
    <ul>
	    <li>Corrected NWS alerts not clearing when expired</li>
	    <li>Changed NWS to include all alerts including statements, red flag, etc</li>
	    <li>Added more visible location to enter NWS county code at line 92</li>
	    <li>Fixed spacing issues with 'Wintry Mix Possible'</li>
	    <li>Added logic for precipitation chance icon: 40+ umbrella for rain, 33-39 wintry mix icon, 32 and below snowflake</li>
	    <li>Added skull and crossbones icon next to feels like in the event the dewpoint is 76 or higher</li>
    </ul>
  <h2>Version 1.1</h2>
    <ul>
	  <li>Corrected centering on NWS alert data</li>
	  <li>Added variable to plug in NWS county code</li>
	</ul>
 
  <h2>Version 1.0</h2>
    <ul>
	  <li>Initial Commit.</li>
	</ul>

<h1>Setup</h1>
  <ol type="1">
    <li>Assuming you have a Pi of your choice loaded, you will need to setup the e-paper display per the instructions from WaveShare: https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_(B)_Manual#Working_With_Raspberry_Pi.  *Note: these instructions are for the 3 color screen which I am using.  I have included comments in the code to change it back to the 2 color if desired.</li>
    <li>Open 'weather.py' and replace **Station ID here** with you station ID (Log into tempestwx.com - after successful login your station id will be listed at the end of the URL: https://tempestwx.com/station/XXXXXX) and **Token Here** with your API key (Create authorization at https://tempestwx.com/settings/tokens).</li>
    <li>Get your State/County ID from NSW to populate Watch/Warning data.  I have not found a great way to get this data other than using a multi-step process.  1. Go to https://www.weather.gov and enter your ZIP code on the left.  2. After the locaiton loads, click on "Get detailed info" 3. Select your city if needed 4. Get the coordinates out of the URL - these will be plugged into the API via browser of your choice: https://api.weather.gov/points/[start,end] - read through the data and look for "county": at the end of the JSON response.  This is your county code to plug into the Python code.  </li>
	<li>You will need an API token from freeastroapi.com to populate the moon phases, eclipse data, and moonrise/moonset data.  This is limited to 80 hits a day, but the screen is coded to only hit at the first run at the top of the hour or uopn reboot.
    <li>Create a script in your home directory that contains 2 commands. cd /home/[username]/Tempest-7.5-E-Paper-Display and sudo python weather.py - each on their own line.  Name this file something like startup.sh.  You will then need to chmod 755 [filename].sh to allow it to execute./</li>
    <li>Create 2 cronjobs in the root crontab.  1. @reboot /home/[username]/[filenamefromabovestep].sh - and 2. 30 3 * * * reboot - the first number represents minutes, the second the hour.  Reboot the Pi at a time of your choosing, this will refresh the screen to prevent burn-in. </li>
  </ol>
<br> 

# Note 
The storm data on this build is dynamic.  Rain totals, severe weather alerts, eclipse info, and lightning strike data only show up when it is present.  This is intentional to reduce clutter on the screen.

<b>Storm data:</b>
<br>
<img src="https://github.com/OG-Anorine/Tempest-7.5-E-Paper-Display/blob/master/photos/storm_output.png"> 
<br>
<b>Normal:</b>
<br>
<img src="https://github.com/OG-Anorine/Tempest-7.5-E-Paper-Display/blob/master/photos/screen_output.png"> 
<br>
<br>
If you are not using a 7.5 inch Version 2b display, you will want to replace 'epd7in5b_V2.py' in the 'lib' folder with whichever one you have from https://github.com/waveshare/e-Paper/tree/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd<br>
Fairly extensive adjustments will have to be made for other sized screens.

Optional items - Meme Mode can be enabled or disabled by setting 1 for on, 0 for off.  

# Parts
<ul>
  <li>https://www.waveshare.com/7.5inch-e-paper-hat-b.htm -OR- https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT *Note: I have actually ordered the grayscale screen.  Having built one of each with the 3 color, the refresh time on the 2 color (grayscale) is so much faster I would not recommend the screen that includes red.  To date, I have not been able to get the red to work which means I just have a ridiculously long refresh time screen.  Not worth it.  The 2 color will refresh in 4 seconds vs ~24 for the 3 color.</li>
  <li>Raspberry Pi ZeroW+</li>
  <li>SD card for the Pi at least 8 GB.</li>
  <li>Power supply for the Pi.</li>
  <li>5 x 7 inch photo frame</li>
  <li>Optional: 3D printer to print new back/mask for frame</li>
</ul>



<h1>Licensing</h1>
  <ul>
    <li>Code licensed under [MIT License](http://opensource.org/licenses/mit-license.html)</li>
    <li>Documentation licensed under [CC BY 3.0](http://creativecommons.org/licenses/by/3.0)</li>
  <ul>
