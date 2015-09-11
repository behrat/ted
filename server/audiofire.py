import dbus
import time
import subprocess

bus = dbus.SessionBus()
dest = 'org.ffado.Control'
mixer_object = '/org/ffado/Control/DeviceManager/001486089d5fa7e6/Mixer'
discrete_interface='org.ffado.Control.Element.Discrete'
continuous_interface='org.ffado.Control.Element.Continuous'
mixer_interface='org.ffado.Control.Element.MatrixMixer'

try:
   dbus.Interface(bus.get_object(dest, "%s/MonitorMute" % mixer_object),
                dbus_interface=mixer_interface)
except dbus.DBusException, ex:
    subprocess.Popen(['ffado-dbus-server', '-v3']).pid
    time.sleep(2)



monitor_mute = dbus.Interface(
   bus.get_object(dest, "%s/MonitorMute" % mixer_object),
   dbus_interface=mixer_interface)
monitor_pan = dbus.Interface(
   bus.get_object(dest, "%s/MonitorPan" % mixer_object),
   dbus_interface=mixer_interface)


outputs = [];
for o in range(12):
    output = {}
    output['mute'] = dbus.Interface(
            bus.get_object(dest, "%s/OUT%dMute" % (mixer_object, o)),
            dbus_interface=discrete_interface)
    output['gain'] = dbus.Interface(
            bus.get_object(dest, "%s/OUT%dGain" % (mixer_object, o)),
            dbus_interface=continuous_interface)
    outputs.append(output)

def set_mute(ins, outs, mute):

    if len(outs) == 2:
        if len(ins) == 1:
            ins.append(ins[0])

        for x in range(2):
            monitor_mute.setValue(ins[x], outs[x], int(mute))

    elif len(outs) == 1:

        pan = monitor_pan.getValue(ins[0], outs[0])
        is_left = outs[0] % 2 == 0

        if mute == is_left:
            # (mute and left) or not (mute or left)
            pan += 127
        else:
            pan -= 127

        if pan == 254:
            pan += 1;
        elif pan == 128:
            pan -= 1;

        for x in range(len(ins)):
            monitor_pan.setValue(ins[x], outs[0], pan)

        if mute == bool(pan == 127):
            for x in range(len(ins)):
                monitor_mute.setValue(ins[x], outs[0], mute)

def connect(ins, outs):
    if connected(ins, outs):
        return

    set_mute(ins, outs, False)

def disconnect(ins, outs):
    if not connected(ins, outs):
        return

    set_mute(ins, outs, True)

def connected(ins, outs):
    assert 0 < len(ins) <= 2
    assert 0 < len(outs) <= 2

    if bool(monitor_mute.getValue(ins[0], outs[0])):
        # it's muted
        return False

    if len(outs) == 2:
        return True

    return monitor_pan.getValue(ins[0], outs[0]) != (1 - (outs[0] % 2)) * 255



