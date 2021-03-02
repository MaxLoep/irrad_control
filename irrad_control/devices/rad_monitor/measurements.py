import csv
import time
import numpy as np
import os


def _check_file_exists(file):

    if os.path.isfile(file):
        raise ValueError("File {} already exists".format(file))


def calibrate_via_r2(outfile, arduino_counter, n_measures_per_step=5, calibrate='counts'):

    _check_file_exists(outfile)

    with open(outfile, 'w') as f:

        f.write("# Arduino counter with sampling time of {} ms\n".format(arduino_counter.get_samplingtime()))
        f.write("# Measuring 1/r^2-relation via {}\n".format(calibrate))
        f.write("# Sampling each measurement {} times\n".format(n_measures_per_step))
        f.write("# Measurement start: {}\n\n".format(time.asctime()))

        writer = csv.writer(f)

        writer.writerow(["# Timestamp / s", "Distance / cm", "mean {}".format(calibrate), "std {}".format(calibrate), "dose rate / uSv/h"])

        read_func = arduino_counter.get_frequency if calibrate != 'counts' else arduino_counter.get_counts

        input_msg = "Enter distance step in cm. Press 'q' to quit"
        step = None

        while step != 'q':

            step = input(input_msg)

            print('Measuring {} for distance {} cm. Mean over {} measurements'.format(calibrate, step, n_measures_per_step))

            data = []

            for _ in range(n_measures_per_step):

                m = read_func()
                print("Measured {}: {}".format(calibrate, m))
                data.append(m)

            dose_rate = input("Corresponding dose rate in uSv/h")

            writer.writerow([time.time(), step, np.mean(data), np.std(data), dose_rate])


def calibrate_source_center(outfile, arduino_counter, xy_stage, square=3, res=10, n_measures_per_step=5, calibrate='counts'):

    _check_file_exists(outfile)

    with open(outfile, 'w') as f:

        f.write("# Arduino counter with sampling time of {} ms\n".format(arduino_counter.get_samplingtime()))
        f.write("# Measuring source center via {}\n".format(calibrate))
        f.write("# Measure square +- {} cm around starting point\n".format(square))
        f.write("# Splitting square in {} equidistant steps in each dimension\n".format(res))
        f.write("# Sampling each measurement {} times\n".format(n_measures_per_step))
        f.write("# Measurement start: {}\n\n".format(time.asctime()))

        writer = csv.writer(f)

        writer.writerow(["# Timestamp / s", "rel x / cm", "rel y / cm", "mean {}".format(calibrate), "std {}".format(calibrate)])

        read_func = arduino_counter.get_frequency if calibrate != 'counts' else arduino_counter.get_counts
        
        ref_pos = xy_stage.get_position(unit='cm')
        ref_pos = [30.0 - ref_pos[0], 30.0 - ref_pos[1]]
        
        rel_measure_points = np.linspace(-square, square, res)

        for y in rel_measure_points:

            xy_stage.move_absolute(target=ref_pos[1] + y, axis=xy_stage.y_axis, unit='cm')

            for x in rel_measure_points:

                xy_stage.move_absolute(target=ref_pos[0] + x, axis=xy_stage.x_axis, unit='cm')

                data = []

                print("Measuring at rel. to counter (x={}, y={}) cm".format(x, y))

                for _ in range(n_measures_per_step):
                    m = read_func()
                    print("Measured {}: {}".format(calibrate, m))
                    data.append(m)

                writer.writerow([time.time(), x, y, np.mean(data), np.std(data)])


def measure_continuously(outfile, arduino_counter, n_measures_per_step=5, measure='counts'):

    _check_file_exists(outfile)

    with open(outfile, 'w') as f:

        f.write("# Arduino counter with sampling time of {} ms\n".format(arduino_counter.get_samplingtime()))
        f.write("# Measuring {} continuously\n".format(measure))
        f.write("# Sampling each measurement {} times\n".format(n_measures_per_step))
        f.write("# Measurement start: {}\n\n".format(time.asctime()))

        writer = csv.writer(f)

        writer.writerow(["# Timestamp / s", "mean {}".format(measure), "std {}".format(measure)])

        read_func = arduino_counter.get_frequency if measure != 'counts' else arduino_counter.get_counts

        try:
            while True:

                data = []

                for _ in range(n_measures_per_step):
                    m = read_func()
                    print("Measured {}: {}".format(measure, m))
                    data.append(m)

                writer.writerow([time.time(), np.mean(data), np.std(data)])

        except KeyboardInterrupt:
            pass
