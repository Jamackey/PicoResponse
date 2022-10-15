import pypico
import numpy as np
import matplotlib.pyplot as plt

start_frequency = 100
end_frequency = 20000
log_steps = 1000


def main():
    # generate frequency list
    frequency_list = np.geomspace(start_frequency, end_frequency, log_steps)

    # startup PicoScope
    init_ps = pypico.PicoScope()
    ps = init_ps.ps

    # Create data list
    amplitude = []

    # Step through frequencies
    for frequency in frequency_list:
        print(f'Frequency: {frequency}')
        ps.signal_generator(pypico.sine, 0.9, frequency)
        duration = (1 / frequency) * 2000
        print(f'Duration: {duration}')
        time_values, voltage_values = ps.block_capture(pypico.channel_A,
                                                       voltage_range=0.5,
                                                       duration_ms=duration,
                                                       threshold=0.2)
        v_max = max(voltage_values)
        v_min = min(voltage_values)
        v_amplitude = v_max - v_min
        print(f'Amplitude: {v_amplitude}')
        # ps.plot(time_values, voltage_values)
        amplitude.append(v_amplitude)

    # Plot Data
    plt.plot(frequency_list, amplitude)
    plt.xlabel('Frequency')
    plt.xscale('log')
    plt.ylabel('Amplitude (mV)')
    plt.ylim([0, 1200])
    plt.show()

    ps.close()


if __name__ == '__main__':
    main()
