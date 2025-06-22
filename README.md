# HA Frameo Control

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This is a custom integration for [Home Assistant](https://www.home-assistant.io/) to control [Frameo](https://frameo.net/) digital photo frames.

This integration was developed based on a **10.1" Frameo device running Android 6.0.1** and has been used with both the standard Frameo application and the alternative [ImmichFrame](https://github.com/ImmichFrame/immich-frame) client. It communicates with the device directly using the Android Debug Bridge (ADB) protocol.

## Key Features

* **Direct Local Control:** No cloud services required. Commands are sent directly to the device over your local network or USB.
* **Screen & Brightness Control:** A `light` entity allows you to turn the screen on/off and adjust the brightness.
* **Slideshow Control:** `button` entities to navigate to the **Next** and **Previous** photos, and to **Pause** the slideshow.
* **Flexible Connection:** Connect via direct USB or over the network using Wireless ADB.
* **Wireless ADB Helper:** A special button is provided to easily enable Wireless ADB mode when connected via USB.

## Important Prerequisite: Enabling ADB

Frameo devices running this version of Android **do not have Wireless ADB enabled by default**, and this setting does not survive a reboot on non-rooted devices. You must first connect via USB to enable it.

### Step 1: Enable ADB on the Frameo Frame
1.  On your Frameo device, navigate to **Settings**.
2.  Tap on **About**.
3.  Tap on the **Beta Program** option to enable it. This will reveal the developer settings.
4.  An **ADB Access** option should now be visible. Tap it to enable ADB.

### Step 2: Understand the Connection Workflow
To control the device wirelessly, you must first connect it to the computer running Home Assistant via USB and use the provided "Start Wireless ADB" button. This will enable ADB over TCP/IP until the next time the frame reboots.

## Installation

### HACS ✨ (Recommended)

1.  **Add** ➕ this repository to your HACS custom repositories:
    * **Click** this button to add the repository to your Home Assistant instance:
        [![Add Repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=YOUR_USERNAME&repository=ha-frameo-control&category=integration)
    * Or **copy** this URL ⤵️ and paste it into the "Custom Repositories" section of HACS:
        ```url
        [https://github.com/YOUR_USERNAME/ha-frameo-control](https://github.com/YOUR_USERNAME/ha-frameo-control)
        ```

2.  **Install** 💻 the `HA Frameo Control` integration from the HACS Integrations page.
3.  **Restart** 🔁 Home Assistant.

### Manual Install ⌨️

1.  Download the `ha_frameo_control` directory from this repository.
2.  Copy the entire `ha_frameo_control` directory into the `<config>/custom_components/` directory of your Home Assistant installation.
3.  **Restart** 🔁 Home Assistant.

## Configuration

Once installed, you can add the integration to Home Assistant.

1.  Navigate to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **"HA Frameo Control"**.
3.  You will be asked to choose a connection method.

### Connection via USB
This is the recommended first step.
1.  Connect your Frameo device directly to your Home Assistant machine using a USB cable.
2.  Choose **USB** from the configuration menu.
3.  (Optional) If you have multiple USB devices connected, you may need to provide the device's serial number. Leave it blank if it's the only one.
4.  Click **Submit**. An integration will be created with all available entities.

**To enable wireless control**, find the **"Start Wireless ADB"** button on your new device's control page in Home Assistant and press it. This will prepare the device for a network connection.

### Connection via Network (Wireless ADB)
This method only works if you have already enabled Wireless ADB on the device (see the USB step above).
1.  Find your Frameo's IP address from its Wi-Fi settings.
2.  Choose **Network** from the configuration menu.
3.  Enter the IP address of your Frameo frame. The port should be `5555`.
4.  Click **Submit**.

## Entities

This integration will create the following entities for your Frameo device:

| Entity Type | Name | Description |
| :--- | :--- | :--- |
| `light` | Frameo Screen | Controls the screen on/off state and brightness. |
| `button` | Next Photo | Swipes to the next photo in the slideshow. |
| `button` | Previous Photo | Swipes to the previous photo in the slideshow. |
| `button` | Pause Photo | Toggles play/pause for the slideshow. |
| `button` | Start Wireless ADB | (USB Connection Only) Enables Wireless ADB mode on the device. |

## Troubleshooting

* **Cannot Connect (USB):** Ensure the USB cable is connected securely and that ADB is enabled on the frame. On some systems (like HA OS on a Raspberry Pi), you may need to ensure the host machine can see the USB device.
* **Cannot Connect (Network):** This almost always means Wireless ADB is not active. Connect the device via USB, set up the integration using the USB method, press the "Start Wireless ADB" button, and then try adding the network connection again.
