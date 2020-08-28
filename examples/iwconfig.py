#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2004, 2005 Róman Joost <roman@bromeco.de> - Rotterdam, Netherlands
# Copyright 2009 by Sean Robinson <seankrobinson@gmail.com>
#
# This file is part of Python WiFi
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
import getopt
import sys
import types

import pythonwifi.flags
from pythonwifi.iwlibs import Wireless, WirelessInfo, Iwrange, getNICnames, getWNICnames

def getBitrate(wifi):
    """ Return formatted string with Bit Rate info. """
    try:
        bitrate = wifi.wireless_info.getBitrate()
    except IOError:
        return None
    else:
        if bitrate.fixed:
            fixed = "="
        else:
            fixed = ":"
        return "Bit Rate{}{}   ".format(fixed, wifi.getBitrate())

def getTXPower(wifi):
    """ Return formatted string with TXPower info. """
    try:
        txpower = wifi.wireless_info.getTXPower()
    except IOError:
        return None
    else:
        if txpower.fixed:
            fixed = "="
        else:
            fixed = ":"
        return "Tx-Power{}{}   ".format(fixed, wifi.getTXPower())

def getSensitivity(wifi):
    """ Return formatted string with Sensitivity info. """
    try:
        sensitivity = wifi.wireless_info.getSensitivity()
    except IOError:
        return None
    else:
        if sensitivity.fixed:
            fixed = "="
        else:
            fixed = ":"
        iwrange = Iwrange(wifi.ifname)
        return "Sensitivity{}{}/{}  ".format(
            fixed, wifi.getSensitivity(), iwrange.sensitivity)

def getRetrylimit(wifi):
    """ Return formatted string with Retry info. """
    try:
        retry = wifi.wireless_info.getRetry()
    except IOError:
        return None
    else:
        modifier = ""
        if (retry.flags & pythonwifi.flags.IW_RETRY_MIN):
            modifier = " min"
        elif (retry.flags & pythonwifi.flags.IW_RETRY_MAX):
            modifier = " max"
        elif (retry.flags & pythonwifi.flags.IW_RETRY_SHORT):
            modifier = " short"
        elif (retry.flags & pythonwifi.flags.IW_RETRY_LONG):
            modifier = "  long"
        type = " limit"
        if (retry.flags & pythonwifi.flags.IW_RETRY_LIFETIME):
            type = " lifetime"
        return "Retry{}{}:{}   ".format(modifier, type, wifi.getRetrylimit())

def getRTS(wifi):
    """ Return formatted string with RTS info. """
    try:
        rts = wifi.wireless_info.getRTS()
    except IOError:
        return None
    else:
        if rts.disabled:
            return "RTS thr:off   "
        if rts.fixed:
            fixed = "="
        else:
            fixed = ":"
        return "RTS thr{}{} B   ".format(fixed, wifi.getRTS())

def getFragmentation(wifi):
    """ Return formatted string with Fragmentation info. """
    try:
        frag = wifi.wireless_info.getFragmentation()
    except IOError:
        return None
    else:
        if frag.disabled:
            return "Fragment thr:off"
        if frag.fixed:
            fixed = "="
        else:
            fixed = ":"
        return "Fragment thr{}{} B   ".format(fixed, wifi.getFragmentation())

def getEncryption(wifi):
    """ Return formatted string with Encryption info.

        As noted in iwconfig.c: we display only the "current" key, use iwlist
        to list all keys.

    """
    enc = wifi.wireless_info.getEncryption()
    if (enc.flags & pythonwifi.flags.IW_ENCODE_DISABLED):
        key = "Encryption key:off"
    else:
        key = "Encryption key:%s" % (wifi.getKey(), )
    if ((enc.flags & pythonwifi.flags.IW_ENCODE_INDEX) > 1):
        index = " [%d]" % (enc.flags & pythonwifi.flags.IW_ENCODE_INDEX, )
    else:
        index = ""
    if ((enc.flags & pythonwifi.flags.IW_ENCODE_RESTRICTED) > 0):
        mode = "   Security mode:restricted"
    elif ((enc.flags & pythonwifi.flags.IW_ENCODE_OPEN) > 0):
        mode = "   Security mode:open"
    else:
        mode = ""
    return "{}{}{}".format(key, index, mode)

