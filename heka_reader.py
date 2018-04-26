import numpy as np
import os

# Data types list, in order specified by the HEKA file header v2.0.
# Using big-endian.
# Code 0=uint8,1=uint16,2=uint32,3=int8,4=int16,5=int32,
#    6=single,7=double,8=string64,9=string512
ENCODINGS = [np.dtype('>u1'), np.dtype('>u2'), np.dtype('>u4'),
             np.dtype('>i1'), np.dtype('>i2'), np.dtype('>i4'),
             np.dtype('>f4'), np.dtype('>f8'), np.dtype('>S64'),
             np.dtype('>S512'), np.dtype('<u2')]

def get_param_list_byte_length(param_list):
    """
    Returns the length in bytes of the sum of all the parameters in the list.
    Here, list[i][0] = param, list[i][1] = np.dtype
    """
    size = 0
    for i in param_list:
        size += i[1].itemsize
    return size

class HekaReader:
    def __init__(self, filename):
        self.heka_file = open(filename, 'rb')
        # Check that the first line is as expected
        line = self.heka_file.readline()
        if not bytes('Nanopore Experiment Data File V2.0', 'utf-8') in line:
            self.heka_file.close()
            raise IOError('Heka data file format not recognized.')
        # Just skip over the file header text, should be always the same.
        while True:
            line = self.heka_file.readline()
            if bytes('End of file format', 'utf-8') in line:
                break

        # So now heka_file should be at the binary data.

        # # Read binary header parameter lists
        self.per_file_param_list = self.read_heka_header_param_list(np.dtype('>S64'))
        self.per_block_param_list = self.read_heka_header_param_list(np.dtype('>S64'))
        self.per_channel_param_list = self.read_heka_header_param_list(np.dtype('>S64'))
        self.channel_list = self.read_heka_header_param_list(np.dtype('>S512'))

        # # Read per_file parameters
        self.per_file_params = self.read_heka_header_params(self.per_file_param_list)

        # # Calculate sizes of blocks, channels, etc
        self.per_file_header_length = self.heka_file.tell()

        # Calculate the block lengths
        self.per_channel_per_block_length = get_param_list_byte_length(self.per_channel_param_list)
        self.per_block_length = get_param_list_byte_length(self.per_block_param_list)

        self.channel_list_number = len(self.channel_list)

        self.header_bytes_per_block = self.per_channel_per_block_length * self.channel_list_number
        self.data_bytes_per_block = self.per_file_params[bytes('Points per block', 'utf-8')] * 2 * self.channel_list_number
        self.total_bytes_per_block = self.header_bytes_per_block + self.data_bytes_per_block + self.per_block_length

        # Calculate number of points per channel
        self.file_size = os.path.getsize(filename)
        self.num_blocks_in_file = int((self.file_size - self.per_file_header_length) / self.total_bytes_per_block)
        remainder = (self.file_size - self.per_file_header_length) % self.total_bytes_per_block
        if not remainder == 0:
            self.heka_file.close()
            raise IOError('Heka file ends with incomplete block')
        self.block_size = self.per_file_params[bytes('Points per block', 'utf-8')]
        self.points_per_channel_total = self.block_size * self.num_blocks_in_file

        self.sample_rate = 1.0 / self.per_file_params[bytes('Sampling interval', 'utf-8')]

    def close_file(self):
        self.heka_file.close()
    
    def extract_data(self, start = 0, stop = 0, decimate = False, dec_rate = 2500):
        all_data = self.get_all_data(decimate = decimate)
        data = all_data[0][0]
        voltages = all_data[1][0]
        sample_rate = self.get_sample_rate()
        total_length = len(data)
    
        start_len = int(start*sample_rate)
        stop_len = int(stop*sample_rate)
    
        if decimate:
            start_len = int(start_len/dec_rate)
            stop_len = int(stop_len/dec_rate)
    
        if stop == 0:
            stop_len = total_length
            stop = int(stop_len/sample_rate*1.0)
            if decimate:
                stop = int(stop_len*dec_rate/sample_rate*1.0)
    
        length = stop_len - start_len
    
        i = data[start_len:stop_len]
        t = np.linspace(0, (stop-start), num = length)
        v = voltages[start_len:stop_len]
    
        return np.asarray([i, t, sample_rate, v, total_length])
    
    def get_sample_rate(self):
        return self.sample_rate
    
    def get_all_data(self, decimate = False):
        """
        Reads files created by the Heka acquisition software and returns the data.
        :returns: List of numpy arrays, one for each channel of data.
        """
        # return to the start of the file
        self.heka_file.seek(self.per_file_header_length)

        data = []
        for _ in self.channel_list:
            if decimate:  # If decimating, just keep max and min value from each block
                data.append(np.empty(self.num_blocks_in_file * 2))
            else:
                data.append(np.empty(self.points_per_channel_total))  # initialize_c array

        for i in range(0, self.num_blocks_in_file):
            block = self.read_heka_next_block()
            for j in range(len(block)):
                if decimate:  # if decimating data, only keep max and min of each block
                    data[j][2 * i] = np.max(block[j])
                    data[j][2 * i + 1] = np.min(block[j])
                else:
                    data[j][i * self.block_size:(i + 1) * self.block_size] = block[j]

        # if decimate:
        #     self.decimate_sample_rate = self.sample_rate * 2 / self.points_per_channel_per_block  # we are downsampling
        voltages = self.get_all_voltages(decimate = decimate)

        return [data, voltages]

    def get_all_voltages(self, decimate = False):
        """
        Returns a time series of the voltage
        """
        # return to the start of the file
        self.heka_file.seek(self.per_file_header_length)

        data = []
        for _ in self.channel_list:
            if decimate:  # If decimating, just keep max and min value from each block
                data.append(np.empty(self.num_blocks_in_file * 2))
            else:
                data.append(np.empty(self.points_per_channel_total))  # initialize_c array

        for i in range(0, self.num_blocks_in_file):
            block = self.read_heka_next_block_voltages()
            for j in range(len(block)):
                if decimate:  # if decimating data, only keep max and min of each block
                    data[j][2 * i] = np.max(block[j])
                    data[j][2 * i + 1] = np.min(block[j])
                else:
                    data[j][i * self.block_size:(i + 1) * self.block_size] = block[j]

        # if decimate:
        #     self.decimate_sample_rate = self.sample_rate * 2 / self.points_per_channel_per_block  # we are downsampling

        return data

    def get_next_blocks(self, n_blocks=1):
        """
        Get the next n blocks of data.
        :param int n_blocks: Number of blocks to grab.
        :returns: List of numpy arrays, one for each channel.
        """
        blocks = []
        totalsize = 0
        size = 0
        done = False
        for i in range(0, n_blocks):
            block = self.read_heka_next_block()
            if block[0].size == 0:
                return block
            blocks.append(block)
            size = block[0].size
            totalsize += size
            if size < self.block_size:  # did we reach the end?
                break

        # stitch the data together
        data = []
        index = []
        for _ in range(0, len(self.channel_list)):
            data.append(np.empty(totalsize))
            index.append(0)
        for block in blocks:
            for i in range(0, len(self.channel_list)):
                data[i][index[i]:index[i] + block[i].size] = block[i]
                index[i] = index[i] + block[i].size

        return data

    def read_heka_next_block_voltages(self):
        """
        Reads the next block of heka voltages.
        Returns a dictionary with 'data', 'per_block_params', and 'per_channel_params'.
        """  # Read block header
        per_block_params = self.read_heka_header_params(self.per_block_param_list)
        if per_block_params is None:
            return [np.empty(0)]

        # Read per channel header
        per_channel_block_params = []
        for _ in self.channel_list:  # underscore used for discarded parameters
            channel_params = {}
            # i[0] = name, i[1] = datatype
            for i in self.per_channel_param_list:
                channel_params[i[0]] = np.fromfile(self.heka_file, i[1], 1)[0]
            per_channel_block_params.append(channel_params)

        # Read data
        data = []
        dt = np.dtype('>i2')  # int16
        values = np.ndarray([])
        tmp = np.ndarray([])
        for i in range(0, len(self.channel_list)):
            values = 1.0 * np.ones(self.block_size) * per_channel_block_params[i][bytes('Voltage', 'utf-8')]
            # get rid of nan's
            #         values[np.isnan(values)] = 0
            tmp = np.fromfile(self.heka_file, dt, count=self.block_size)
            data.append(values)

        return data

    def read_heka_next_block(self):
        """
        Reads the next block of heka data.
        Returns a dictionary with 'data', 'per_block_params', and 'per_channel_params'.
        """  # Read block header
        per_block_params = self.read_heka_header_params(self.per_block_param_list)
        if per_block_params is None:
            return [np.empty(0)]

        # Read per channel header
        per_channel_block_params = []
        for _ in self.channel_list:  # underscore used for discarded parameters
            channel_params = {}
            # i[0] = name, i[1] = datatype
            for i in self.per_channel_param_list:
                channel_params[i[0]] = np.fromfile(self.heka_file, i[1], 1)[0]
            per_channel_block_params.append(channel_params)

        # Read data
        data = []
        dt = np.dtype('>i2')  # int16
        values = np.ndarray([])
        for i in range(0, len(self.channel_list)):
            values = np.fromfile(self.heka_file, dt, count=self.block_size) * \
                     per_channel_block_params[i][
                         bytes('Scale', 'utf-8')]
            # get rid of nan's
            #         values[np.isnan(values)] = 0
            data.append(values)

        return data

    def read_heka_header_params(self, param_list):
        params = {}
        # pair[0] = name, pair[1] = np.datatype
        array = np.ndarray([])
        for pair in param_list:
            array = np.fromfile(self.heka_file, pair[1], 1)
            if array.size > 0:
                params[pair[0]] = array[0]
            else:
                return None
        return params

    def read_heka_header_param_list(self, datatype):
        """
        Reads the binary parameter list of the following format:
            3 null bytes
            1 byte uint8 - how many params following
            params - 1 byte uint8 - code for datatype (eg encoding[code])
                     datatype.intemsize bytes - name the parameter
        Returns a list of parameters, with
            item[0] = name
            item[1] = numpy datatype
        """
        param_list = []
        self.heka_file.read(3)  # read null characters?
        dt = np.dtype('>u1')
        num_params = np.fromfile(self.heka_file, dt, 1)[0]
        for _ in range(0, num_params):  # underscore used for discarded parameters
            type_code = np.fromfile(self.heka_file, dt, 1)[0]
            name = np.fromfile(self.heka_file, datatype, 1)[0].strip()
            param_list.append([name, ENCODINGS[type_code]])
        return param_list