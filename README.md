# GNU-Radio-Spectrum-Sharing

GNU Radio Out-of-Tree (OOT) module implementing dynamic spectrum sharing for OFDM-based systems. This module enables cognitive radio applications with spectrum sensing, intelligent carrier allocation, and transmission scheduling.

**Key Features:**
- **Spectrum Sensing**: Energy detection of occupied/free frequency bands
- **Cognitive Radio**: Dynamic allocation of free OFDM subcarriers
- **Periodic Scheduling**: Time-based transmission control for secondary users
- **Real-time Processing**: Implemented in Python for prototyping and accessibility

---

## Requirements

### System Requirements
- **GNU Radio**: 3.10.9.2 or later
- **Python**: 3.8 or later
- **CMake**: 3.8 or later
- **C++ Compiler**: GCC 7.0+ or Clang 5.0+
- **Build Tools**: make, git

### Python Dependencies
- `numpy`: Numerical computing library
- `gnuradio`: Core GNU Radio framework (3.10+)

### Optional (for hardware-based demos)
- **USRP Hardware**: Ettus Research USRP (N-series recommended)
- **UHD Drivers**: Compatible with your USRP model
- **GNU Radio Companion (GRC)**: For visual flowgraph editing

### Tested Platform
- Linux Ubuntu 24.04 with USRP B210 over USB3


---

## Architecture & Blocks

### System Overview

The module consists of three main interconnected blocks for dynamic spectrum sharing:

```
scheduler → tx_enable
              ↓
          [carrierAllocator] → TX data (OFDM)
              ↑
         occupancy
              ↑
        [energyDetector]
              ↑
        RF input (RX)
```

### Block Summary

#### 1. energyDetector
Performs spectrum sensing by analyzing received RF signals.
- **Input**: Complex OFDM symbols (FFT output) + control signal
- **Output**: Binary occupancy flags (1=occupied, 0=free) per FFT bin
- **Parameters**: FFTSize, numSubbands, threshold

#### 2. carrierAllocator
Performs intelligent OFDM carrier allocation.
- **Input**: Occupancy flags + TX enable control
- **Output**: Frequency-domain OFDM symbol with QPSK data on free bins
- **Parameters**: FFTSize, numSubbands, txAmplitude, seed

#### 3. scheduler
Generates periodic TX enable/disable control signals.
- **Output**: Binary TX enable stream (1=transmit, 0=silent)
- **Parameters**: sample_rate, on_ms, off_ms

---

## Installation & Building

### Step 1: Prerequisites Installation

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    gnuradio \
    gnuradio-dev \
    libgnuradio-dev \
    cmake \
    build-essential \
    git \
    python3-dev \
    python3-numpy
```

### Step 2: Build the Module

Navigate to the gr-spectrumSharing directory and build:

```bash
cd gr-spectrumSharing
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
```

### Step 3: Verify Installation

Check that the module is properly installed:
```bash
# Test Python import
python3 -c "from gnuradio import spectrumSharing; print('Module imported successfully')"

# Verify GRC blocks are available
find ~/.local/share/gnuradio -name "*spectrumSharing*.block.yml"
# or
find /usr/share/gnuradio -name "*spectrumSharing*.block.yml"
```

---

## Demo Flowgraph

### Overview

The file `final_scheme_real_hardware.grc` is a complete demonstration of the spectrum-sharing system using real USRP hardware.

**Flowgraph Features:**
- Full transceiver implementation (RX + TX paths)
- Real-time spectrum sensing and dynamic allocation
- GUI controls for parameter adjustment
- USRP source and sink integration
- FFT processing for spectrum analysis

### Running the Demo

1. **Open in GNU Radio Companion:**
   ```bash
   gnuradio-companion final_scheme_real_hardware.grc
   ```

2. **Hardware Setup:**
   - Connect USRP to computer via Ethernet/USB
   - Verify USRP is detected: `uhd_find_devices`
   - Set USRP center frequency and gain in GRC parameters

3. **Configure Parameters:**
   - **FFTSize**: 4096 (standard for many applications)
   - **numSubbands**: 64 (frequency resolution)
   - **Detection Threshold**: 0.5 (adjust sensitivity)
   - **TX Amplitude**: 0.8 (to avoid clipping)
   - **Scheduler Duty Cycle**: on_ms=1, off_ms=9 (10% duty cycle)

4. **Execute:**
   - Click the "Run" button (play icon)
   - Monitor detection results in real-time
   - Adjust sliders to tune parameters while running

---

## Usage Guide

#### Configuration Table

| Block | Parameter | Recommended | Notes |
|-------|-----------|-------------|-------|
| energyDetector | FFTSize | 4096 | Match RX FFT size |
| energyDetector | numSubbands | 64 | Frequency resolution |
| energyDetector | threshold | 0.5 | Start here, adjust ±0.1 |
| carrierAllocator | FFTSize | 4096 | Must match energyDetector |
| carrierAllocator | numSubbands | 64 | Must match energyDetector |
| carrierAllocator | txAmplitude | 0.8 | Prevent clipping |
| carrierAllocator | seed | 42 | For reproducibility |
| scheduler | sample_rate | 1e6 | Control stream rate |
| scheduler | on_ms | 9.0 | Transmission duration |
| scheduler | off_ms | 1.0 | Sensing duration |

---