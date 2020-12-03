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
import errno
import sys
import types

import python3wifi.flags
from python3wifi.iwlibs import Wireless, Iwrange, getNICnames


def print_scanning_results(wifi, args=None):
    """ Print the access points detected nearby.

    """
    # "Check if the interface could support scanning"
    try:
        iwrange = Iwrange(wifi.ifname)
    except IOError:
        sys.stderr.write("{:8.16}  Interface doesn't support "
                         "scanning.\n\n".format(wifi.ifname))
    else:
        # "Check for Active Scan (scan with specific essid)"
        # "Check for last scan result (do not trigger scan)"
        # "Initiate Scanning"
        try:
            results = wifi.scan()
        except IOError as io_error:
            if io_error.errno != errno.EPERM:
                sys.stderr.write(
                    "{:8.16}  Interface doesn't support scanning : "
                    "{}\n\n".format(wifi.ifname, io_error.strerror))
        else:
            if (len(results) == 0):
                print("{:8.16}  No scan results".format(wifi.ifname))
            else:
                (num_channels, frequencies) = wifi.getChannelInfo()
                print("{:8.16}  Scan completed :".format(wifi.ifname))
                index = 1
                for ap in results:
                    print("          Cell {:02d} - Address: {}".format(index,
                                                                       ap.bssid))
                    print("                    ESSID:\"{}\"".format(ap.essid))
                    print("                    Mode:{}".format(ap.mode))
                    print("                    "
                          "Frequency:{} (Channel {})".format(
                              wifi._formatFrequency(
                                  ap.frequency.getFrequency()),
                              frequencies.index(wifi._formatFrequency(
                                  ap.frequency.getFrequency())) + 1))
                    if bool(ap.quality.updated
                            & pythonwifi.flags.IW_QUAL_QUAL_UPDATED):
                        quality_updated = "="
                    else:
                        quality_updated = ":"
                    if bool(ap.quality.updated
                            & pythonwifi.flags.IW_QUAL_LEVEL_UPDATED):
                        signal_updated = "="
                    else:
                        signal_updated = ":"
                    if bool(ap.quality.updated
                            & pythonwifi.flags.IW_QUAL_NOISE_UPDATED):
                        noise_updated = "="
                    else:
                        noise_updated = ":"
                    print("                    "
                          "Quality{}{}/{}  Signal level{}{}/{}  "
                          "Noise level{}{}/{}".format(
                              (quality_updated,
                               ap.quality.quality,
                               wifi.getQualityMax().quality,
                               signal_updated,
                               ap.quality.getSignallevel(),
                               "100",
                               noise_updated,
                               ap.quality.getNoiselevel(),
                               "100")))
                    # This code on encryption keys is very fragile
                    if bool(ap.encode.flags
                            & pythonwifi.flags.IW_ENCODE_DISABLED):
                        key_status = "off"
                    else:
                        if bool(ap.encode.flags
                                & pythonwifi.flags.IW_ENCODE_NOKEY):
                            if (ap.encode.length <= 0):
                                key_status = "on"
                    print("                    "
                          "Encryption key:{}".format(key_status))
                    if len(ap.rate) > 0:
                        for rate_list in ap.rate:
                            # calc how many full lines of bitrates
                            rate_lines = len(rate_list) / 5
                            # calc how many bitrates on last line
                            rate_remainder = len(rate_list) % 5
                            line = 0
                            # first line should start with a label
                            rate_line = "                    Bit Rates:"
                            while line < rate_lines:
                                # print full lines
                                if line > 0:
                                    # non-first lines should start *very*
                                    # indented
                                    rate_line = "                              "
                                rate_line = rate_line + \
                                    "{}; {}; {}; {}; {}".format(
                                        *tuple(wifi._formatBitrate(x) for x in
                                               rate_list[line * 5:(line * 5) + 5]))
                                line = line + 1
                                print(rate_line)
                            if line > 0:
                                # non-first lines should start *very* indented
                                rate_line = "                              "
                            # print non-full line
                            print(rate_line +
                                  ("{}; " * (rate_remainder - 1)).format(
                                      *tuple(wifi._formatBitrate(x) for x in
                                             rate_list[line * 5:line * 5 +
                                                       rate_remainder - 1])) +
                                  "{}".format(wifi._formatBitrate(
                                      rate_list[line * 5 + rate_remainder - 1])))
                    index = index + 1
            print


