#!/usr/bin/python

import audiofire
import socket_io
import argparse
import MySQLdb
import subprocess
import json
import jack
import numpy
import time
import math
import sys

argparser = argparse.ArgumentParser(description="TED socket.io server")
argparser.add_argument('-p', type=int, default=35000, help='Port to listen on')
argparser.add_argument('-w', help='Directory of webclient to check svn version')
args = argparser.parse_args()

db = MySQLdb.connect('localhost', 'ted', 'qPueHNCFFv2CVSS6', 'ted')
#cursor = db.cursor(MySQLdb.cursors.DictCursor)
cursor = db.cursor()

jack.attach("ted");       
jack.activate()

def main():
    # TODO: make not global
    global ted 

    ted = TedServer()

    ted.listen(args.p, fork=True)    

    freq = 15
    period = 1.0/freq
    levels = [0 for i in range(len(ted.mixer.inputs))]

    while True:
        time.sleep(period)
        meters = jack.get_input_meters()
        message = []

        i = 0;
        for id, input in ted.mixer.inputs.items():
            peak = None
            for port in input.ports:
                if peak < meters[i]:
                    peak = meters[i]
                i += 1
            #peak += 14 # Uncomment if using consumer-audio volume levels


            if(peak >= -36):
                level = int(math.floor(100 * (peak + 36)/36))
            else:
                level = 0

            if(input.level > 0):
                input.level = max(0, input.level - int(100.0/freq))
            
            if(input.level < level):
                input.level = level
                if level > 0:
                    status = {}
                    status['level'] = level
                    status['e'] = 'i'
                    status['i'] = input.id
                    message.append(status)


        if(len(message) > 0):
            ted.broadcast(json.dumps(message))
        
    


    #N = jack.get_buffer_size()
    #Sr = float(jack.get_sample_rate()
    #channels = 12
    #in_buffer = numpy.zeros((12,N), 'f')
    #out_buffer = numpy.zeros(12,N), 'f')


class InputPort(object):

    def __init__(self, client, name, number):
        self.client = client
        self.name = name
        self.number = number
        self.port = "%s:%s%d" %(self.client, self.name, self.number)
        self.monitor_port = "monitor_%s_%s%d" % (self.client, self.name, self.number)

        jack.register_port(self.monitor_port, jack.IsInput)
        jack.connect(self.port, "%s:%s" % (jack.get_client_name(), self.monitor_port))

    def connected(self, output):
        return output.port in jack.get_connections(self.port)

    def connect(self, output):
        jack.connect(self.port, output.port)

    def disconnect(self, output):
        jack.disconnect(self.port, output.port)


class Input(object):
    def __init__(self, id, name, local_out):
        self.id = id
        self.name = name
        self.local_out = local_out
        self.level = 0

        self.ports = []
        cursor.execute("""
            SELECT jin_client, jin_port_name, jin_port_number
            FROM jack_input
            WHERE jin_input_id = %d
        """  % self.id)
        for row in cursor.fetchall():
            self.ports.append(InputPort(row[0], row[1], row[2]))

        # True only if all ports are audiofire
        self.audiofire = reduce(lambda x, y: x and y, map(lambda x: x.client == 'system', self.ports))
        if(self.audiofire):
            self.af_ports = map(lambda p: p.number-1, self.ports)

    def connected(self, output):
        if self.audiofire and output.audiofire:
            return audiofire.connected(self.af_ports, output.af_ports)
        else:
            return self.ports[0].connected(output.ports[0])

    def connect(self, output):
        if self.audiofire and output.audiofire:
            audiofire.connect(self.af_ports, output.af_ports)
            return

        elif len(self.ports) == len(output.ports):
            for x in range(len(self.ports)):
                self.ports[x].connect(output.ports[x])
        elif len(output.ports) == 1:
            for i in self.ports:
                i.connect(output.ports[0])
        elif len(self.ports) == 1:
            for o in output.ports:
                self.ports[0].connect(o)
        else:
            raise NotImplementedError 

    def disconnect(self, output):
        # TODO: merge connect and disconnect

        if self.audiofire and output.audiofire:
            audiofire.disconnect(self.af_ports, output.af_ports)
            return

        elif len(self.ports) == len(output.ports):
            for x in range(len(self.ports)):
                self.ports[x].disconnect(output.ports[x])
        elif len(output.ports) == 1:
            for i in self.ports:
                i.disconnect(output.ports[0])
        elif len(self.ports) == 1:
            for o in output.ports:
                self.ports[0].disconnect(o)
        else:
            raise NotImplementedError 

class OutputPort(object):

    def __init__(self, client, name, number):
        self.client = client
        self.name = name
        self.number = number
        self.port = "%s:%s%d" %(self.client, self.name, self.number)

