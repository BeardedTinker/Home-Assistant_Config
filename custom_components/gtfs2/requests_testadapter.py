#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 by Łukasz Langa
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""requests_testadapter
   --------------------

   An adapter for `requests <https://pypi.python.org/pypi/requests>`_ that
   enables easy unit testing of applications otherwise relying on Internet
   connectivity."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import BytesIO

from requests.compat import OrderedDict
import requests.adapters
import requests.status_codes


class Resp(BytesIO):
    def __init__(self, stream, status=200, headers=None):
        self.status = status
        self.headers = headers or {}
        self.reason = requests.status_codes._codes.get(
            status, ['']
        )[0].upper().replace('_', ' ')
        BytesIO.__init__(self, stream)

    @property
    def _original_response(self):
        return self

    @property
    def msg(self):
        return self

    def read(self, chunk_size, **kwargs):
        return BytesIO.read(self, chunk_size)

    def info(self):
        return self

    def get_all(self, name, default):
        result = self.headers.get(name)
        if not result:
            return default
        return [result]

    def getheaders(self, name):
        return self.get_all(name, [])

    def release_conn(self):
        self.close()


class TestAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, stream, status=200, headers=None):
        self.stream = stream
        self.status = status
        self.headers = headers or {}
        super(TestAdapter, self).__init__()

    def send(self, request, stream=False, timeout=None,
             verify=True, cert=None, proxies=None):
        resp = Resp(self.stream, self.status, self.headers)
        r = self.build_response(request, resp)
        if not stream:
            # force prefetching content unless streaming in use
            r.content
        return r


class TestSession(requests.Session):
    """Just like requests.Session but solves an issue with adapter ordering
       for requests 1.2.0 and lower. It also doesn't connect the default
       handlers for HTTP and HTTPS so you will be notified if your requests
       unintentionally try to reach external websites in your unit tests."""

    def __init__(self):
        super(TestSession, self).__init__()
        self.adapters = OrderedDict()

    def mount(self, prefix, adapter):
        """Registers a connection adapter to a prefix.

        Adapters are sorted in descending order by key length."""
        self.adapters[prefix] = adapter
        keys_to_move = [k for k in self.adapters if len(k) < len(prefix)]
        for key in keys_to_move:
            self.adapters[key] = self.adapters.pop(key)