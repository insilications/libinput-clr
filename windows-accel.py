#!/usr/bin/env python
# calculation are based on http://www.esreality.com/index.php?a=post&id=1945096
# assuming windows 10 uses the same calculation as windows 7.
# guesses have been made calculation is not accurate
# touchpad users make sure your touchpad is calibrated with `sudo libinput measure touchpad-size`
import matplotlib.pyplot as plt
import struct

# set according to your device:
xinput_device_id = 11
# device_dpi = 2100 # mouse dpi
device_dpi = 2100 # mouse dpi
screen_dpi = 384
screen_scaling_factor = 1
sample_point_count = 32 # should be enough but you can try to increase for accuracy of windows function
sensitivity_factor = 10.0
# sensitivity factor translation table: (windows slider notches)
# 1 = 0.1
# 2 = 0.2
# 3 = 0.4
# 4 = 0.6
# 5 = 0.8
# 6 = 1.0 default
# 7 = 1.2
# 8 = 1.4
# 9 = 1.6
# 10 = 1.8
# 11 = 2.0

# sudo libinput debug-gui --verbose --set-profile=custom --set-custom-points="0.000;0.142;1.230;2.460;3.689;5.327;7.177;9.027;10.877;12.727;14.577;16.701;19.511;22.321;25.131;27.941;30.751;33.561;36.371;39.181;41.991;44.801;47.611;50.421;53.231;56.041;58.851;61.661;64.471;67.281;70.091;72.901" --set-custom-step=0.1428571428 --set-custom-type=scroll

# xinput set-prop 11 "libinput Accel Custom Scroll Points" 0.000, 0.142857, 1.230, 2.460, 3.689, 5.327, 7.177, 9.027, 10.877, 12.727, 14.577, 16.701, 19.511, 22.321, 25.131, 27.941, 30.751, 33.561, 36.371, 39.181, 41.991, 44.801, 47.611, 50.421, 53.231, 56.041, 58.851, 61.661, 64.471, 67.281, 70.091, 72.901
# xinput set-prop 11 "libinput Accel Custom Scroll Step" 0.142857
# xinput set-prop 11 "libinput Accel Profile Enabled" 0, 0, 1

# TODO: find accurate formulas for scale x and scale y
# mouse speed: inch/s to device-units/millisecond
scale_x = device_dpi / 1e3
# pointer speed: inch/s to screen pixels/millisecond
scale_y =  screen_dpi / 1e3 / screen_scaling_factor * sensitivity_factor

print(f'scale_x={scale_x}, scale_y={scale_y}')
# scale_x = scale_x * 120
# scale_y = scale_y * 120
print(f'scale_x2={scale_x}, scale_y2={scale_y}')


def float16x16(num):
    return struct.unpack('<i', num[:-4])[0] / int(0xffff)

# windows 10 registry values:
# HKEY_CURRENT_USER\Control Panel\Mouse\SmoothMouseXCurve
X = [
b'\x00\x00\x00\x00\x00\x00\x00\x00',
b'\x15\x6e\x00\x00\x00\x00\x00\x00',
b'\x00\x40\x01\x00\x00\x00\x00\x00',
b'\x29\xdc\x03\x00\x00\x00\x00\x00',
b'\x00\x00\x28\x00\x00\x00\x00\x00',
]
# HKEY_CURRENT_USER\Control Panel\Mouse\SmoothMouseYCurve
Y=[
b'\x00\x00\x00\x00\x00\x00\x00\x00',
b'\xfd\x11\x01\x00\x00\x00\x00\x00',
b'\x00\x24\x04\x00\x00\x00\x00\x00',
b'\x00\xfc\x12\x00\x00\x00\x00\x00',
b'\x00\xc0\xbb\x01\x00\x00\x00\x00',
]

windows_points = [[float16x16(x), float16x16(y)] for x,y in zip(X,Y)]
# windows_points[1][1] = windows_points[1][0]
# print(windows_points[1][1])
print('\n\nWindows original points:')
for point in windows_points:
    print(point)

# scale windows points according to device config
points = [[x * scale_x, y * scale_y] for x, y in windows_points]
# points[1][1] = points[1][0]
# print(points[1][1])
print('\n\nWindows scaled points')
for point in points:
    print(point)
