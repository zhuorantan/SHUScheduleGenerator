# SHUScheduleGenerator

This is a small Python script which can extract course schedule from the website of Shanghai University's Educational Administration and create a .ics file containing the schedule generated.

![](https://raw.githubusercontent.com/JeromeTan1997/SHUScheduleGenerator/master/assets/screenshot.png)

![](https://raw.githubusercontent.com/JeromeTan1997/SHUScheduleGenerator/master/assets/result.png)

## Download

If you just want to use the SHUScheduleGenerator, you can download SHUScheduleGenerator.py only.

## Environment

[Python](https://www.python.org) 3.6+ installation is required. Tested in Python 3.7.0.

Install icalendar and pytz packages.

``` sh
sudo pip install icalendar pytz
```

If you haven't installed pip, you can follow the guide [here](https://pip.pypa.io/).

## Usage

Click the link for more information: [link](https://www.kmahyyg.xyz/2018/SHU2ICS-Tutorial/)

That's all. After a while, a file named Course Schedule.ics will be put into the directory you provided.

If you are using OS X, you can double click it or drag it to `Calendar` to import your schedule to iCloud and iCloud will sync it to all the Apple devices you own.

You can also import it to Gmail, Microsoft Outlook or other email service that support .ics file import. Then after you logged in these email in your devices, schedule will be synced to calendar app.

## Development

If you are interested, you can fork this repository and create your own version of ScheduleGenerator.

You can modify it to generate schedules for other university other than Shanghai University.

Or, you can build a website or an App upon it to make it eaiser to access.

Furthermore, I have an idea to build a CalDAV server to sync schedules automatically. It's much harder and requires the access to universities' database. It's very difficult, if you are interested, you can help me.

## License

MIT
