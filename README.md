# HA Frameo Control Integration 🏠


This is a custom integration for [Home Assistant](https://www.home-assistant.io/) to control [Frameo](https://frameo.net/) digital photo frames.

This integration provides Home Assistant entities (`light`, `button`) for controlling your device. It was developed based on a **10.1" Frameo device running Android 6.0.1** and has been used with both the standard Frameo application and the alternative [ImmichFrame](https://github.com/ImmichFrame/immich-frame) client.

## 🌟 Key Features

* **Local Control:** 📡 All commands are sent locally to the backend add-on.
* **Screen & Brightness Control:** 💡 A `light` entity allows you to turn the screen on/off and adjust the brightness.
* **Slideshow Control:** ▶️ `button` entities to navigate to the **Next** and **Previous** photos, and to **Pause** the slideshow.
* **App & Settings Launchers:** 📱 Buttons to directly open the Frameo app, ImmichFrame, or the Android Settings page.
* **Wireless ADB Helper:** 🪄 A special button is provided by the backend to easily enable Wireless ADB mode.

## ‼️ Requirements

You **MUST** install and run the **[Frameo Control Backend Add-on](https://github.com/HunorLaczko/ha-frameo-control-addon)** before setting up this integration. The add-on handles the actual communication with the device.

## 🚀 Installation

### HACS ✨ (Recommended)

1.  **Add** ➕ this repository to your HACS custom repositories:
    * **Click** this button to add the repository to your Home Assistant instance:
        [![Add Repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=HunorLaczko&repository=ha-frameo-control&category=integration)
    * Or **copy** this URL ⤵️ and paste it into the "Custom Repositories" section of HACS:
        ```url
        [https://github.com/HunorLaczko/ha-frameo-control](https://github.com/HunorLaczko/ha-frameo-control)
        ```

2.  **Install** 💻 the `HA Frameo Control` integration from the HACS Integrations page.
3.  **Restart** 🔁 Home Assistant.

### Manual Install ⌨️

1.  Download the `ha_frameo_control` directory from this repository.
2.  Copy the entire `ha_frameo_control` directory into the `<config>/custom_components/` directory of your Home Assistant installation.
3.  **Restart** 🔁 Home Assistant.

## 🛠️ Configuration

Once the Backend Add-on is running, you can add this integration.

1.  Navigate to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **"HA Frameo Control"**.
3.  A confirmation dialog will appear. Click **Submit**. The integration will automatically connect to the backend add-on.

## 🖼️ Entities

This integration will create the following entities for your Frameo device:

| Entity Type | Name                | Description                                                          |
| :---------- | :------------------ | :------------------------------------------------------------------- |
| `light`     | Screen              | Controls the screen on/off state and brightness.                     |
| `button`    | Next Photo          | Swipes to the next photo in the slideshow.                           |
| `button`    | Previous Photo      | Swipes to the previous photo in the slideshow.                       |
| `button`    | Pause Photo         | Toggles play/pause for the slideshow.                                |
| `button`    | Start ImmichFrame   | Launches the ImmichFrame application.                                |
| `button`    | Start Frameo App    | Launches the default Frameo application.                             |
| `button`    | Open Settings       | Opens the main Android Settings page.                                |
| `button`    | Start Wireless ADB  | Asks the backend add-on to enable Wireless ADB on the device.          |


## ❓ Troubleshooting

* **Cannot Connect (USB):** Ensure the USB cable is connected securely and that ADB is enabled on the frame. On some systems (like HA OS on a Raspberry Pi), you may need to ensure the host machine can see the USB device.
* **Cannot Connect (Network):** This almost always means Wireless ADB is not active. Connect the device via USB, set up the integration using the USB method, press the "Start Wireless ADB" button, and then try adding the network connection again.