print(f"\n")
print(f"\n")

# fig1, ax1 = plt.subplots()
# ax1.plot(*list(zip(*windows_points)), label=f'windows points')
# ax1.plot(*list(zip(*points)), label=f'scaled points')
# ax1.set_xlabel('device-speed')
# ax1.set_ylabel('pointer-speed')
# ax1.legend(loc='best')
# fig1.savefig("points1.png", bbox_inches='tight')
# # plt.show()
# # fig1.savefig("points1.png")
# plt.close()

def find2points(x):
    i = 0
    while i < len(points) - 2 and x >= points[i+1][0]:
        i +=1
    assert -1e6 + points[i][0] <= x <= points[i+1][0]+1e6, f'{points[i][0]} <= {x} <= {points[i+1][0]}'
    return points[i], points[i+1]


def interpolate(x):
    (x0, y0), (x1, y1) = find2points(x)
    y = ((x-x0)*y1+(x1-x)*y0)/(x1-x0)
    return y


def sample_points(count):
    # use linear extrapolation for last point to get better accuracy for lower points
    last_point = -2
    max_x = points[last_point][0]
    step = max_x / (count + last_point) # we need another point for 0
    sample_points_x = [si * step for si in range(count)]
    # sample_points_x = [(si * step * 120) for si in range(count)]
    # sample_points_y = [(interpolate(x)) for x in sample_points_x]
    sample_points_y = [interpolate(x) for x in sample_points_x]
    sample_points_x = [ x for x in sample_points_x ]
    # sample_points_x = [ x + 6 for x in sample_points_x ]
    # sample_points_x[0] = 0.0
    # sample_points_y = [ x + 6 for x in sample_points_y ]
    sample_points_y = [ x for x in sample_points_y ]
    # sample_points_y[0] = 0.0
    return sample_points_x, sample_points_y


sample_points_x, sample_points_y = sample_points(sample_point_count)
# sample_points_x = [0, 5.00986, 8.573373007, 9.86005951, 11.14674601, 12.43343252, 13.72011902, 15.00680552, 16.29349203, 17.58017853, 18.86686503, 20.15355154, 21.44023804, 22.72692454, 24.01361105, 25.30029755, 26.58698405, 27.87367056, 29.16035706, 30.44704356, 31.73373007, 33.02041657, 34.30710307, 35.59378958, 36.88047608, 38.16716258, 39.45384909, 40.74053559, 42.0272221, 43.3139086, 44.6005951, 45.88728161]
# sample_points_y = [0, 8.459515245, 10.91903049, 13.37854574, 16.65432796, 20.35442719, 24.05452642, 27.75462565, 31.45472488, 35.15482411, 39.40205075, 45.02205945, 50.64206815, 56.26207686, 61.88208556, 67.50209426, 73.12210296, 78.74211166, 84.36212036, 89.98212906, 95.60213776, 101.2221465, 106.8421552, 112.4621639, 118.0821726, 123.7021813, 129.32219, 134.9421987, 140.5622074, 146.1822161, 151.8022248, 163.4165822]
# sample_points_x[1] = 0.25
# step = sample_points_x[1] - sample_points_x[0]
# sample_points_y[1] = step

step = 0.25
for i in range(sample_point_count):
    sample_points_x[i] = i*step
sample_points_y[1] = step

sample_points_y = [0, 0.25, 2.5, 4, 5.5, 7.5, 9, 11, 14, 16, 18, 21, 24, 26, 28, 32, 35, 37, 39, 42, 45, 48, 52, 54, 57, 60, 62, 65, 68, 70, 74, 82]
# fig2, ax2 = plt.subplots()
# ax2.plot(sample_points_x, sample_points_y, label=f'windows {sample_point_count} points')
# ax2.plot(*sample_points(1024), label=f'windows 1024 points')
# ax2.set_xlabel('device-speed')
# ax2.set_ylabel('pointer-speed')
# ax2.legend(loc='best')
# # fig2.savefig("points2.png")
# fig2.savefig("points2.png", bbox_inches='tight')
# # plt.show()
# plt.close()

