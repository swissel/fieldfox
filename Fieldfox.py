import pyvisa as visa
import os
import numpy as np
import matplotlib.pyplot as pyp
import datetime
import string
import time
import pandas as pd
import sys

def readHeader():
     # Create the frequency header information manaually.
    head = {}
    head['center_freq_hz'] = float(sa.query("SENS:FREQ:CENT?;*OPC?").split(';')[0])
    head['rbw_hz'] = float(sa.query("SENS:BAND:RES?;*OPC?").split(';')[0])
    head['vbw_hz'] = float(sa.query("SENS:BAND:VID?;*OPC?").split(';')[0])
    head['span_hz'] = float(sa.query("SENS:FREQ:SPAN?;*OPC?").split(';')[0])
    head['start_freq_hz'] = float(sa.query("SENS:FREQ:START?;*OPC?").split(';')[0])
    head['stop_freq_hz'] = float(sa.query("SENS:FREQ:STOP?;*OPC?").split(';')[0])
        
    # A couple of parameters that are used subsequently
    head['date'] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    head['units'] = sa.query("SENS:AMPL:UNIT?;*OPC?").split(';')[0]
    head['npoints'] = int(sa.query("SENS:SWE:POIN?;*OPC?").split(';')[0])
    #print(f"{head}")

    # Read the scale properties as well
    head['scale'] = sa.query("SENS:AMPL:SCAL?;*OPC?") # LOG / LINEAR
    head['unit'] = sa.query("SENS:AMPL:UNIT?;*OPC?") # Units : dBm / W or others
    #head['dB_pdiv'] = sa.query('DISP:WIND:TRAC1:Y:SCAL:PDIV;*OPC?') #units per division
    #head['ref_dB'] = sa.query('DISP:WIND:TRAC1:Y:SCAL:RLEV;*OPC?') #ref level in dB
    #head['red_pos_dB'] = sa.query('DISP:WIND:TRAC1:Y:SCAL:RPOS;*OPC?') #ref level in dB, i think these two are the same?

    freq_hz = np.linspace(head['start_freq_hz'],
                    head['stop_freq_hz'], head['npoints'])

    print('%d Spectrum at '%(len(headStream)+1), head['date'], "with", len(freq_hz), "points")
    return head, freq_hz

def readData(sweep_time_s=0.):

    sa.write('INIT:IMM')
    # wait for the spectrum to reset	
    print("..........waiting........", sweep_time_s, " s")  
    time.sleep(sweep_time_s)   

    dataStr = sa.query("TRAC:DATA?")
    data = np.array([float(datum) for datum in dataStr.split(",")])
    # This assumes that the data are all negative (which may not be true!!!)
    # It works if the units are in dBm
    #print(f"{dataStr}")
    #firstNegSign = dataStr.find("-")
    #data = np.array([float(datum)
    #                for datum in dataStr[firstNegSign:].split(',')])
    return data

def readSpectrum(sweep_time_s=0):
    # Read a header
    print('Initiating sweep')
    sa.write('INIT:CONT 0')
    print('Attempting to read')      
    head, freq_hz = readHeader()
    data = readData(sweep_time_s)

    headStream[len(headStream)] = head
    dataStream[len(dataStream)] = {'power_dBm': data, 'freq_hz': freq_hz}

    return head, freq_hz, data, headStream, dataStream
        
def readSpectrogram(nspectra=10, sweep_time_s=0):
    print('Initiating sweep')
    sa.write('INIT:CONT 0')
    
    # The true sweep time (displayed on the FieldFox screen)
    # is larger than the stored value, since the stored value doesn't include the 
    # overhead of dipslaying, queries, etc.
    # So the 6500 multiplier is an empirical value determined
    # to keep the fieldfox from giing qruery interrupted errors.
    #sweep_time_s = float(sa.query("SWE:TIME?;*OPC")) * 3250 
    #print("Waiting ", sweep_time_s, " s for the spectrum to reset.")
    
    #time.sleep(sweep_time_s)     
    sa.write('INIT:IMM')
    # wait for the spectrum to reset	
    time.sleep(sweep_time_s)   

    #sweep_mode = sa.query("*OPC?")
    #print(sweep_mode)
    for i in range(nspectra):   
        print('Read the sweep')
        head, freq_hz, data, headStream, dataStream = readSpectrum(sweep_time_s)
	# print(f"{head}, {freq_hz}, {data}")
    return head, freq_hz, data, headStream, dataStream

