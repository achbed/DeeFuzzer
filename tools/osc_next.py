#!/usr/bin/env python

import liblo, sys

# send all messages to port 1234 on the local machine
try:
    target = liblo.Address(1234)
except liblo.AddressError, err:
    print str(err)
    sys.exit()

# send message "/foo/message1" with int, float and string arguments
liblo.send(target, "/media/next", 1)