def getPowerManagement(wifi):
    """ Return formatted string with Power Management info. """
    power = wifi.wireless_info.getPower()
    status = ""
    if (power.disabled):
        status = ":off"
    else:
        if (power.flags & IW_POWER_TYPE):
            if (power.flags & pythonwifi.flags.IW_POWER_MIN):
                status = status + " min"
            if (power.flags & pythonwifi.flags.IW_POWER_MAX):
                status = status + " max"
            if (power.flags & pythonwifi.flags.IW_POWER_TIMEOUT):
                status = status + " timeout:"
            else:
                if (power.flags & pythonwifi.flags.IW_POWER_SAVING):
                    status = status + " saving:"
                else:
                    status = status + " period:"
        pm_mode_mask = power.flags & pythonwifi.flags.IW_POWER_MODE
        if (pm_mode_mask == pythonwifi.flags.IW_POWER_UNICAST_R):
            status = status + "mode:Receive Unicast only received"
        elif (pm_mode_mask == pythonwifi.flags.IW_POWER_MULTICAST_R):
            status = status + "mode:Receive Multicast only received"
        elif (pm_mode_mask == pythonwifi.flags.IW_POWER_ALL_R):
            status = status + "mode:All packets received"
        elif (pm_mode_mask == pythonwifi.flags.IW_POWER_FORCE_S):
            status = status + "mode:Force sending"
        elif (pm_mode_mask == pythonwifi.flags.IW_POWER_REPEATER):
            status = status + "mode:Repeat multicasts"
        if (power.flags & pythonwifi.flags.IW_POWER_ON):
            status = status + ":on"
    return "Power Management{}".format(status)

def iwconfig(interface):
    """ Get wireless information from the device driver. """
    if interface not in getWNICnames():
        print("{:8.16}  no wireless extensions.".format(interface))
    else:
        wifi = Wireless(interface)
        line = """{:8.16}  {}  """.format(interface, wifi.getWirelessName())
        if (wifi.getEssid()):
            line = line + """ESSID:"{}"  \n          """.format(wifi.getEssid())
        else:
            line = line + "ESSID:off/any  \n          "

        # Mode, Frequency, and Access Point
        line = line + "Mode:" + wifi.getMode()
        try:
            line = line + "  Frequency:" + wifi.getFrequency()
        except IOError:
            # Some drivers do not return frequency info if not associated
            pass

        if (wifi.wireless_info.getMode() == pythonwifi.flags.IW_MODE_ADHOC):
            ap_type = "Cell"
        else:
            ap_type = "Access Point"
        ap_addr = wifi.getAPaddr()
        if (ap_addr == "00:00:00:00:00:00"):
            ap_addr = "Not-Associated"
        line = line + "  " + ap_type + ": " + ap_addr + "   "
        print(line)

        # Bit Rate, TXPower, and Sensitivity line
        line = "          "
        bitrate = getBitrate(wifi)
        if bitrate:
            line = line + bitrate
        txpower = getTXPower(wifi)
        if txpower:
            line = line + txpower
        sensitivity = getSensitivity(wifi)
        if sensitivity:
            line = line + sensitivity
        print(line)

        # Retry, RTS, and Fragmentation line
        line = "          "
        retry = getRetrylimit(wifi)
        if retry:
            line = line + retry
        rts = getRTS(wifi)
        if rts:
            line = line + rts
        fragment = getFragmentation(wifi)
        if fragment:
            line = line + fragment
        print(line)

        # Encryption line
        line = "          "
        try:
            line = line + getEncryption(wifi)
        except IOError:
            pass
        else:
            print(line)

        # Power Management line
        line = "          "
        line = line + getPowerManagement(wifi)
        print(line)

        try:
            stat, qual, discard, missed_beacon = wifi.getStatistics()
        except IOError:
            # Some drivers do not return statistics info if not associated
            pass
        else:
            # Link Quality, Signal Level and Noise Level line
            line = "          "
            line = line + "Link Quality:{}/100  ".format(qual.quality)
            line = line + "Signal level:{}dBm  ".format(qual.signallevel)
            line = line + "Noise level:{}dBm".format(qual.noiselevel)
            print(line)
            # Rx line
            line = "          "
            line = line + "Rx invalid nwid:{}  ".format(discard['nwid'])
            line = line + "Rx invalid crypt:{}  ".format(discard['code'])
            line = line + "Rx invalid frag:{}".format(discard['fragment'])
            print(line)
            # Tx line
            line = "          "
            line = line + "Tx excessive retries:{}  ".format(discard['retries'])
            line = line + "Invalid misc:{}   ".format(discard['misc'])
            line = line + "Missed beacon:{}".format(missed_beacon)
            print(line)

    print()

def setEssid(wifi, essid):
    """ Set the ESSID on the NIC. """
    try:
        wifi.setEssid(essid)
    except OverflowError:
        print("Error for wireless request \"Set ESSID\" ({:X}) :".format(
                pythonwifi.flags.SIOCSIWESSID))
        print("    argument too big (max {})".format(
                pythonwifi.flags.IW_ESSID_MAX_SIZE))
    except Exception as unexpected:
        # Unexpected errors
        print(unexpected)