def plotSpectrum(head, freq_hz, data):
    pyp.figure(figsize=(8, 16))
    pyp.subplot(2, 1, 1)
    pyp.title(head['date'])
    pyp.plot(freq_hz/1e6, data)
    pyp.xlabel("Frequency (MHz)")
    pyp.ylabel("Power (dBm)")
    pyp.subplot(2, 1, 2)
    pyp.plot(freq_hz/1e6, data - 10. * np.log10(head['rbw_hz']))
    pyp.xlabel("Frequency (MHz)")
    pyp.ylabel("Power Spectral Density (dBm/Hz)")

def plotSpectra(headStream, dataStream):
    pyp.figure(figsize=(8, 16))

    nspectra = len(headStream)
    # Get all the time stamps
    timestamps = [ headStream[num]['date'] for num in range(nspectra) ]
    datestrf = '%d/%m/%Y %H:%M:%S'#'%Y-%m-%d-%W-%H-%M-%S'
    datetimestamps = [datetime.datetime.strptime(
            ts, datestrf) for ts in timestamps]

    starttime = datetimestamps[0]
    tdelta = np.zeros(len(datetimestamps))
    for i, ts in enumerate(datetimestamps):
            tdelta[i] = (ts - starttime).total_seconds()

    # plot
    for i, dt in enumerate(tdelta):
            timestamp = timestamps[i]
            spec = dataStream[i]['power_dBm']
            freq = dataStream[i]['freq_hz']/1e6
            
            # This assumes the Fieldfox is in the default mode of 
            # units in dB ranther than in PSD mode. 
            # You can double check the units by Scale/Amptd->More->PSD Function ON
            pyp.subplot(2, 1, 1)
            pyp.title(starttime.strftime(format=datestrf))
            pyp.plot(freq, spec) #units dBm
            pyp.xlabel("Frequency (MHz)")
            pyp.ylabel("Power (dBm)")

            # convret to a power spectral density (PSD)
            # by dividing by the resolution bandwidht (RBW)
            pyp.subplot(2, 1, 2)
            pyp.title(starttime.strftime(format=datestrf))
            pyp.plot(freq, spec - 10 * np.log10(headStream[i]['rbw_hz'])) #units dBm
            pyp.xlabel("Frequency (MHz)")
            pyp.ylabel("Power (dBm/Hz)")
    pyp.savefig("%s/spectra_%s.pdf"%(dirc,datestr), bbox_inches='tight')
		