sample_points_str = ";".join(["%.3f" % number for number in sample_points_y])
sample_points_y_str = ", ".join(["%.3f" % number for number in sample_points_y])
sample_points_x_str = ";".join(["%.3f" % number for number in sample_points_x])

print(f"\n")
print(f"libinput custom-step: {step}")
print(f"libinput custom-points y ({sample_point_count}):")
print("\t", sample_points_str)
print(f"libinput custom-points x ({sample_point_count}):")
print("\t", sample_points_x_str)
print(f"\n")
for x, y in zip(sample_points_x, sample_points_y):
    print(f'[{x}, {y}]')

print(f"\n")
print(f"\n")
for x in sample_points_x:
    print(f'{x:0.3f}')
print(f"\n")
for y in sample_points_y:
    print(f'{y:0.3f}')
print(f"\n")

print(f"\n")
first_motion_time_interval = (1/step) * 1000
print(f"\t\tsize_t npoints = {sample_point_count};")
print(f"\t\tdouble step = {step:0.10f};")
print(f"\t\tdouble first_motion_time_interval = {first_motion_time_interval:0.0f};")
print(f"\t\tdouble points[{sample_point_count}] = {{{sample_points_y_str}}};")
# print(f"\n")
print(f"\n")
print("libinput test:")
print("\t", f"sudo libinput debug-gui --verbose --set-profile=custom --set-custom-points=\"{sample_points_str}\" --set-custom-step={step:0.10f} --set-custom-type=scroll")
print("\t", f"sudo libinput debug-events --verbose --set-profile=custom --set-custom-points=\"{sample_points_str}\" --set-custom-step={step:0.10f} --set-custom-type=scroll")

# | grep -P '(normalized.y|raw.y)
# print("\t", f"sudo libinput debug-gui --verbose --set-profile=custom --set-custom-points=\"0.0;9.0;36.0;81.0;144.0;225.0;324.0;441.0;576.0;729.0;900.0;1089.0;1296.0;1521.0;1764.0;2025.0\" --set-custom-step=3.0 --set-custom-type=scroll | grep -P '(normalized.y|raw.y)'")

print('\nxinput set-props commands:')
# print(f'\txinput set-prop {xinput_device_id} "libinput Accel Custom Motion Points" {sample_points_str.replace(";", ", ")}')
# print(f'\txinput set-prop {xinput_device_id} "libinput Accel Custom Motion Step" {step:0.10f}')
# print(f'\txinput set-prop {xinput_device_id} "libinput Accel Custom Fallback Points" {sample_points_str.replace(";", ", ")}')
# print(f'\txinput set-prop {xinput_device_id} "libinput Accel Custom Fallback Step" {step:0.10f}')
print(f'\txinput set-prop {xinput_device_id} "libinput Accel Custom Scroll Points" {sample_points_str.replace(";", ", ")}')
print(f'\txinput set-prop {xinput_device_id} "libinput Accel Custom Scroll Step" {step:0.10f}')
print(f'\txinput set-prop {xinput_device_id} "libinput Accel Profile Enabled" 0, 0, 1')
# # xinput set-prop 9 "libinput Scroll Method Enabled" 0, 0, 1
# # xinput set-prop 9 "libinput Scrolling Pixel Distance" 1
# # xinput set-prop 9 "libinput High Resolution Wheel Scroll Enabled" 0
# # xinput set-prop 11 "libinput Accel Custom Scroll Points" 1.0, 3.0, 4.5, 4.5
# # xinput set-prop 11 "libinput Accel Custom Scroll Step" 2.5
# print('\nxinput libinput.conf Options:')
# print('\tOption "AccelProfile" "custom"')
# print(f'\tOption "AccelPointsMotion" "{sample_points_str.replace(";", " ")}"')
# print(f'\tOption "AccelStepMotion" "{step:0.10f}"')
# print(f'\tOption "AccelPointsFallback" "{sample_points_str.replace(";", " ")}"')
# print(f'\tOption "AccelStepFallback" "{step:0.10f}"')
# print(f'\tOption "AccelPointsScroll" "{sample_points_str.replace(";", " ")}"')
# print(f'\tOption "AccelStepScroll" "{step:0.10f}"')
