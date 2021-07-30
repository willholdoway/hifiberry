## HiFiBerry for Home Assistant

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![License: CC0-1.0](https://licensebuttons.net/l/zero/1.0/80x15.png)](http://creativecommons.org/publicdomain/zero/1.0/)

The HiFiBerry HA integration allows controlling [HifiBerry OS](https://www.hifiberry.com/hifiberryos/) media players from Home Assistant.

This is an end-to-end streaming lightweight OS built by HiFiBerry for their Amp+, DAC+ or Digi+ HAT Raspberry Pi boards compatible with AirPlay, Bluetooth, DLNA, LMS/Squeezebox, MPD, Snapcast, Spotify and Roon music services. This uses the [HiFiBerry audiocontrol2 REST API](https://github.com/hifiberry/audiocontrol2/blob/master/doc/api.md).

### Installation

You can use [HACS](https://hacs.xyz/) or install the component manually:

To get started put the files from `/custom_components/hifiberry/` in your folder `<config directory>/custom_components/hifiberry/`

### Configuration

- Browse to your Home Assistant instance.
- In the sidebar click on  **Configuration**.
- From the configuration menu select:  **Integrations**.
- In the bottom right, click on the  Add Integration button.
- From the list, search and select “_Hifiberry_”.
- Follow the instruction on screen to complete the set up.

### Installation

None required other than setting a fixed IP for the device running HiFiBerry.

### Support

There is no official support for this add-on and is community supported within the **[Home Assistant HiFiBerry discussion thread](https://community.home-assistant.io/t/hifiberry-os-media-player-integration/163567)**.

If you have any proposed changes or bug fixes, please code them and create pull requests for your patches.

### See Also

* [Home Assistant HiFiBerry discussion thread](https://community.home-assistant.io/t/hifiberry-os-media-player-integration/163567)
* [pyhifiberry](https://github.com/dgomes/pyhifiberry)