def plotSpectrogram(headStream, dataStream):
        pyp.figure(figsize=(8, 16))
        pyp.subplot(2, 1, 1)
        #pyp.title(self.datestr)

        nspectra = len(headStream)
        # Get all the time stamps
        timestamps = [ headStream[num]['date'] for num in range(nspectra) ]
        datestrf = '%d/%m/%Y %H:%M:%S'#'%Y-%m-%d-%W-%H-%M-%S'
        datetimestamps = [datetime.datetime.strptime(
            ts, datestrf) for ts in timestamps]

        starttime = datetimestamps[0]
        tdelta = np.zeros(len(datetimestamps))
        for i, ts in enumerate(datetimestamps):
            tdelta[i] = (ts - starttime).total_seconds()

        # Setup the spectrogram array
        spectrogram = np.zeros((nspectra, headStream[0]['npoints']))
        for i, dt in enumerate(tdelta):
            timestamp = timestamps[i]
            spec = dataStream[i]['power_dBm']
            spectrogram[i, :] = spec

        # make a mesh for plotting
        freqmesh, timemesh = np.meshgrid(dataStream[i]['freq_hz']/1e6, tdelta)

        # plot!
        pyp.pcolormesh(freqmesh, timemesh, spectrogram)
        pyp.xlabel("Frequency (MHz)")
        pyp.ylabel("Time(s)")
        pyp.title(starttime.strftime(format=datestrf))
        cbar = pyp.colorbar()
        cbar.set_label("Power (dBm)")

        # plot!
        pyp.subplot(2, 1, 2)
        pyp.pcolormesh(freqmesh, timemesh, spectrogram -
                       10.*np.log10(headStream[i]['rbw_hz']/1e6))
        pyp.xlabel("Frequency (MHz)")
        pyp.ylabel("Time(s)")
        pyp.title(starttime.strftime(format=datestrf))
        cbar = pyp.colorbar()
        cbar.set_label("Power (dBm/MHz)")
        
        pyp.savefig("%s/spectrogram_%s.png"%(dirc,datestr), bbox_inches='tight')

def writeSpectrum(dirc, outputFileName, timestamp, headStream, dataStream):
    print("Writing data to %s%s" % (dirc, outputFileName))

    run_header = pd.DataFrame({'run': run, 'timestamp': timestamp, 'filename': outputFileName}, index=[0])
    run_header.to_hdf(dirc + outputFileName, key='run_header', mode='a', )
    headerStored = True

    headDf = pd.DataFrame(headStream)
    dataDf = pd.DataFrame(dataStream)
    headDf.to_hdf(dirc + outputFileName, key='header', mode='a')
    dataDf.to_hdf(dirc + outputFileName, key='spectra', mode='a')

def run(npsectra, wait_time_s):
    
    head, freq_hz, data, headStream, dataStream = readSpectrogram(nspectra, wait_time_s)
    #plotSpectrum(head, freq_hz, data)
    plotSpectra(headStream, dataStream)
    plotSpectrogram(headStream, dataStream)
    #pyp.show()

    writeSpectrum(dirc, outputFileName, timestamp, headStream, dataStream)

if __name__ == "__main__":

   nspectra = 1   
   wait_time_s = 0.1
   dirc = '/home/radio/data/rnog/2022/'
   if( len(sys.argv) == 1):
        print("\nUsage: fieldfox_spectra <nspectra, required> <wait time in s, default=%1.2f s> <output directory default %s>\n"%(wait_time_s, dirc))
        print("       Make sure to set up the Fieldfox with your preferred settings.")
        print("       in terms of the frequency range, number of points in the spectrum,")
        print("       amplitude and scale, and video and resolution bandwidth.")
        print("       Once you're happy, check the sweep time on the screen and set the")
        print("       wait time to a little more than the sweep time.")
        print("\n       Keep the PSD settings off (Scale/Amptd->More->PSD OFF).")
        print("       But you can divides out the RBW to get the power spectral density")
        print("       in units of dB/Hz which you can compare to your output.\n") 
        exit()

   if( len(sys.argv) > 1):
        nspectra = int(sys.argv[1])
   if( len(sys.argv) > 2):
        wait_time_s = float(sys.argv[2])
   if( len(sys.argv) > 3):
        dirc = sys.argv[3] 

   # Setup the instrument
   rm = visa.ResourceManager("/home/radio/keysight/iolibs/libktvisa32.so")
   sa = rm.get_instrument("TCPIP0::169.254.24.71::inst0::INSTR")
   sa.write("*IDN?")
   print("Talking to instrument", sa.read())

   # dictionaries to store the data
   headStream = {}
   dataStream = {}
   
   # time stamp
   timestamp = time.time()
   datestr = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
   outputFileName = "specanalyzer_%s.hdf5" % ( datestr)
   print("File name %s" % outputFileName)

   run(nspectra, wait_time_s)