def print_channels(wifi, args=None):
    """ Print all frequencies/channels available on the card.

    """
    try:
        (num_frequencies, channels) = wifi.getChannelInfo()
        current_freq = wifi.getFrequency()
    except IOError as io_error:
        # Channel/frequency info not available
        if (io_error.errno == errno.EOPNOTSUPP) or \
           (io_error.errno == errno.EINVAL) or \
           (io_error.errno == errno.ENODEV):
            sys.stderr.write("{:8.16}  no frequency information.\n\n".format(
                wifi.ifname))
        else:
            report_error("channel", wifi.ifname, io_error.errno,
                         io_error.strerror)
    else:
        # Channel/frequency info available
        print("{:8.16}  {:02d} channels in total; "
              "available frequencies :".format(wifi.ifname, num_frequencies))
        for channel in channels:
            print("          Channel {:02d} : {}".format(
                channels.index(channel) + 1, channel))
        # Do some low-level comparisons on frequency info
        iwfreq = wifi.wireless_info.getFrequency()
        # XXX - this is not the same flags value as iwlist.c
        if iwfreq.flags & pythonwifi.flags.IW_FREQ_FIXED:
            fixed = "="
        else:
            fixed = ":"
        if iwfreq.getFrequency() < pythonwifi.iwlibs.KILO:
            return_type = "Channel"
        else:
            return_type = "Frequency"
        # Output current channel/frequency
        current_freq = wifi.getFrequency()
        print("          Current {}{}{} (Channel {})\n".format(
            return_type, fixed, current_freq,
            channels.index(current_freq) + 1))


def print_bitrates(wifi, args=None):
    """ Print all bitrates available on the card.

    """
    try:
        num_bitrates, bitrates = wifi.getBitrates()
    except IOError as io_error:
        if (io_error.errno == errno.EOPNOTSUPP) or \
           (io_error.errno == errno.EINVAL) or \
           (io_error.errno == errno.ENODEV):
            # not a wireless device
            sys.stderr.write("{:8.16}  no bit-rate information.\n\n".format(
                wifi.ifname))
        else:
            report_error("bit rate", wifi.ifname, io_error.errno,
                         io_error.strerror)
    else:
        if (num_bitrates > 0) and \
           (num_bitrates <= pythonwifi.flags.IW_MAX_BITRATES):
            # wireless device with bit rate info, so list 'em
            print("{:8.16}  {:02d} available bit-rates :".format(
                wifi.ifname, num_bitrates))
            for rate in bitrates:
                print("\t  {}".format(rate))
        else:
            # wireless device, but no bit rate info available
            print("{:8.16s}  unknown bit-rate information.".format(
                wifi.ifname))
    # current bit rate
    try:
        bitrate = wifi.wireless_info.getBitrate()
    except IOError:
        # no bit rate info is okay, error was given above
        pass
    else:
        if bitrate.fixed:
            fixed = "="
        else:
            fixed = ":"
        print("          Current Bit Rate{}{}".format(fixed,
                                                      wifi.getBitrate()))
        # broadcast bit rate
        # XXX add broadcast bit rate
        print


def print_encryption(wifi, args=None):
    """ Print encryption keys on the card.

    """
    try:
        keys = wifi.getKeys()
    except IOError as io_error:
        if (io_error.errno == errno.EOPNOTSUPP) or \
           (io_error.errno == errno.EINVAL) or \
           (io_error.errno == errno.ENODEV):
            # not a wireless device
            sys.stderr.write("{:8.16}  no encryption keys "
                             "information.\n\n".format(wifi.ifname))
    else:
        range_info = Iwrange(wifi.ifname)
        key_sizes = ""
        for index in range(range_info.num_encoding_sizes - 1):
            key_sizes = key_sizes + \
                repr(range_info.encoding_size[index] * 8) + \
                ", "
        key_sizes = key_sizes + \
            repr(range_info.encoding_size[range_info.num_encoding_sizes - 1] * 8) + \
            "bits"
        print("{:8.16}  {} key sizes : {}".format(
            wifi.ifname, range_info.num_encoding_sizes, key_sizes))
        print("          {} keys available :".format(len(keys)))
        for key in keys:
            print("\t\t[{}]: {}".format(key[0], key[1]))
        print("          Current Transmit Key: [{}]".format(
            wifi.wireless_info.getKey().flags &
            pythonwifi.flags.IW_ENCODE_INDEX))
        if bool(wifi.wireless_info.getKey().flags &
                pythonwifi.flags.IW_ENCODE_RESTRICTED):
            print("          Security mode:restricted")
        if wifi.wireless_info.getKey().flags & pythonwifi.flags.IW_ENCODE_OPEN:
            print("          Security mode:open")
        print("\n")


