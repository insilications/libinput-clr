#!/usr/bin/env python3
# -*- coding: utf-8
# vim: set expandtab shiftwidth=4:
# -*- Mode: python; coding: utf-8; indent-tabs-mode: nil -*- */
#
# Copyright © 2021 Red Hat, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the 'Software'),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
#
# Measures the relative motion between touch events (based on slots)
#
# Input is a libinput record yaml file


import argparse
import libevdev
import sys
import yaml

class Multiplier:
    """The kernel doesn't expose the multiplier, this class is a simple way to
    guess it by using the average of all events"""
    def __init__(self):
        self.count = 0
        self.value = 0
        self.min_mult = 120

    def add(self, value):
        self.count += 1
        self.value += abs(value)
        if value != 0:
            self.min_mult = min([self.min_mult, abs(value)])

    @property
    def multiplier(self):
        return 120//self.min_mult

    @property
    def average(self):
        return self.value//self.count if self.count else 0


class WheelEvent:
    def __init__(self):
        self.lores = 0
        self.hires = []

    def add_lores(self, value):
        self.lores = value

    def add_hires(self, value):
        self.hires += [value]

    @property
    def hires_count(self):
        return len(self.hires)

    @property
    def hires_distance(self):
        """Returns a tuple of the distance travelled and the abs distance traveled"""
        return sum(self.hires), sum([abs(x) for x in self.hires])


def main(argv):
    parser = argparse.ArgumentParser(
        description="Analyse scroll wheel data"
    )
    parser.add_argument(
        "path", metavar="recording", nargs=1, help="Path to libinput-record YAML file"
    )
    args = parser.parse_args()

    yml = yaml.safe_load(open(args.path[0]))
    device = yml["devices"][0]

    try:
        if libevdev.EV_REL.REL_WHEEL.value not in device["evdev"]["codes"][libevdev.EV_REL.value]:
            print("Device does not have a scroll wheel")
            sys.exit(1)
        if libevdev.EV_REL.REL_WHEEL_HI_RES.value not in device["evdev"]["codes"][libevdev.EV_REL.value]:
            print("Device does not have a high-res scroll wheel")
            sys.exit(1)
    except KeyError:
            print("Device does not have a scroll wheel")
            sys.exit(1)

    # We're calculating the multiplier first because that matters for the
    # follow-up calculation
    multiplier = Multiplier()
    for event in device["events"]:
        for evdev in event["evdev"]:
            e = libevdev.InputEvent(
                code=libevdev.evbit(evdev[2], evdev[3]),
                value=evdev[4],
                sec=evdev[0],
                usec=evdev[1],
            )

            if e.code == libevdev.EV_REL.REL_WHEEL_HI_RES:
                multiplier.add(e.value)


    print(f"Wheel multiplier: {multiplier.multiplier} (avg value {multiplier.average})")

    wheel_events = []
    def new_wheel_seq():
        wheel = WheelEvent()
        wheel_events.append(wheel)
        return wheel

    wheel = new_wheel_seq()

    for event in device["events"]:
        for evdev in event["evdev"]:
            e = libevdev.InputEvent(
                code=libevdev.evbit(evdev[2], evdev[3]),
                value=evdev[4],
                sec=evdev[0],
                usec=evdev[1],
            )

            if e.code == libevdev.EV_REL.REL_WHEEL_HI_RES:
                wheel.add_hires(e.value)
            elif e.code == libevdev.EV_REL.REL_WHEEL:
                wheel.add_lores(e.value)
                wheel = new_wheel_seq()

    print(f"| REL_WHEEL | REL_WHEEL_HI_RES ")
    for w in wheel_events:
        count = w.hires_count
        dist, absdist = w.hires_distance
        def wfmt(l):
            return ", ".join([f"{x:3d}" for x in l])
        print(f"| {w.lores:9d} | {count:3d} events, distance {dist:4d}, absolute distance {absdist:4d} | {wfmt(w.hires)}")

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
