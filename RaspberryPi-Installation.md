# Installing Raspberry Pi OS
---
* [Requirements](#requirements)
  * [Software Requirements](#software-requirements)
  * [Hardware Requirements](#hardware-requirements)
* [Raspberry Pi Imager](#raspberry-pi-imager)
* [OS Installation](#os-installation)  
* [Network Configuration](#network-configuration)
  * [WiFi Configuration](#wifi-configuration)
  * [Hostname](#hostname)
  * [SSH](#ssh)
* [Raspberry Pi OS Configuration](#raspberry-pi-os-configuration)
* [Update the Raspberry Pi](#update-the-raspberry-pi)
* [Install Required Packages](#install-required-packages)
* [Format USB Thumb Drive with exFAT partition](#format-usb-thumb-drive-with-exfat-partition)
* [Install PiPlates Libraries](#install-piplates-libraries)
* [Update PiPlates Precision](#update-piplates-precision)
* [Clone the Program Repository](#clone-the-program-repository)
* [Disable WiFi](#disable-wifi)
* [Optional for Developers](#optional-for-developers)
  * [Configure X11 over SSH](#configure-x11-over-ssh)
  * [Install xeyes to test X11 export configuration](#install-xeyes-to-test-x11-export-configuration)
  * [Install geany IDE with Solarized Dark environment](#install-geany-ide-with-solarized-dark-environment)

## Requirements
### Software Requirements
1. Raspberry Pi Imager

### Hardware Requirements
1. 32GB SD Card
2. SD-Card reader for your platform (Windows/OSX/Linux)

## Raspberry Pi Imager
The easiest way to install an operating system onto an SD card for the Raspberry Pi, is by using the [Raspberry Pi imager](https://www.raspberrypi.org/downloads/).  Download the utility and install it using the default options.

## OS Installation
After the *Raspberry Pi Imager* has been installed, open it from the start menu. Once opened, follow these instructions by clicking on the corresponding options.

>1. Choose OS -> Raspberry Pi OS (other) -> Raspberry Pi OS Lite (32-bit)
>2. Choose SD Card -> (choose your SD card from the list options)
>3. Write -> Yes -> Continue

Close the Raspberry Pi imager

## Network configuration
It is recommended that you connect the Pi to the internet (if you have one with built-in WiFi functionality).  This allows for easy remote connection and configuration.

The instructions for configuring the WiFi, SSH access and hostname come courtesy of Professor Carl Salvaggio from the Rochester Institute of Technology (RIT) Imaging Science department and is described in his [Camera Trigger](https://github.com/csalvaggio/camera_trigger) project.

The SD-card should still be plugged into your device.  Remove the card and re-insert it.

### WiFi Configuration
Create the file *wpa_supplicant.conf* in the */boot* directory of your SD-card.  The path should be:

```
/boot/wpa_supplicant.conf
```

Open the file in a text editor and add the following:

*wpa_supplicant.conf*
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={
  ssid="<insert your SSID here>"
  psk="<insert your network's WPA passphrase here>"
  key_mgmt=WPA-PSK
}
```

### SSH Configuration
Create an empty file, without file extension named *ssh* in the */boot* directory of the SD-card.  The path should be:

```
/boot/ssh
```

### Hostname configuration
In order to change the hostname of the device, you need a Linux or OSX machine since Windows does not see the *rootfs* partition on the SD-card.  You need to change the hostname in two files:

```
/etc/hostname
/etc/hosts
```

Simply open the files with your favorite text editor and change the existing name to your preferred name.

## Raspberry Pi OS configuration
Certain interface and localization options need to be changed in order for the data collection and Pi-Hats to function correctly.  Firstly we will enable SPI and configure the Serial interface.

Run the command *raspi-config* as root user to perform the required changes.

```
sudo raspi-config
```

In the setup window that opens, go to *Interface Options*, then choose

>1. SPI -> yes
>2. Serial -> no -> yes

Use the *Back* button to return to the previous window, then go to *Localisation Options* and choose

>1. Change Time Zone -> None of the above -> UTC -> reboot

The Raspberry Pi is now configured to use the GPIO headers with SPI, and the serial interface for device communication.

## Update the Raspberry Pi
Before we can start installing the required software, we need to ensure the Pi is running the latest distribution and software packages.  To update the Pi perform the following actions.

To update the distribution:

```
sudo apt-get -y update && sudo apt-get -y dist-upgrade
```

Reboot the Pi after this process completes, then type:

```
sudo apt-get -y update && sudo apt-get -y upgrade
```

to update the packages.

## Install Required Packages
The project needs to run a Python project and interface with multiple add-on boards.  To facilitate communication, many packages and libraries need to be installed.

Run the following segments to install the required packages.

```
sudo apt-get -y update && sudo apt-get install -y --fix-missing build-essential vim vim-enhanced fuse exfat-fuse exfat-utils ifmetric gpiozero
```
```
sudo apt-get -y update && sudo apt-get install -y --fix-missing p7zip-full minicom libqmi-utils udhcpc xdg-utils x11-apps
```
```
sudo apt-get -y update && sudo apt-get install -y --fix-missing wiringpi ftp okular git python3-pip python3-pyqt4 python3-tk python-pmw rpi.gpio python3-paramiko
```

Occasionally some of the libraries are not installed during the first attempt.  This happens when connection to the server is interrupted or there are slow connections to the source files.  You can re-run any of the above commands if you received any errors or find that some features are not working.

When the above commands have completed, run the following command to clean up the installation.

```
sudo apt-get -y autoremove
```

## Format USB Thumb Drive with exFAT partition

*The SD-Card is detected as **mmcblk0**, therefore the USB thumb drive is **sda**.*

Launch fdisk to partition the drive (The enter key is represented by an arrow **<-**).

```
sudo fdisk /dev/sda
```

>*fdisk
```
d
n <- <- <- <-
t
7 (exFAT)
w
```

Lastly, format the partition
```
mkfs.exfat /dev/sda1
```

In order for the program to access the USB thumb drive, we need to mount it.  Mount the drive and set up partitions as follows:

1. Make a directory to mount the drive to
```
sudo mkdir /mnt/storage
```
2. Open the */etc/fstab* file with your favorite text editor and add the following line at the bottom of the file.  This will allow the system to automatically mount the USB thumb drive at boot time.
```
sudo vim /etc/fstab
```

  >*fstab*
```
/dev/sda1	/mnt/storage	exfat	defaults,auto,umask=000,users,rw	0 0
```
3. Save and exit the file.

Test the changes you've made to the fstab file by entering:

```
sudo mount -a
```

If everything is correct, you won't receive any errors and the USB thumb drive will be mounted to */mnt/storage/*.

Lastly make the directories that are used to store and manage files by the program.

```
sudo mkdir /mnt/storage/toUpload
sudo mkdir /mnt/storage/uploaded
```

## Install PiPlates libraries
In order to use the PiPlates boards with the Raspberry Pi, we need to install the PiPlates libraries.

Run the following commands to install all dependencies and example programs.

```
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install --upgrade Pi-Plates spidev python3-serial

mkdir -p /opt/DAQC2apps
cd /opt/DAQC2apps
wget https://pi-plates.com/downloads/DAQC2apps.tar.gz
tar -xzvf DAQC2apps.tar.gz
rm DAQC2apps.tar.gz
```

## Update PiPlates Precision
By default the PiPlates library only provides .3 decimal places for precision.  For sensor sampling we prefer .5 decimal places.  To update the precision to 5 decimal places, we need to changes values in the *DAQC2plate.py* file.

You can find the location of the *DAQC2plate.py* file with the following command.

```
sudo find / -name DAQC2plate.py
```

Once you've found the location of the file (*/usr/local/lib/python3.7/dist-packages/piplates/DAQC2plate.py* in my case), open it in your favorite text editor.  Change the precision from *3* to *5* in line 87 (it may be a different line in your file).

**CHANGE THE *3* AT THE END OF THE LINE TO A 5**

FROM
```
value=round(value*calscale[addr][channel]+calOffset[addr][channel],3)
```
TO **(notice the second-to-last value in the string)**
```
value=round(value*calscale[addr][channel]+calOffset[addr][channel],5)
```

Save the file and exit.

## Clone the Program Repository
The entire radiometer program is in this repository.  For the radiometer to work you need to clone the repository to the Raspberry Pi.  In order to do this, go into the *pi* home directory and clone the project by performing the following actions.

```
cd ~
git clone https://github.com/BKleynhans-WIP/radiometer-raspberrypi
```

## Disable WiFi
The last step in the setup process is to disable WiFi.

!!! PLEASE NOTE !!!
Once you disable WiFi, you will no longer be able to reach the device via SSH and would have to connect a keyboard and screen to the device in order to enable SSH again.

In order to disable WiFi, open the */etc/wpa_supplicant/wpa_supplicant.conf* file with your favorite text editor and comment the network section.  It should look as follows when you are done.


*wpa_supplicant.conf*
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

#network={
#  ssid="<insert your SSID here>"
#  psk="<insert your network's WPA passphrase here>"
#  key_mgmt=WPA-PSK
#}
```

## Optional for Developers
When working on larger projects it can be daunting to work with command line editors if you are not used to working with them.  To facilitate this process you can install a light weight version of the Geany IDE.  In order for the IDE to work via SSH however, you need to install and configure X11 forwarding.

The following process will guide you to configure X11 forwarding through SSH and install the Geany IDE.

### Configure X11 over SSH
Make a backup of the sshd_config file

```
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
```

Open the */etc/ssh/sshd_config* file with your favorite text editor.  Search for the following lines and change them accordingly.

```
X11Forwarding yes
X11DisplayOffset 10
X11UseLocalhost yes
```

Restart the SSH daemon service.

```
sudo systemctl restart sshd.service
```

### Install xeyes to test X11 export configuration
In order to test the X11 configuration, we can open the xeyes program we installed as part of the *Required Applications* step.

```
xeyes
```

If the Gnome eyes application opens and you can see the eyes following your mouse cursor, your X11 forwarding was set up correctly.

### Install geany IDE with Solarized ark environment
Now that the X11 forwarding has been configured correctly, we can install the Geany IDE.  First close the xeyes program, then enter the following commands.

```
sudo apt-get install -y geany
mkdir -p ~/.config/geany/colorschemes/
cd ~/.config/geany/colorschemes
wget https://raw.github.com/geany/geany-themes/master/colorschemes/solarized-dark.conf
```

You can now launch the Geany IDE from the terminal by entering *geany* and pressing enter.