def format_pm_value(value, args=None):
    """ Return formatted PM value.

    """
    if (value >= pythonwifi.iwlibs.MEGA):
        fvalue = "{:g}s".format(value / pythonwifi.iwlibs.MEGA)
    else:
        if (value >= pythonwifi.iwlibs.KILO):
            fvalue = "{:g}ms".format(value / pythonwifi.iwlibs.KILO)
        else:
            fvalue = "{:d}us".format(value)
    return fvalue


def print_power(wifi, args=None):
    """ Print power management info for the card.

    """
    try:
        (pm_capa, power_period, power_timeout, power_saving, power_params) = \
            wifi.getPowermanagement()
    except IOError as io_error:
        if (io_error.errno == errno.ENODEV):
            sys.stderr.write("{:8.16}  no power management "
                             "information.\n\n".format(wifi.ifname))
    else:
        print("{:8.16} ".format(wifi.ifname))
        if bool(pm_capa & pythonwifi.flags.IW_POWER_MODE):
            print("Supported modes :")
            if bool(pm_capa & (pythonwifi.flags.IW_POWER_UNICAST_R |
                               pythonwifi.flags.IW_POWER_MULTICAST_R)):
                print("\t\t\to Receive all packets (unicast & multicast)")
                print("\t ", end='')
            if pm_capa & pythonwifi.flags.IW_POWER_UNICAST_R:
                print("\t\to Receive Unicast only (discard multicast)")
                print("\t ", end='')
            if pm_capa & pythonwifi.flags.IW_POWER_MULTICAST_R:
                print("\t\to Receive Multicast only (discard unicast)")
                print("\t ", end='')
            if pm_capa & pythonwifi.flags.IW_POWER_FORCE_S:
                print("\t\to Force sending using Power Management")
                print("\t ", end='')
            if pm_capa & pythonwifi.flags.IW_POWER_REPEATER:
                print("\t\to Repeat multicast")
                print("\t ", end='')
        if bool(power_period[0] & pythonwifi.flags.IW_POWER_PERIOD):
            if bool(power_period[0] & pythonwifi.flags.IW_POWER_MIN):
                print("Auto  period  ; ", end='')
            else:
                print("Fixed period  ; ", end='')
            print("min period:{}\n\t\t\t  ".format(
                format_pm_value(power_period[1])), end='')
            print("max period:()\n\t ".format(format_pm_value(
                power_period[2])), end='')
        if bool(power_timeout[0] & pythonwifi.flags.IW_POWER_TIMEOUT):
            if bool(power_timeout[0] & pythonwifi.flags.IW_POWER_MIN):
                print("Auto  timeout ; ", end='')
            else:
                print("Fixed timeout ; ", end='')
            print("min period:%s\n\t\t\t  ".format(
                format_pm_value(power_timeout[1])), end='')
            print("max period:%s\n\t ".format(format_pm_value(
                power_timeout[2])), end='')
        if (power_saving[0] & pythonwifi.flags.IW_POWER_SAVING):
            if (power_saving[0] & pythonwifi.flags.IW_POWER_MIN):
                print("Auto  saving  ; ", end='')
            else:
                print("Fixed saving  ; ", end='')
            print("min period:{}\n\t\t\t  ".format(
                format_pm_value(power_saving[1])), end='')
            print("max period:{}\n\t ".format(format_pm_value(
                power_saving[2])), end='')
        if power_params.disabled:
            print("Current mode:off")
        else:
            if bool(power_params.flags & pythonwifi.flags.IW_POWER_MODE ==
                    pythonwifi.flags.IW_POWER_UNICAST_R):
                print("Current mode:Unicast only received")
            elif bool(power_params.flags & pythonwifi.flags.IW_POWER_MODE ==
                      pythonwifi.flags.IW_POWER_MULTICAST_R):
                print("Current mode:Multicast only received")
            elif bool(power_params.flags & pythonwifi.flags.IW_POWER_MODE ==
                      pythonwifi.flags.IW_POWER_ALL_R):
                print("Current mode:All packets received")
            elif bool(power_params.flags & pythonwifi.flags.IW_POWER_MODE ==
                      pythonwifi.flags.IW_POWER_FORCE_S):
                print("Current mode:Force sending")
            elif bool(power_params.flags & pythonwifi.flags.IW_POWER_MODE ==
                      pythonwifi.flags.IW_POWER_REPEATER):
                print("Current mode:Repeat multicasts")
        print


