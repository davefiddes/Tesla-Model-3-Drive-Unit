# Saleae Logic High Level Analyzer for Tesla Model 3/Y oil pump LIN bus

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame

# The list of expected LIN PIDs supported by the oil pump
SPEED_REQUEST = 0x0A
STATUS1_RESPONSE = 0x2A
STATUS2_RESPONSE = 0x32
STATUS3_RESPONSE = 0x30
STATUS4_RESPONSE = 0x31


def convert_temp(temp: int) -> int:
    '''Convert an oil pump temperature from a raw byte to an degrees Celsius'''
    return temp - 40


class oil_pump_analyzer(HighLevelAnalyzer):
    '''
    Analyze LIN frames sent to and from a Tesla Model 3/Y oil pump
    '''

    result_types = {
        'error': {
            'format': 'Unknown PID: {{data.pid}}'
        },
        'request': {
            'format': 'Request speed: {{data.speed}}'
        },
        'status1': {
            'format': 'Status1 Flow: {{data.flow}} Pressure: {{data.pressure}} Fluid temp: {{data.fluid_temp}} Pump temp: {{data.pump_temp}}'
        },
        'status2': {
            'format': 'Status2'
        },
        'status3': {
            'format': 'Status3 Voltage: {{data.voltage}} Motor RPM: {{data.motor_rpm}}'
        },
        'status4': {
            'format': 'Status4 Current: {{data.current}} Temp3: {{data.temp3}} Temp4: {{data.temp4}} Temp5: {{data.temp5}} Temp6: {{data.temp6}}'
        }
    }

    def __init__(self):
        '''
        Initialize the analyzer state machine
        '''
        self.start_time = None
        self.pid = None
        self.data = []

    def decode(self, frame: AnalyzerFrame):
        '''
        Process a frame from the LIN input analyzer. We use the header_break to
        indicate the start of a frame before pulling out the PID and data
        bytes. When a checksum or data_or_checksum frame is seen we assume the
        frame is complete and can decode it.
        '''

        if frame.type == 'header_break':
            self.start_time = frame.start_time
            self.pid = None
            self.data = []
            return

        if frame.type == 'header_pid':
            self.pid = frame.data['protected_id']
            return

        if frame.type == 'data':
            self.data.append(frame.data['data'])
            return

        if frame.type in ('checksum', 'data_or_checksum'):
            if self.start_time:
                start_time = self.start_time
                self.start_time = None
            else:
                start_time = frame.start_time
            end_time = frame.end_time

            if self.pid == SPEED_REQUEST:
                if len(self.data) == 2:
                    speed = self.data[1]
                else:
                    speed = 'invalid'
                return AnalyzerFrame('request', start_time, end_time, {
                    'speed': speed
                })

            if self.pid == STATUS1_RESPONSE:
                if len(self.data) == 8:
                    data = {'flow': self.data[1],
                            'pressure': self.data[2],
                            'fluid_temp': convert_temp(self.data[3]),
                            'pump_temp': convert_temp(self.data[5])
                            }
                else:
                    data = {}
                return AnalyzerFrame('status1', start_time, end_time, data)

            if self.pid == STATUS2_RESPONSE:
                # Nothing is known about the contents of this message
                return AnalyzerFrame('status2', start_time, end_time)

            if self.pid == STATUS3_RESPONSE:
                if len(self.data) == 8:
                    motor_rpm = self.data[4] | (self.data[5] << 8)
                    data = {
                        'voltage': f"{self.data[0] * 0.1:.1f}",
                        'motor_rpm': motor_rpm
                    }
                else:
                    data = {}
                return AnalyzerFrame('status3', start_time, end_time, data)

            if self.pid == STATUS4_RESPONSE:
                if len(self.data) == 8:
                    data = {
                        'current': self.data[1],
                        'temp3': convert_temp(self.data[3]),
                        'temp4': convert_temp(self.data[4]),
                        'temp5': convert_temp(self.data[5]),
                        'temp6': convert_temp(self.data[6])
                    }
                else:
                    data = {}
                return AnalyzerFrame('status4', start_time, end_time, data)

            return AnalyzerFrame('error', start_time, end_time, {
                'pid': self.pid
            })
