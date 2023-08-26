## HiFiBerry for Home Assistant

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

The HiFiBerry HA integration allows controlling [HifiBerry OS](https://www.hifiberry.com/hifiberryos/) media players from Home Assistant.

This is an end-to-end streaming lightweight OS built by HiFiBerry for their Amp+, DAC+ or Digi+ HAT Raspberry Pi boards compatible with AirPlay, Bluetooth, DLNA, LMS/Squeezebox, MPD, Snapcast, Spotify and Roon music services. This uses the [HiFiBerry audiocontrol2 socketio API](https://github.com/hifiberry/audiocontrol2/blob/master/doc/socketio_api.md).
 
***Be aware that this API is disabled by default. In order to use this integration it has to be enabled in the /etc/audiocontrol2.conf on the device, an authtoken will also have to be added:***
```bash
[webserver]
enable=yes
port=81
socketio_enabled=True
authtoken=my_super_secret_auth_token
```

### Installation

It is recommended this is installed using [Home Assistant Community Store (HACS)](https://hacs.xyz/) to ensure your Home Assistant instance can easily be kept up-to-date with the latest changes.

However, to install this manually, copy everything from `/custom_components/hifiberry/` to your folder `<config directory>/custom_components/hifiberry/`.

### Configuration

- Browse to your Home Assistant instance
- In the sidebar click on  **Configuration**
- From the configuration menu select: **Integrations**
- In the bottom right, click on the **Add Integration** button
- From the list, search and select “_HiFiBerry_”
- Follow the instruction to complete the set up

### Installation

None required other than setting a fixed IP for the device running HiFiBerry.

### Support

There is no official support for this add-on and is community supported within the **[Home Assistant HiFiBerry discussion thread](https://community.home-assistant.io/t/hifiberry-os-media-player-integration/163567)**.

If you have any proposed changes or bug fixes, please code them and create pull requests for your patches.

### See Also

* [Home Assistant HiFiBerry discussion thread](https://community.home-assistant.io/t/hifiberry-os-media-player-integration/163567)
* [pyhifiberry](https://github.com/schnabel/pyhifiberry)