def print_txpower(wifi, args=None):
    """ Print transmit power info for the card.

    """
    pass


def print_retry(wifi, args=None):
    try:
        range_info = Iwrange(wifi.ifname)
    except IOError as io_error:
        if (io_error.errno == errno.EOPNOTSUPP) or \
           (io_error.errno == errno.EINVAL) or \
           (io_error.errno == errno.ENODEV):
            sys.stderr.write("{:8.16}  no retry limit/lifetime "
                             "information.\n\n".format(wifi.ifname))
    else:
        ifname = "{:8.16}  ".format(wifi.ifname)
        if (range_info.retry_flags & pythonwifi.flags.IW_RETRY_LIMIT):
            if (range_info.retry_flags & pythonwifi.flags.IW_RETRY_MIN):
                limit = "Auto  limit    ;  min limit:{}".format(
                    range_info.min_retry)
            else:
                limit = "Fixed limit    ;  min limit:{}".format(
                    range_info.min_retry)
            print(ifname + limit)
            ifname = None
            print("                            max limit:{}".format(
                range_info.max_retry))
        if (range_info.r_time_flags & pythonwifi.flags.IW_RETRY_LIFETIME):
            if (range_info.r_time_flags & pythonwifi.flags.IW_RETRY_MIN):
                lifetime = "Auto  lifetime ;  min lifetime:{}".format(
                    range_info.min_r_time)
            else:
                lifetime = "Fixed lifetime ;  min lifetime:{}".format(
                    range_info.min_r_time)
            if ifname:
                print(ifname + lifetime)
                ifname = None
            else:
                print("          " + lifetime)
            print("                            max lifetime:{}".format(
                range_info.max_r_time))
        iwparam = wifi.wireless_info.getRetry()
        if iwparam.disabled:
            print("          Current mode:off")
        else:
            print("          Current mode:on")
            if (iwparam.flags & pythonwifi.flags.IW_RETRY_TYPE):
                if (iwparam.flags & pythonwifi.flags.IW_RETRY_LIFETIME):
                    mode_type = "lifetime"
                else:
                    mode_type = "limit"
                mode = "                 "
                if (iwparam.flags & pythonwifi.flags.IW_RETRY_MIN):
                    mode = mode + " min {}:{}".format(mode_type, iwparam.value)
                if (iwparam.flags & pythonwifi.flags.IW_RETRY_MAX):
                    mode = mode + " max {}:{}".format(mode_type, iwparam.value)
                if (iwparam.flags & pythonwifi.flags.IW_RETRY_SHORT):
                    mode = mode + " short {}:{}".format(
                        mode_type, iwparam.value)
                if (iwparam.flags & pythonwifi.flags.IW_RETRY_LONG):
                    mode = mode + " long {}:{}".format(
                        mode_type, iwparam.value)
                print(mode)


