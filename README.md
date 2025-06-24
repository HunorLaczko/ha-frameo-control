# HA Frameo Control Integration 🏠

This is a custom integration for [Home Assistant](https://www.home-assistant.io/) to control [Frameo](https://frameo.net/) digital photo frames.

This integration provides Home Assistant entities (`light`, `button`) for controlling your device. It was developed based on a **10.1" Frameo device running Android 6.0.1** and has been used with both the standard Frameo application and the alternative [ImmichFrame](https://github.com/ImmichFrame/immich-frame) client.

> [!WARNING]
> **Disclaimer:** This is a very early and highly experimental version. If you follow the setup steps in the correct order, it should work. However, long-term stability and behavior across Home Assistant restarts or network instabilities have not been thoroughly tested. Any contributions are very welcome!

## ‼️ Requirements

You **MUST** install and run the **[Frameo Control Backend Add-on](https://github.com/HunorLaczko/ha-frameo-control-addon)** before setting up this integration. The add-on is essential as it handles the direct USB/ADB communication with the device.

## 🚀 Installation

The recommended way to install is via the Home Assistant Community Store (HACS).

### HACS ✨ (Recommended)
1.  Ensure the **[Frameo Control Backend Add-on](https://github.com/HunorLaczko/ha-frameo-control-addon)** is installed and running first.
2.  Add this repository to HACS as a custom integration repository:
    * Click this button to add the repository to your Home Assistant instance:
      [![Add Repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=HunorLaczko&repository=ha-frameo-control&category=integration)
    * Or, go to HACS > Integrations, click the three-dots menu (⋮), select "Custom repositories", and add the URL:
      ```
      [https://github.com/HunorLaczko/ha-frameo-control](https://github.com/HunorLaczko/ha-frameo-control)
      ```
3.  Install the `HA Frameo Control` integration from the HACS Integrations page.
4.  Restart Home Assistant.

### Manual Install ⌨️
1.  Download the `ha_frameo_control` directory from this repository's `main` branch.
2.  Copy the entire `ha_frameo_control` directory into the `<config>/custom_components/` directory of your Home Assistant installation.
3.  Restart Home Assistant.

## 🛠️ Configuration

With the Backend Add-on running, you can now add the integration.

1.  Navigate to **Settings > Devices & Services**.
2.  Click **Add Integration** and search for **"Frameo Control"**.
3.  Choose your connection method. **USB is mandatory for the initial setup.**
4.  Select your device from the discovered list.
5.  Click **Submit**.
6.  **IMMEDIATELY CHECK THE FRAMEO DEVICE'S SCREEN.** You must accept the **"Allow USB Debugging"** prompt that appears on the device. You have about two minutes to approve it.

The integration should now be set up and your entities will be created.

## ✨ Switching to a Network Connection

The "Start Wireless ADB" button allows you to switch from a USB to a network connection. Please follow this specific workflow:

> [!NOTE]
> Once you enable wireless ADB, the USB ADB interface on the device will stop working until the device is rebooted. You will need to re-configure the integration.

1.  Ensure your integration is set up and working via **USB**.
2.  Press the **Start Wireless ADB** button in Home Assistant.
3.  On your Frameo device, go to its settings to find its IP Address. Or check your router.
4.  In Home Assistant, go to **Settings > Devices & Services**, find your Frameo Control integration, and **DELETE** it.
5.  Click **Add Integration** again and add **"Frameo Control"**.
6.  This time, choose the **Network** connection method and enter the IP address of your device.

## 🖼️ Entities

This integration creates a device with several entities to control your frame.

| Entity Type | Name                    | Description                                                                  |
| :---------- | :---------------------- | :--------------------------------------------------------------------------- |
| `light`     | Screen                  | Controls the screen on/off state. Brightness control is not yet functional.  |
| `button`    | Frameo Next Photo       | Uses a **swipe** gesture to advance to the next photo in the official Frameo app. |
| `button`    | Frameo Previous Photo   | Uses a **swipe** gesture to go to the previous photo in the official Frameo app.|
| `button`    | Immich Next Photo       | Uses a **tap** on the right side of the screen, optimized for the ImmichFrame app. |
| `button`    | Immich Previous Photo   | Uses a **tap** on the left side of the screen, optimized for the ImmichFrame app.  |
| `button`    | Immich Pause Photo      | Uses a **tap** in the center of the screen to toggle the OSD / pause.          |
| `button`    | Start Frameo App        | Launches the default Frameo application.                                     |
| `button`    | Start ImmichFrame       | Launches the ImmichFrame application.                                        |
| `button`    | Open Settings           | Opens the main Android Settings page on the device.                          |
| `button`    | Start Wireless ADB      | Enables Wireless ADB mode (see workflow above).                              |


## Known Issues

* **Brightness control does not work.** While the `light` entity is present, attempting to change the brightness will have no effect.
* The connection to the device can sometimes be lost if the addon or Home Assistant restarts. If entities become `Unavailable`, reloading the integration from the Devices & Services page will usually fix it.

## 🚧 Future Development (TODO)

This integration is still under development. Contributions and ideas are welcome!
* **Dynamic Controls:** Intelligently detect the currently open app (Frameo vs. Immich) to dynamically show only the relevant buttons.
* **Dynamic Orientation:** Detect screen orientation to provide perfectly placed taps, rather than relying on hardcoded coordinates.
* **Backend Improvements:** Investigate removing the need for `host_network: true` in the backend addon for improved network security.
* **Control Multiple Devices:** Allow a single Home Assistant instance to control more than one Frameo frame.