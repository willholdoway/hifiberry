## Custom component for Hifiberry using audiocontrol2 REST API.
The `HifiBerry` platform allows you to control a [HifiBerry OS](https://www.hifiberry.com/hifiberryos/) media player from Home Assistant. This is an end-to-end streaming lightweight OS built by HifiBerry for their Amp+, DAC+ or Digi+ HAT Raspberry Pi boards compatible with Airplay, Bluetooth, DLNA, LMS/Squeezebox, MPD, Snapcast, Spotify and Roon music services.
### Installation
You can use HACS or install the component manually:

To get started put the files from `/custom_components/hifiberry/` in your folder `<config directory>/custom_components/hifiberry/`

### Configuration
#### Example configuration.yaml

```yaml
media_player:
  - platform: hifiberry
    host: 192.168.1.100
```

### Configuration variables

key | required | value | description  
:--- | :--- | :--- | :---
**platform** | yes | `hifiberry` | The platform name `hifiberry`.
**host** | yes | `192.168.1.101` | The IP address or hostname of the hifiberry device.
**port** | no | `81` | The Port number of HifiBerry audciocontrol2 rest service. By default, '81'.
**name** | no | `HifiBerry` | The name the media player will have in Home Assistant, default is `HifiBerry`.

### Installation instructions Hifiberry
None required other than setting a fixed IP for the device.
