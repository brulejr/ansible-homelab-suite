Runs on container port 9442

# Tools

`merge_z2m_db.py` is installed into the app directory. It merges two zigbee2mqtt
`database.db` files, e.g. when moving to a new host whose instance has already
re-interviewed a few devices. Devices are matched by `ieeeAddr` and groups by
`groupID`; entries in the newer database win, and ids are renumbered.

Stop zigbee2mqtt on both instances before copying databases.

```bash
./merge_z2m_db.py old-database.db new-database.db merged-database.db
```

# Resources

Reference

- [Zigbee2MQTT](https://www.zigbee2mqtt.io/)

GitHub

- [koenkk/zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt)

Video Tutorials

- [How to Install Zigbee2MQTT - Home Assistant or Docker](https://www.youtube.com/watch?v=4hnWqc-5q1c)
- [Zigbee2MQTT Home Assistant: 2024 How To Guide for HAOS, UnRaid & Docker](https://www.youtube.com/watch?v=3elyzOzd2lc)
