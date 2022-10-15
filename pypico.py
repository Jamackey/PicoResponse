import ctypes
from picosdk.ps2000a import ps2000a as ps2000a
from picosdk.ps3000a import ps3000a as ps3000a
from picosdk.functions import adc2mV, assert_pico_ok
import numpy as np
import matplotlib.pyplot as plt
from picosdk.discover import find_unit

sine = ctypes.c_int16(0)

channel_A = 0
channel_B = 1
coupling_DC = 1

volt_range_list = {
    0.02: 1,
    0.05: 2,
    0.1: 3,
    0.2: 4,
    0.5: 5,
    1: 6,
    2: 7,
    5: 8,
    10: 9,
    20: 10
}


class PicoScope:
    def __init__(self):
        with find_unit() as device:
            name = device.info.variant.decode()
            series = name[0]
        print(f'PicoScope {name}')
        if series == '2':
            self.ps = PicoScope2000a()
        elif series == '3':
            self.ps = PicoScope3000a()


class PicoScope2000a:
    def __init__(self):
        # Gives the device a handle
        self.status = {}
        self.chandle = ctypes.c_int16()

        # Opens the device/s
        self.status["openunit"] = ps2000a.ps2000aOpenUnit(ctypes.byref(self.chandle), None)

        try:
            assert_pico_ok(self.status["openunit"])
        except:
            # powerstate becomes the status number of openunit
            powerstate = self.status["openunit"]

            # If powerstate is the same as 282 then it will run this if statement
            if powerstate == 282:
                # Changes the power input to "PICO_POWER_SUPPLY_NOT_CONNECTED"
                self.status["ChangePowerSource"] = ps2000a.ps2000aChangePowerSource(self.chandle, 282)
            # If the powerstate is the same as 286 then it will run this if statement
            elif powerstate == 286:
                # Changes the power input to "PICO_USB3_0_DEVICE_NON_USB3_0_PORT"
                self.status["ChangePowerSource"] = ps2000a.ps2000aChangePowerSource(self.chandle, 286)
            else:
                raise

            assert_pico_ok(self.status["ChangePowerSource"])

        self.sweeptype = ctypes.c_int32(0)
        self.triggertype = ctypes.c_int32(0)
        self.triggerSource = ctypes.c_int32(0)

    def signal_generator(self, wave, amplitude, frequency, offset=0):
        amplitude = int(amplitude * 1000000)
        self.status["SetSigGenBuiltIn"] = ps2000a.ps2000aSetSigGenBuiltIn(self.chandle, offset, amplitude,
                                                                          wave, frequency, frequency, 0, 1,
                                                                          self.sweeptype, 0, 0, 0,
                                                                          self.triggertype,
                                                                          self.triggerSource, 1)
        return assert_pico_ok(self.status["SetSigGenBuiltIn"])

    def block_capture(self, channel, voltage_range, duration_ms, threshold=0, pre_trigger=0):

        # Convert voltage & threshold values
        adc_bits = 65535
        voltage_range = volt_range_list[voltage_range]
        threshold = round(threshold / (voltage_range / adc_bits))

        # Set up channel A
        self.status["setChA"] = ps2000a.ps2000aSetChannel(self.chandle, channel, 1, 1, voltage_range, 0)
        assert_pico_ok(self.status["setChA"])

        # Set up single trigger
        self.status["trigger"] = ps2000a.ps2000aSetSimpleTrigger(self.chandle, 1, 0, threshold, 0, 0, 0)
        assert_pico_ok(self.status["trigger"])

        # Set number of pre and post trigger samples to be collected

        # Get timebase information
        timebase = 10
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()
        oversample = ctypes.c_int16(0)
        self.status["getTimebase2"] = ps2000a.ps2000aGetTimebase2(self.chandle,
                                                                  timebase,
                                                                  1276,
                                                                  ctypes.byref(timeIntervalns),
                                                                  oversample,
                                                                  ctypes.byref(returnedMaxSamples),
                                                                  0)
        assert_pico_ok(self.status["getTimebase2"])

        # calculate amount of samples to cover duration & add pre trigger (if any)
        print(f'Time Interval: {timeIntervalns.value}')
        samples = round((duration_ms * 1000000) / timeIntervalns.value)
        totalSamples = samples
        preTriggerSamples = samples * pre_trigger
        postTriggerSamples = samples * (100 - pre_trigger)
        print(f'Samples: {samples}')

        # Run block capture
        self.status["runBlock"] = ps2000a.ps2000aRunBlock(self.chandle,
                                                          preTriggerSamples,
                                                          postTriggerSamples,
                                                          timebase,
                                                          oversample,
                                                          None,
                                                          0,
                                                          None,
                                                          None)
        assert_pico_ok(self.status["runBlock"])

        # Check for data collection to finish using ps2000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps2000a.ps2000aIsReady(self.chandle, ctypes.byref(ready))

        # Create buffers ready for assigning pointers for data collection
        bufferAMax = (ctypes.c_int16 * totalSamples)()
        bufferAMin = (ctypes.c_int16 * totalSamples)()

        # Set data buffer location for data collection from channel A
        self.status["setDataBuffersA"] = ps2000a.ps2000aSetDataBuffers(self.chandle,
                                                                       0,
                                                                       ctypes.byref(bufferAMax),
                                                                       ctypes.byref(bufferAMin),
                                                                       totalSamples,
                                                                       0,
                                                                       0)
        assert_pico_ok(self.status["setDataBuffersA"])

        # Create overflow location
        overflow = ctypes.c_int16()
        # create converted type totalSamples
        cTotalSamples = ctypes.c_int32(totalSamples)

        # Retried data from scope to buffers assigned above
        self.status["getValues"] = ps2000a.ps2000aGetValues(self.chandle, 0, ctypes.byref(cTotalSamples), 0, 0, 0,
                                                            ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        # find maximum ADC count value
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps2000a.ps2000aMaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])

        # convert data to lists
        voltage_values = adc2mV(bufferAMax, voltage_range, maxADC)
        time_values = np.linspace(0, (cTotalSamples.value - 1) * timeIntervalns.value, cTotalSamples.value)

        # Stop the scope
        self.status["stop"] = ps2000a.ps2000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        return time_values, voltage_values

    def ready(self):
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps2000a.ps2000aIsReady(self.chandle, ctypes.byref(ready))

    def plot(self, time_values, voltage_values):
        plt.plot(time_values, voltage_values)
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

    def close(self):
        self.status["close"] = ps2000a.ps2000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])


