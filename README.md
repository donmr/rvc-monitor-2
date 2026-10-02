# rvc-monitor-2

RV-C Monitor - Python Edition

Monitors and decodes the [RV-C CAN-Bus protocol](http://www.rv-c.com/?q=node/75) (and a bit of SAE J1939),
printing each decoded message as one JSON object per line on stdout. Can read from a live CAN interface or
replay a previously captured JSON-lines file.

This project began as a fork of [rvc-monitor-py](https://github.com/linuxkidd/rvc-monitor-py); see `NOTICE`
for details.

```
usage: rvc-monitor-2 [-h] [-i INTERFACE] [-t TYPE] [-r REPLAY] [-s SPECFILE]

options:
  -h, --help            show this help message and exit
  -i INTERFACE, --interface INTERFACE
                        CAN interface to use
  -t TYPE, --type TYPE  CAN bus type/backend (default: slcan); other options
                        supported by python-can: canalystii, cantact, etas,
                        gs_usb, iscan, ixxat, kvaser, neousys, neovi, nican,
                        nixnet, pcan, robotell, seeedstudio, serial, slcan,
                        socketcan, socketcand, systec, udp_multicast, usb2can,
                        vector, virtual
  -r REPLAY, --replay REPLAY
                        replay saved output
  -s SPECFILE, --specfile SPECFILE
                        RVC/J1939 Spec file; repeat -s to load multiple
                        (default: /etc/rvc/rvc-spec.yml and
                        /etc/rvc/sae-j1939.yml)
```

## Usage

```
# Live decode from a CAN interface, JSON to stdout
usr/bin/rvc-monitor-2 -i can0

# Replay a previously captured JSON-lines file instead of live CAN
usr/bin/rvc-monitor-2 -r some-capture.rvc

# Load additional/alternate spec files (repeatable; later files win on key collisions)
usr/bin/rvc-monitor-2 -i can0 -s etc/rvc/rvc-spec.yml -s etc/rvc/sae-j1939.yml

# Use a different python-can backend (default: slcan) e.g. a native SocketCAN interface
usr/bin/rvc-monitor-2 -i can0 -t socketcan
```

Decoded output goes to stdout only, so it can be piped (e.g. into `jq`) or redirected to a file to create a
new replay capture for later use with `-r`.

## Requirements

* A computer with a CAN-Bus interface. 

* Python package dependencies:
  ~~~
  pip3 install -r requirements.txt
  ~~~

## Tests

```
pytest
```