def print_aps(wifi, args=None):
    """ Print the access points detected nearby.

        iwlist.c uses the deprecated SIOCGIWAPLIST, but iwlist.py uses
        regular scanning (i.e. Wireless.scan()).

    """
    # "Check if the interface could support scanning"
    try:
        iwrange = Iwrange(wifi.ifname)
    except IOError:
        sys.stderr.write("{:8.16}  Interface doesn't support "
                         "scanning.\n\n".format(wifi.ifname))
    else:
        # "Check for Active Scan (scan with specific essid)"
        # "Check for last scan result (do not trigger scan)"
        # "Initiate Scanning"
        try:
            results = wifi.scan()
        except IOError as io_error:
            if io_error.errno != errno.EPERM:
                sys.stderr.write(
                    "{:8.16}  Interface doesn't support "
                    "scanning : {}\n\n".format(
                        wifi.ifname, io_error.strerror))
        else:
            if (len(results) == 0):
                print("{:8.16}  Interface doesn't have ".format(wifi.ifname)
                      + "a list of Peers/Access-Points")
            else:
                print("{:8.16}  Peers/Access-Points in range:".format(
                    wifi.ifname))
                for ap in results:
                    if (ap.quality.quality):
                        if (ap.quality.updated &
                                pythonwifi.flags.IW_QUAL_QUAL_UPDATED):
                            quality_updated = "="
                        else:
                            quality_updated = ":"
                        if (ap.quality.updated &
                                pythonwifi.flags.IW_QUAL_LEVEL_UPDATED):
                            signal_updated = "="
                        else:
                            signal_updated = ":"
                        if (ap.quality.updated &
                                pythonwifi.flags.IW_QUAL_NOISE_UPDATED):
                            noise_updated = "="
                        else:
                            noise_updated = ":"
                        print("    {} : Quality{}{}/{}  Signal level{}{}/{} "
                              "Noise level{}{}/{}".format(
                                  ap.bssid,
                                  quality_updated,
                                  ap.quality.quality,
                                  wifi.getQualityMax().quality,
                                  signal_updated,
                                  ap.quality.getSignallevel(),
                                  "100",
                                  noise_updated,
                                  ap.quality.getNoiselevel(),
                                  "100"))
                    else:
                        print("    {}".format(ap.bssid))
                print


def report_error(function, interface, error_number, error_string):
    """ Print error to user. """
    print("Uncaught error condition.  Please report this to the "
          "developers' mailing list (informaion available at "
          "http://lists.berlios.de/mailman/listinfo/pythonwifi-dev).  "
          "While attempting to print {} informaion for {}, "
          "the error \"{} - {}\" occurred.".format(
              function, interface, error_number, error_string))


def usage():
    print("""\
Usage: iwlist.py [interface] scanning [essid NNN] [last]
                 [interface] frequency
                 [interface] channel
                 [interface] bitrate
                 [interface] encryption
                 [interface] keys
                 [interface] power
                 [interface] txpower
                 [interface] retry
                 [interface] ap
                 [interface] accesspoints
                 [interface] peers""")


def get_matching_command(option):
    """ Return a function for the command.

        'option' -- string -- command to match

        Return None if no match found.

    """
    # build dictionary of commands and functions
    iwcommands = {"s": ("scanning", print_scanning_results),
                  "c": ("channel", print_channels),
                  "f": ("frequency", print_channels),
                  "b": ("bitrate", print_bitrates),
                  "ra": ("rate", print_bitrates),
                  "en": ("encryption", print_encryption),
                  "k": ("keys", print_encryption),
                  "po": ("power", print_power),
                  "t": ("txpower", print_txpower),
                  "re": ("retry", print_retry),
                  "ap": ("ap", print_aps),
                  "ac": ("accesspoints", print_aps),
                  "pe": ("peers", print_aps),
                  # "ev" : ("event", print_event),
                  # "au" : ("auth", print_auth),
                  # "w"  : ("wpakeys", print_wpa),
                  # "g"  : ("genie", print_genie),
                  # "m"  : ("modulation", print_modulation),
                  }

    function = None
    for command in iwcommands.keys():
        if option.startswith(command):
            if iwcommands[command][0].startswith(option):
                function = iwcommands[command][1]
    return function


def main():
    # if only program name is given, print usage info
    if len(sys.argv) == 1:
        usage()

    # if program name and one argument are given
    if len(sys.argv) == 2:
        option = sys.argv[1]
        # look for matching command
        list_command = get_matching_command(option)
        # if the one argument is a command
        if list_command is not None:
            for ifname in getNICnames():
                wifi = Wireless(ifname)
                list_command(wifi)
        else:
            print("iwlist.py: unknown command `{}' "
                  "(check 'iwlist.py --help').".format(option))

    # if program name and more than one argument are given
    if len(sys.argv) > 2:
        # Get the interface and command from command line
        ifname, option = sys.argv[1:]
        # look for matching command
        list_command = get_matching_command(option)
        # if the second argument is a command
        if list_command is not None:
            wifi = Wireless(ifname)
            list_command(wifi, sys.argv[3:])
        else:
            print("iwlist.py: unknown command `{}' "
                  "(check 'iwlist.py --help').".format(option))


if __name__ == "__main__":
    main()