class PicoScope3000a:
    def __init__(self):
        # Gives the device a handle
        self.status = {}
        self.chandle = ctypes.c_int16()

        # Opens the device/s
        self.status["openunit"] = ps3000a.ps3000aOpenUnit(ctypes.byref(self.chandle), None)

        try:
            assert_pico_ok(self.status["openunit"])
        except:
            # powerstate becomes the status number of openunit
            powerstate = self.status["openunit"]

            # If powerstate is the same as 282 then it will run this if statement
            if powerstate == 282:
                # Changes the power input to "PICO_POWER_SUPPLY_NOT_CONNECTED"
                self.status["ChangePowerSource"] = ps3000a.ps3000aChangePowerSource(self.chandle, 282)
            # If the powerstate is the same as 286 then it will run this if statement
            elif powerstate == 286:
                # Changes the power input to "PICO_USB3_0_DEVICE_NON_USB3_0_PORT"
                self.status["ChangePowerSource"] = ps3000a.ps3000aChangePowerSource(self.chandle, 286)
            else:
                raise

            assert_pico_ok(self.status["ChangePowerSource"])

        self.sweeptype = ctypes.c_int32(0)
        self.triggertype = ctypes.c_int32(0)
        self.triggerSource = ctypes.c_int32(0)

    def signal_generator(self, wave, amplitude, frequency, offset=0):
        amplitude = int(amplitude * 1000000)
        self.status["SetSigGenBuiltIn"] = ps3000a.ps3000aSetSigGenBuiltIn(self.chandle, offset, amplitude,
                                                                          wave, frequency, frequency, 0, 1,
                                                                          self.sweeptype, 0, 0, 0,
                                                                          self.triggertype,
                                                                          self.triggerSource, 1)
        return assert_pico_ok(self.status["SetSigGenBuiltIn"])

    def block_capture(self, channel, voltage_range, duration_ms, threshold=0, pre_trigger=0):

        # Convert voltage & threshold values
        adc_bits = 65535
        voltage_range = volt_range_list[voltage_range]
        threshold = round(threshold / (voltage_range / adc_bits))

        # Set up channel A
        self.status["setChA"] = ps3000a.ps3000aSetChannel(self.chandle, channel, 1, 1, voltage_range, 0)
        assert_pico_ok(self.status["setChA"])

        # Set up single trigger
        self.status["trigger"] = ps3000a.ps3000aSetSimpleTrigger(self.chandle, 1, 0, threshold, 0, 0, 0)
        assert_pico_ok(self.status["trigger"])

        # Set number of pre and post trigger samples to be collected

        # Get timebase information
        timebase = 10
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()
        oversample = ctypes.c_int16(0)
        self.status["getTimebase2"] = ps3000a.ps3000aGetTimebase2(self.chandle,
                                                                  timebase,
                                                                  1276,
                                                                  ctypes.byref(timeIntervalns),
                                                                  oversample,
                                                                  ctypes.byref(returnedMaxSamples),
                                                                  0)
        assert_pico_ok(self.status["getTimebase2"])

        # calculate amount of samples to cover duration & add pre trigger (if any)
        print(f'Time Interval: {timeIntervalns.value}')
        samples = round((duration_ms * 1000000) / timeIntervalns.value)
        totalSamples = samples
        preTriggerSamples = samples * pre_trigger
        postTriggerSamples = samples * (100 - pre_trigger)
        print(f'Samples: {samples}')

        # Run block capture
        self.status["runBlock"] = ps3000a.ps3000aRunBlock(self.chandle,
                                                          preTriggerSamples,
                                                          postTriggerSamples,
                                                          timebase,
                                                          oversample,
                                                          None,
                                                          0,
                                                          None,
                                                          None)
        assert_pico_ok(self.status["runBlock"])

        # Check for data collection to finish using ps3000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps3000a.ps3000aIsReady(self.chandle, ctypes.byref(ready))

        # Create buffers ready for assigning pointers for data collection
        bufferAMax = (ctypes.c_int16 * totalSamples)()
        bufferAMin = (ctypes.c_int16 * totalSamples)()

        # Set data buffer location for data collection from channel A
        self.status["setDataBuffersA"] = ps3000a.ps3000aSetDataBuffers(self.chandle,
                                                                       0,
                                                                       ctypes.byref(bufferAMax),
                                                                       ctypes.byref(bufferAMin),
                                                                       totalSamples,
                                                                       0,
                                                                       0)
        assert_pico_ok(self.status["setDataBuffersA"])

        # Create overflow location
        overflow = ctypes.c_int16()
        # create converted type totalSamples
        cTotalSamples = ctypes.c_int32(totalSamples)

        # Retried data from scope to buffers assigned above
        self.status["getValues"] = ps3000a.ps3000aGetValues(self.chandle, 0, ctypes.byref(cTotalSamples), 0, 0, 0,
                                                            ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        # find maximum ADC count value
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps3000a.ps3000aMaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])

        # convert data to lists
        voltage_values = adc2mV(bufferAMax, voltage_range, maxADC)
        time_values = np.linspace(0, (cTotalSamples.value - 1) * timeIntervalns.value, cTotalSamples.value)

        # Stop the scope
        self.status["stop"] = ps3000a.ps3000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        return time_values, voltage_values

    def ready(self):
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps3000a.ps3000aIsReady(self.chandle, ctypes.byref(ready))

    def plot(self, time_values, voltage_values):
        plt.plot(time_values, voltage_values)
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

    def close(self):
        self.status["close"] = ps3000a.ps3000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])