class Output(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name 

        self.ports = []
        cursor.execute("""
            SELECT jout_client, jout_port_name, jout_port_number
            FROM jack_output
            WHERE jout_output_id = %d
        """ % self.id)
        for row in cursor.fetchall():
            self.ports.append(OutputPort(row[0], row[1], row[2]))

        # True only if all ports are audiofire
        # TODO: merge code with input
        self.audiofire = reduce(lambda x, y: x and y, map(lambda x: x.client == 'system', self.ports))
        if(self.audiofire):
            self.af_ports = map(lambda p: p.number-1, self.ports)

    def _get_muted(self):
        #if(self.audiofire):
            # TODO: move to audiofire module
        return bool(audiofire.outputs[self.af_ports[0]]['mute'].getValue())

    def _set_muted(self, mute):
        mute = bool(mute)

        if self.muted == mute:
            return

        for port in self.af_ports:
            # TODO: move to audiofire module
            audiofire.outputs[port]['mute'].setValue(int(mute))

        ted.broadcast(json.dumps([self.get_status(['muted'])]))

    muted = property(_get_muted, _set_muted)

    def get_status(self, attrs=None):
        status = {}
        status['e'] = 'output'
        status['o'] = self.id

        if attrs is None or 'muted' in attrs:
            status['muted'] = self.muted

        return status



class Mixer(object):

    def __init__(self):
        self.inputs = {}
        cursor.execute("SELECT in_id, in_name, in_local_out FROM input")
        for row in cursor.fetchall():
            self.inputs[row[0]] = Input(row[0], row[1], row[2]);

        self.outputs = {}
        cursor.execute("SELECT out_id, out_name FROM output")
        for row in cursor.fetchall():
            self.outputs[row[0]] = Output(row[0], row[1]);

        self.matrix = {}
        for i in self.inputs:
            self.matrix[i] = {}
            for o in self.outputs:
                self.matrix[i][o] = MatrixNode(self.inputs[i], self.outputs[o])
    
    def get_status(self):
        status = []
        for i, nodes in self.matrix.items():
            for o, node in nodes.items():
                status.append(node.get_status())
        for o, output in self.outputs.items():
            status.append(output.get_status())

        return status

class MatrixNode(object):

    def __init__(self, i, o):
        self.i = i
        self.o = o

    def _get_muted(self):
        return not self.i.connected(self.o)

    def _set_muted(self, mute):
        mute = bool(mute)

        if self.i.id == 1 and self.o.id == 1:
            # TODO: Something smarter...
            ted.broadcast(json.dumps([self.get_status(['muted'])]))
            return

        if self.muted != mute:
            if mute:
                self.i.disconnect(self.o)
            else:
                self.i.connect(self.o)

        ted.broadcast(json.dumps([self.get_status(['muted'])]));

    muted = property(_get_muted, _set_muted) 


    def get_status(self, attrs=None):
        status = {}
        status['e'] = 'matrix'
        status['i'] = self.i.id
        status['o'] = self.o.id

        if attrs is None or 'muted' in attrs:
            status['muted'] = self.muted

        return status
"""
class MixerOutput(object):
    def __init__(self, o, outs):
        self._o = o
        self.outputs = []
        for o in outs:
            self.outputs.append(dbus.Interface(bus.get_object(dest, "%s/OUT%dMute" % (mixer_object, o)),
                    dbus_interface=discrete_interface))
    def _get_muted(self):
        return bool(self.outputs[0].getValue())

    def _set_muted(self, mute):
        mute = bool(mute)

        if self.muted == mute:
            return

        for output in self.outputs:
            output.setValue(int(mute))

        ted.broadcast(json.dumps([self.get_status(['muted'])]))

    muted = property(_get_muted, _set_muted)

    def get_status(self, attrs=None):
        status = {}
        status['e'] = 'output'
        status['o'] = self._o

        if attrs is None or 'muted' in attrs:
            status['muted'] = self.muted

        return status
"""
class TedServer(socket_io.Server):

    def __init__(self):
        socket_io.Server.__init__(self)
        self.mixer = Mixer()

    def on_connect(self, client):
        print client, 'connected'
        if(args.w):
            message = {};
            message['e'] = 'version';
            message['version'] = subprocess.check_output(['svnversion', args.w]).strip()
            client.send(json.dumps([message]))
        client.send(json.dumps(self.mixer.get_status()))

    def on_disconnect(self, client):
        print client, 'disconnected'

    def on_message(self, client, message):
        print client, "sent", message
        command = json.loads(message)

        if command['command'] == 'element':
            if command['element'] == 'output':
                element = self.mixer.outputs[command['o']]
            elif command['element'] == 'matrix':
                element = self.mixer.matrix[command['i']][command['o']]
            
            setattr(element, command['attr'], command['value'])
        elif command['command'] == 'macro':
            if command['element'] == 'input':
                if command['macro'] == 'all':
                    for key, node in self.mixer.matrix[command['i']].items():
                        node.muted = False
                elif command['macro'] == 'solo':
                    for key, col in self.mixer.matrix.items():
                        if col is self.mixer.matrix[command['i']]:
                            mute = False
                        else:
                            mute = True
                        for key, node in col.items():
                            node.muted = mute
                elif command['macro'] == 'local':
                    for key, node in self.mixer.matrix[command['i']].items():
                        if node is self.mixer.matrix[command['i']][command['o']]:
                            node.muted = False
                        else:
                            node.muted = True
                elif command['macro'] == 'off':
                    for key, node in self.mixer.matrix[command['i']].items():
                        node.muted = True
            elif command['element'] == 'output':
                for key, col in self.mixer.matrix.items():
                    col[command['o']].muted = key != int(command['macro'])
            elif command['element'] == 'general':
                for key, output in self.mixer.outputs.items():
                    if command['macro'] == 'all-on':
                        output.muted = False
                    elif command['macro'] == 'mute-all':
                        output.muted = True

if __name__ == "__main__":
    main()
    db.close()
