#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 Martin Kousal.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class energyDetector(gr.sync_block):
    """
    Energy detector block


    output: vector of size FFTSize with occupancy per FFT bin
    1 - signal detected (occupied)
    0 - no signal detected (free)
    

    inputs:
      0) vector of complex samples of size FFTSize
      1) uint8 detect_ctrl stream
         0 -> run sensing and update occupancy state
         non-zero -> hold previous occupancy state



    """
    def __init__(self, FFTSize=4096, numSubbands=64, threshold=0.5):
        self.FFTSize = FFTSize
        self.numSubbands = numSubbands
        self.threshold = threshold

        assert FFTSize % numSubbands == 0, \
            "FFT size must be divisible by number of subbands"
        
        self.subbandSize = FFTSize // numSubbands
        self.last_occupancy = np.zeros(self.FFTSize, dtype=np.float32)

        gr.sync_block.__init__(self,
            name="energyDetector",
            in_sig=[(np.complex64, FFTSize), np.uint8],
            out_sig=[(np.float32, FFTSize), ])
        
    def set_threshold(self, threshold):
        self.threshold = threshold
        print(f"Threshold set to: {self.threshold}")

    def set_numSubbands(self, numSubbands):
        assert self.FFTSize % numSubbands == 0, \
            "FFT size must be divisible by number of subbands"
        self.numSubbands = numSubbands
        self.subbandSize = self.FFTSize // numSubbands
        print(f"Number of subbands set to: {self.numSubbands}, subband size: {self.subbandSize}")

    def work(self, input_items, output_items):
        in0 = input_items[0]
        detect_ctrl_in = input_items[1]
        out = output_items[0]
        numSubbands = self.numSubbands
        subbandSize = self.subbandSize
        nitems = min(len(in0), len(detect_ctrl_in), len(out))

        for vectorIndex in range(nitems):
            detect_ctrl = detect_ctrl_in[vectorIndex] != 0

            if detect_ctrl:
                out[vectorIndex, :] = self.last_occupancy
                continue

            subbands = np.reshape(in0[vectorIndex], (numSubbands, subbandSize))
            power_values = np.sum(np.abs(subbands)**2, axis=1) / subbandSize
            power_values = 10 * np.log10(power_values + 1e-12)  # Convert to dB scale

            # Calculate dynamic range for thresholding
            min_power = np.min(power_values)
            max_power = np.max(power_values)
            dynamic_threshold = min_power + self.threshold * (max_power - min_power)

            # Apply detection based on threshold
            detected = (power_values > dynamic_threshold).astype(np.float32)
            # Expand each subband decision to all FFT bins in that subband.
            occupancy_bins = np.repeat(detected, subbandSize).astype(np.float32)

            self.last_occupancy = occupancy_bins
            out[vectorIndex, :] = self.last_occupancy

        return nitems
