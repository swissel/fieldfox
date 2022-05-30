# quick check of the data

import matplotlib.pyplot as pyp
import numpy as np
import datetime
import sys
import pandas as pd

file = '/Users/swissel/work/rnog/specanalysis/specanalyzer_2022-05-29_14-20-25.hdf5'
if( len(sys.argv) > 1):
    file = sys.argv
 
head = pd.read_hdf(file, key='header')
spectra = pd.read_hdf(file, key='spectra')

nspectra = len(spectra.keys())
npoints = head[0].npoints
rbw_hz = head[0].rbw_hz
print(nspectra, npoints)

# Read the timestamps
datestrf = '%d/%m/%Y %H:%M:%S'
timestamps = [head[i].date for i in range(nspectra)]
datetimestamps = [datetime.datetime.strptime(ts, datestrf) for ts in timestamps]

# Plot the spectra
pyp.figure()
for i in range(0,nspectra, 1):
    freq = spectra[i].freq_hz
    pyp.plot(freq/1e6, spectra[i].power_dBm)
    
pyp.xlabel("Frequency (MHz)")
pyp.ylabel("Power (dBm)")
pyp.title("Power Spectrum")


# Plot the PSDs
pyp.figure()
for i in range(0,nspectra, 1):
    freq = spectra[i].freq_hz
    pyp.plot(freq/1e6, spectra[i].power_dBm - 10.*np.log10(rbw_hz/1e6))
    
pyp.xlabel("Frequency (MHz)")
pyp.ylabel("Power Spectral Density (dBm/MHz)")
pyp.title("Power Spectral Density")


# Plot the Spectrogram
pyp.figure()
starttime = datetimestamps[0]
tdelta = np.zeros(len(datetimestamps))
for i,ts in enumerate(datetimestamps):
    tdelta[i] = (ts - starttime).total_seconds()

spectrogram = np.zeros( (nspectra, npoints))
print(np.shape(spectrogram))
for i in range(nspectra):
    timestamp = timestamps[i]
    spec = spectra[i].power_dBm
    spectrogram[i,:] = spec
    
freq = spectra[i].freq_hz    
freqmesh, timemesh = np.meshgrid(freq/1e6, tdelta)

pyp.pcolormesh(freqmesh,timemesh, spectrogram)
cbar = pyp.colorbar()
cbar.set_label("Power (dBm)")
pyp.xlabel("Frequency (MHz)")
pyp.ylabel("Time (s)")
pyp.title(starttime.strftime(format=datestrf))


# Plot the Spectrogram in PSD
pyp.figure()
pyp.pcolormesh(freqmesh,timemesh, spectrogram-10*np.log10(rbw_hz/1e6))
cbar = pyp.colorbar()
cbar.set_label("Power (dBm/MHz)")
pyp.xlabel("Frequency (MHz)")
pyp.ylabel("Time (s)")
pyp.title(starttime.strftime(format=datestrf))

pyp.show()

