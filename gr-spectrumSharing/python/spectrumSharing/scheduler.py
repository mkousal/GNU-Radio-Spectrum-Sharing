#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 Martin Kousal.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class scheduler(gr.sync_block):
    """
    Periodic TX-enable scheduler:
      outputs 1 for on_ms, then 0 for off_ms, repeating.

    Note:
      sample_rate is the rate of this control stream (items/s), not
      necessarily the RF sample rate of your flowgraph.
    """
    def __init__(self, sample_rate=1e6, on_ms=1.0, off_ms=9.0):
        self.sample_rate = float(sample_rate)
        self.on_ms = float(on_ms)
        self.off_ms = float(off_ms)
        self._update_lengths()
        self.phase = 0

        gr.sync_block.__init__(self,
            name="scheduler",
            in_sig=None,
            out_sig=[np.uint8, ])

    def _update_lengths(self):
        assert self.sample_rate > 0.0, "sample_rate must be positive"
        assert self.on_ms > 0.0, "on_ms must be positive"
        assert self.off_ms > 0.0, "off_ms must be positive"
        self.high_len = max(1, int(round(self.sample_rate * (self.on_ms * 1e-3))))
        self.low_len = max(1, int(round(self.sample_rate * (self.off_ms * 1e-3))))
        self.period_len = self.high_len + self.low_len

    def set_sample_rate(self, sample_rate):
        self.sample_rate = float(sample_rate)
        self._update_lengths()

    def set_on_ms(self, on_ms):
        self.on_ms = float(on_ms)
        self._update_lengths()

    def set_off_ms(self, off_ms):
        self.off_ms = float(off_ms)
        self._update_lengths()


    def work(self, input_items, output_items):
        out = output_items[0]
        n = len(out)
        if n == 0:
            return 0

        idx = (self.phase + np.arange(n, dtype=np.int64)) % self.period_len
        out[:] = (idx < self.high_len).astype(np.uint8)
        self.phase = (self.phase + n) % self.period_len
        # print(f"Scheduler output: {out[:10]}...")  # Debug print for first 10 items
        return n
