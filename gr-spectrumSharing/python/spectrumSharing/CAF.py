#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 Martin Kousal.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr


def cyklicka_autokorelace1(x, tau_vec, alpha_vec):
    """Compute the 2D cyclic autocorrelation function (CAF).

    This keeps the same zero-padded delay handling used in the code the user
    supplied, while making the search vectors and peak target configurable.
    """
    x = np.asarray(x, dtype=np.complex64).flatten()
    tau_vec = np.asarray(tau_vec, dtype=np.int64).flatten()
    alpha_vec = np.asarray(alpha_vec, dtype=np.float32).flatten()

    sample_count = len(x)
    caf = np.zeros((len(alpha_vec), len(tau_vec)), dtype=np.complex64)
    if sample_count == 0 or tau_vec.size == 0 or alpha_vec.size == 0:
        return caf

    n = np.arange(sample_count, dtype=np.float32)
    exp_matrix = np.exp(-1j * 2.0 * np.pi * np.outer(alpha_vec, n))

    for tau_index, tau in enumerate(tau_vec):
        x_shifted = np.zeros_like(x)

        if tau > 0:
            if tau < sample_count:
                x_shifted[tau:] = x[:-tau]
        elif tau < 0:
            tau_abs = abs(tau)
            if tau_abs < sample_count:
                x_shifted[:-tau_abs] = x[tau_abs:]
        else:
            x_shifted[:] = x

        core_product = x * np.conj(x_shifted)
        caf[:, tau_index] = (1.0 / sample_count) * np.dot(exp_matrix, core_product)

    return caf


class CAF(gr.sync_block):
    """Cyclic autocorrelation estimator for GNU Radio.

    Stream outputs provide a quick metric and the peak CAF magnitude.
    The full CAF mesh is emitted as a flattened stream vector.
    """

    def __init__(
        self,
        input_len=1024,
        tau_vec=None,
        alpha_vec=None,
        peak_tau=-128,
        peak_alpha=0.0,
    ):
        self.input_len = int(input_len)
        self.tau_vec = np.asarray(
            np.arange(-130, -124) if tau_vec is None else tau_vec,
            dtype=np.int64,
        ).flatten()
        self.alpha_vec = np.asarray(
            np.linspace(0.0, 0.0002, 5) if alpha_vec is None else alpha_vec,
            dtype=np.float32,
        ).flatten()
        self.peak_tau = int(peak_tau)
        self.peak_alpha = float(peak_alpha)

        self.mesh_len = int(self.tau_vec.size * self.alpha_vec.size)
        self._validate_parameters()
        self.last_result = {}

        gr.sync_block.__init__(
            self,
            name="CAF",
            in_sig=[(np.complex64, self.input_len)],
            out_sig=[np.float32, (np.float32, self.mesh_len)],
        )

    def _validate_parameters(self):
        if self.input_len <= 0:
            raise ValueError("input_len must be positive")
        if self.tau_vec.size == 0:
            raise ValueError("tau_vec must not be empty")
        if self.alpha_vec.size == 0:
            raise ValueError("alpha_vec must not be empty")
        if self.mesh_len <= 0:
            raise ValueError("mesh_len must be positive")

    def _nearest_index(self, values, target):
        values = np.asarray(values)
        if values.size == 0:
            raise ValueError("Search vector is empty")
        return int(np.argmin(np.abs(values - target)))

    def _update_last_result(self, caf_mat):
        ix_tau = self._nearest_index(self.tau_vec, self.peak_tau)
        ix_alpha = self._nearest_index(self.alpha_vec, self.peak_alpha)

        baseline = float(np.mean(np.abs(caf_mat[0, :]))) if caf_mat.size else 0.0
        peak_value = caf_mat[ix_alpha, ix_tau]
        metric = float(np.abs(peak_value) / baseline) if baseline > 0.0 else 0.0

        self.last_result = {
            "tau_vec": self.tau_vec.copy(),
            "alpha_vec": self.alpha_vec.copy(),
            "caf_mat": caf_mat.copy(),
            "caf_abs": np.abs(caf_mat).astype(np.float32),
            "metric": np.float32(metric),
            "peak_tau": int(self.tau_vec[ix_tau]),
            "peak_alpha": float(self.alpha_vec[ix_alpha]),
            "peak_value": np.complex64(peak_value),
            "peak_value_abs": np.float32(np.abs(peak_value)),
            "peak_tau_index": ix_tau,
            "peak_alpha_index": ix_alpha,
        }

        return metric, peak_value

    def get_last_result(self):
        return self.last_result.copy()

    def set_tau_vec(self, tau_vec):
        tau_vec = np.asarray(tau_vec, dtype=np.int64).flatten()
        if tau_vec.size != self.tau_vec.size:
            raise ValueError("tau_vec length cannot change at runtime")
        self.tau_vec = tau_vec

    def set_alpha_vec(self, alpha_vec):
        alpha_vec = np.asarray(alpha_vec, dtype=np.float32).flatten()
        if alpha_vec.size != self.alpha_vec.size:
            raise ValueError("alpha_vec length cannot change at runtime")
        self.alpha_vec = alpha_vec

    def set_peak_tau(self, peak_tau):
        self.peak_tau = int(peak_tau)

    def set_peak_alpha(self, peak_alpha):
        self.peak_alpha = float(peak_alpha)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out_metric = output_items[0]
        out_mesh = output_items[1]

        nitems = min(len(in0), len(out_metric), len(out_mesh))
        if nitems <= 0:
            return 0

        for vector_index in range(nitems):
            x_filtered = in0[vector_index]
            caf_mat = cyklicka_autokorelace1(x_filtered, self.tau_vec, self.alpha_vec)
            metric, peak_value = self._update_last_result(caf_mat)
            out_metric[vector_index] = np.float32(metric)
            out_mesh[vector_index, :] = np.abs(caf_mat).astype(np.float32).ravel()

        return nitems
