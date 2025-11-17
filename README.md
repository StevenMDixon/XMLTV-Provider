# XMLTV-Provider

Goal exploit the fact that Github offers cron jobs. With this we can run a service everyday that pulls data from a provider and converts it into an xml tv epg file.
With GH pages we can output the results of the action to a publically accessible place :-)


Toonami Aftermath has a public api endpoint: https://api.toonamiaftermath.com/media?scheduleName=Toonami%20Aftermath%20EST&dateString=2025-11-09T11%3A00%3A00Z&count
We should be able to hit this endpoint, get the schedule and then convert it to a an xml file to ingest in Jellyfin
