from ctypes import CDLL, POINTER, c_int, c_char_p, create_string_buffer

lib = CDLL('./generator_lib.dll')

StrBuild = lib.StrBuild
StrBuild.restype = POINTER(POINTER(POINTER(c_int)))
StrBuild.argtypes = [c_char_p]

setPb = lib.setPb
setPb.restype = c_int
setPb.argtypes = [POINTER(POINTER(POINTER(c_int))), c_int, c_int, c_int]

pdPWM = lib.pb_PWM
pdPWM.restype = c_int
pdPWM.argtypes = [c_int, POINTER(POINTER(c_int)), c_int]


def _config_builder(num_channels, channel_numbers, impulse_counts, start_times, stop_times):
    result = [str(num_channels)]

    start_index = 0
    stop_index = 0

    for i in range(num_channels):
        channel = channel_numbers[i]
        num_impulses = impulse_counts[i]

        channel_start_times = start_times[start_index:start_index + num_impulses]
        channel_stop_times = stop_times[stop_index:stop_index + num_impulses]

        start_index += num_impulses
        stop_index += num_impulses

        result.append(f'_{channel}_{num_impulses}')
        result.extend(f'_{time}' for time in channel_start_times + channel_stop_times)

    return ''.join(result)


# result_str = _config_builder(2, [0, 1], [2, 3], [0, 350, 0, 200, 350], [150, 400, 150, 300, 400])

# t = result_str.encode('utf-8')

# print(t)


def impulse_builder(num_channels: int, channel_numbers: list[int], impulse_counts: list[int], start_times: list[int],
                    stop_times: list[int], repeat_time, pulse_scale, rep_scale):
    setPb(StrBuild(create_string_buffer(
        _config_builder(num_channels, channel_numbers, impulse_counts, start_times, stop_times).encode("utf-8"))), repeat_time, pulse_scale,
        rep_scale)


impulse_builder(1, [0], [1], [0], [10], 10,1,1)