def setMode(wifi, mode):
    """ Set the mode on the NIC. """
    try:
        wifi.setMode(mode)
    except ValueError:
        print("Error for wireless request \"Set Mode\" ({:X}) :".format(
                pythonwifi.flags.SIOCSIWMODE))
        print("    invalid argument \"{}\".".format(mode))
    except IOError as io_error:
        print("Error for wireless request \"Set Mode\" ({:X}) :".format(
                pythonwifi.flags.SIOCSIWMODE))
        print("    SET failed on device %s ; %s.".format(wifi.ifname,
                io_error.strerror))
    except Exception as unexpected:
        # Unexpected errors
        print(unexpected)

def setFreq(wifi, freq):
    """ Set the frequency on the NIC. """
    try:
        wifi.setFrequency(freq)
    except Exception as unexpected:
        # Unexpected errors
        print(unexpected)

def setKey(wifi, key):
    """ Set a WEP key on the NIC. """
    try:
        wifi.setKey(key)
    except Exception as unexpected:
        # Unexpected errors
        print(unexpected)

def setAP(wifi, ap):
    """ Set the AP with which to associate. """
    try:
        wifi.setAPaddr(ap)
    except Exception as unexpected:
        # Unexpected errors
        print(unexpected)

def usage():
    """ Print info about using iwconfig.py. """
    print("""Usage: iwconfig.py [interface]
                interface essid {NNN|any|on|off}
                interface mode {managed|ad-hoc|master|...}
                interface freq N.NNN[k|M|G]
                interface channel N
                interface bit {N[k|M|G]|auto|fixed}
                interface rate {N[k|M|G]|auto|fixed}
                interface enc {NNNN-NNNN|off}
                interface key {NNNN-NNNN|off}
                interface power {period N|timeout N|saving N|off}
                interface nickname NNN
                interface nwid {NN|on|off}
                interface ap {N|off|auto}
                interface txpower {NmW|NdBm|off|auto}
                interface sens N
                interface retry {limit N|lifetime N}
                interface rts {N|auto|fixed|off}
                interface frag {N|auto|fixed|off}
                interface modulation {11g|11a|CCK|OFDMg|...}
                interface commit 
       Check man pages for more details.""")

def version_info():
    """ Print version info for iwconfig.py, Wireless Extensions compatibility,
        and Wireless Extensions version in the kernel.

    """
    pass

def get_matching_command(option):
    """ Return a function for the command.

        'option' -- string -- command to match

        Return None if no match found.

    """
    # build dictionary of commands and functions
    iwcommands = { "es"   : ("essid",      setEssid),
                   "mode" : ("mode",       setMode),
                   "fre"  : ("freq",       setFreq),
                   "ch"   : ("channel",    setFreq),
                   #"b"    : ("bit",        setBitrate),
                   #"ra"   : ("rate",       setBitrate),
                   "en"   : ("enc",        setKey),
                   "k"    : ("key",        setKey),
                   #"p"    : ("power",      setPower),
                   #"ni"   : ("nickname",   setNickname),
                   #"nw"   : ("nwid",       setNwid),
                   "a"    : ("ap",         setAP),
                   #"t"    : ("txpower",    setTxpower),
                   #"s"    : ("sens",       setSens),
                   #"re"   : ("retry",      setRetry),
                   #"rt"   : ("rts",        setRts),
                   #"fra"  : ("frag",       setFrag),
                   #"modu" : ("modulation", setModulation),
                   #"co"   : ("commit",     setCommit),
                 }

    function = None
    for command in iwcommands.keys():
        if option.startswith(command):
            if iwcommands[command][0].startswith(option):
                function = iwcommands[command][1]
    return function

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "version"])
    except getopt.GetoptError:
        # invalid options will be taken to be interface name
        pass
    else:
        if len(args) == 0:
            # no params given to iwconfig.py
            for interface in getNICnames():
                iwconfig(interface)
        else:
            if opts[0][0] in ("-h", "--help"):
                usage()
            elif opts[0][0] in ("-v", "--version"):
                version_info()
            elif len(args) == 1:
                # one param given to iwconfig.py, it should be a network device
                if sys.argv[1] in getNICnames():
                    iwconfig(sys.argv[1])
            else:
                # more than one param, must be a command
                # if program name and more than one argument are given
                if len(sys.argv) > 2:
                    # Get the interface and command from command line
                    ifname, option = sys.argv[1:3]
                    # look for matching command
                    set_command = get_matching_command(option)
                    # if the second argument is a command
                    if set_command is not None:
                        wifi = Wireless(ifname)
                        set_command(wifi, sys.argv[3])
                    else:
                        print("iwconfig.py: unknown command `{}' " \
                            "(check 'iwconfig.py --help').".format(option))


if __name__ == "__main__":
    main()
