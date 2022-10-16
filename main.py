import pypico
import numpy as np
import matplotlib.pyplot as plt

start_frequency = 100
end_frequency = 20000
log_steps = 500

freq_axis = 'log'  # 'log' or 'linear'


def main():
    # generate frequency list
    frequency_list = np.geomspace(start_frequency, end_frequency, log_steps)

    # startup PicoScope
    ps = pypico.get_picoscope()

    # Create data list
    amplitude = []

    # Step through frequencies
    for frequency in frequency_list:
        ps.signal_generator(pypico.sine, 0.9, frequency)
        duration = (1 / frequency) * 2000
        time_values, voltage_values, samples, interval_ns = ps.block_capture(pypico.channel_A,
                                                                             voltage_range=0.5,
                                                                             duration_ms=duration,
                                                                             threshold=0.2,
                                                                             return_timebase=True)
        v_max = max(voltage_values)
        v_min = min(voltage_values)
        v_amplitude = v_max - v_min
        print(f'Frequency: {round(frequency, 2)}, ' +
              f'Duration: {round(duration, 4)}, ' +
              f'Samples: {samples}, ' +
              f'Interval: {interval_ns} ns, ' +
              f'Amplitude: {round(v_amplitude, 2)}')
        amplitude.append(v_amplitude)

    # Plot Data
    plt.plot(frequency_list, amplitude)
    plt.title('PicoResponse')
    plt.xlabel('Frequency')
    plt.xscale(freq_axis)
    plt.xlim([start_frequency, end_frequency])
    plt.ylabel('Amplitude (mV)')
    plt.ylim([0, 1200])
    plt.show()

    ps.close()


if __name__ == '__main__':
    main()
