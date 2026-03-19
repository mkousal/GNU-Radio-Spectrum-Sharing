#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 Martin Kousal.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class carrierAllocator(gr.basic_block):
    """
    OFDM carrier allocator driven by subband occupancy from energyDetector.

    Inputs:
      0) float32 vector of length FFTSize
      - occupancy flags per FFT bin:
        1.0 -> occupied (do not use)
        0.0 -> free (may be used)
      1) uint8 scalar stream (TX enable switch):
        0 -> do not transmit (output zeros)
        non-zero -> transmit on free subcarriers

    Output:
      complex64 vector of length FFTSize
      - time-domain OFDM symbol (IFFT of allocated carriers)
      - data are placed only on free (not occupied) subcarriers
    """
    def __init__(self, FFTSize=4096, numSubbands=64, txAmplitude=1.0, seed=0):
        self.FFTSize = FFTSize
        self.numSubbands = numSubbands
        self.txAmplitude = txAmplitude
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        assert FFTSize > 0, "FFT size must be positive"
        assert numSubbands > 0, "Number of subbands must be positive"
        assert FFTSize % numSubbands == 0, \
            "FFT size must be divisible by number of subbands"

        self.subbandSize = FFTSize // numSubbands
        self.qpsk_scale = np.float32(self.txAmplitude / np.sqrt(2.0))

        gr.basic_block.__init__(self,
            name="carrierAllocator",
            in_sig=[(np.float32, FFTSize), np.uint8],
            out_sig=[(np.complex64, FFTSize), ])

    def set_numSubbands(self, numSubbands):
        assert numSubbands > 0, "Number of subbands must be positive"
        assert self.FFTSize % numSubbands == 0, \
            "FFT size must be divisible by number of subbands"
        self.numSubbands = numSubbands
        self.subbandSize = self.FFTSize // self.numSubbands
        print(f"Number of subbands set to: {self.numSubbands}")

    def set_FFTSize(self, FFTSize):
        assert FFTSize > 0, "FFT size must be positive"
        assert FFTSize % self.numSubbands == 0, \
            "FFT size must be divisible by number of subbands"
        self.FFTSize = FFTSize
        self.subbandSize = self.FFTSize // self.numSubbands
        print(f"FFT size set to: {self.FFTSize}")

    def set_txAmplitude(self, txAmplitude):
        self.txAmplitude = txAmplitude
        self.qpsk_scale = np.float32(self.txAmplitude / np.sqrt(2.0))
        print(f"TX amplitude set to: {self.txAmplitude}")

    def _generate_qpsk(self, n):
        if n <= 0:
            return np.empty(0, dtype=np.complex64)
        i = self.rng.choice(np.array([-1.0, 1.0], dtype=np.float32), size=n)
        q = self.rng.choice(np.array([-1.0, 1.0], dtype=np.float32), size=n)
        return (i + 1j * q).astype(np.complex64) * self.qpsk_scale

    def forecast(self, noutput_items, ninputs):
        return [noutput_items] * ninputs

    def general_work(self, input_items, output_items):
        occupancy_in = input_items[0]
        tx_enable_in = input_items[1]
        out = output_items[0]

        nitems = min(len(occupancy_in), len(tx_enable_in), len(out))
        if nitems <= 0:
            return 0

        for vectorIndex in range(nitems):
            tx_enable = tx_enable_in[vectorIndex] != 0

            if not tx_enable:
                out[vectorIndex, :] = 0
                continue

            occupancy = occupancy_in[vectorIndex, :]
            # print(f"Vector {vectorIndex}: Occupancy input: {occupancy[:10]}...")  # Debug print for first 10 bins
            free_bins_mask = occupancy < 0.5
            free_bins = np.flatnonzero(free_bins_mask)
            # free_bins = np.flatnonzero(occupancy)
            # print(f"Vector {vectorIndex}: {len(free_bins)} free bins")

            ofdm_symbol = np.zeros(self.FFTSize, dtype=np.complex64)
            ofdm_symbol[free_bins] = self._generate_qpsk(len(free_bins))
            # ofdm_symbol = np.fft.ifft(ofdm_symbol, n=self.FFTSize)
            out[vectorIndex, :] = ofdm_symbol

        self.consume_each(nitems)
        return nitems
