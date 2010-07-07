
import struct


### TAG classes ################################################################

class TAG(object):
    """ Super class for all the TAG types. """
    
    def __init__(self, data, name=None):
        """ Create a new TAG with the given data and optional name. """
        
        self.data = data
        self.name = name
    
    def __str__(self):
        """ Standard string representation of TAG. """
        
        if self.name:
            return self.__class__.__name__ + '("' + self.name.data + '"): ' + str(self.data)
        else:
            return self.__class__.__name__ + ': ' + str(self.data)


class TAG_Basic(TAG):
    
    """ Super class for basic TAG types (like short, int, byte, etc.). """
    
    @classmethod
    def read(cls, stream, named=False):
        """ Read a TAG_Basic from the start of the given stream. Return an
        instance of TAG_Basic represnting the read TAG, and the number of bytes
        read. """
        
        bytes_read = 0
        
        # Read name, if applicable
        if named:
            name, bytes = TAG_String.read(stream, False)
            stream = stream[bytes:]
            bytes_read += bytes
        else:
            name = None
        
        # Read data itself
        format = '>' + cls.format
        data = struct.unpack(format, stream[:cls.size])[0]
        bytes_read += cls.size
        
        return cls(data, name), bytes_read
    
    def write(self):
        """ Return a binary string ready for writing to file. """
        
        if self.name:
            

class TAG_Byte(TAG_Basic):
    
    size = 1
    format = 'b'

class TAG_Short(TAG_Basic):
    
    size = 2
    format = 'h'

class TAG_Int(TAG_Basic):
    
    size = 4
    format = 'i'

class TAG_Long(TAG_Basic):
    
    size = 8
    format = 'q'

class TAG_Float(TAG_Basic):
    
    size = 4
    format = 'f'

class TAG_Double(TAG_Basic):
    
    size = 8
    format = 'd'


class TAG_String(TAG):
    
    length_type = TAG_Short
    
    @classmethod
    def read(cls, stream, named=False):
        """ Read a TAG_String from the start of the given stream. Return the
        TAG_String instance and the number of bytes read. """
        
        bytes_read = 0
        
        # Read name, if applicable
        if named:
            name, bytes = TAG_String.read(stream, False)
            stream = stream[bytes:]
            bytes_read += bytes
        else:
            name = None
        
        # Get string size
        size_byte, bytes = cls.length_type.read(stream, False)
        size = size_byte.data
        stream = stream[bytes:]
        bytes_read += bytes
        
        # Read string
        string = stream[:size]
        bytes_read += size
        
        return cls(string, name), bytes_read

class TAG_List(TAG):
    
    id_size = 1
    id_format = 'b'
    length_type = TAG_Int
    
    def __init__(self, data, name=None):
        """ Create a new TAG_List with the given length (number of elements),
        tag type and optionally a name. """
        
        self.length, self.type, self.entries = data
        self.name = name
    
    @classmethod
    def read(cls, stream, named=False):
        """ Read a TAG_List from the start of the given stream. Return the
        name (if applicable), length (number of items), and the number of bytes
        read. """
        
        bytes_read = 0
        
        # Read name, if applicable
        if named:
            name, bytes = TAG_String.read(stream, False)
            stream = stream[bytes:]
            bytes_read += bytes
        else:
            name = None
        
        # Get tag type
        type_byte = struct.unpack('>'+cls.id_format, stream[:cls.id_size])[0]
        tag_type = type_bytes[type_byte]
        bytes_read += cls.id_size
        stream = stream[cls.id_size:]
        
        # Get list length
        length, bytes = cls.length_type.read(stream, False)
        stream = stream[bytes:]
        bytes_read += bytes
        
        # Read entries
        entries = []
        for i in xrange(length.data):
            entry, bytes = tag_type.read(stream, False)
            entries.append(entry)
            stream = stream[bytes:]
            bytes_read += bytes
        
        return cls((length, tag_type, entries), name), bytes_read
    
    def __str__(self):
        if self.name:
            string = self.__class__.__name__ + '("' + self.name.data + '"): '
        else:
            string = self.__class__.__name__ + ': '
        string += str(self.length.data) + ' entries of type ' + self.type.__name__ + '\n'
        string += '{\n'
        for i in xrange(self.length.data):
            string += str(self.entries[i]) + '\n'
        string += '}'
        return string

class TAG_Byte_Array(TAG):
    
    length_type = TAG_Int
    byte_type = TAG_Byte
    
    def __init__(self, data, name=None):
        """ Create a new TAG_Byte_Array with the given length (number of
        elements), bytes and optionally a name. """
        
        self.length, self.bytes_array = data
        self.name = name
    
    @classmethod
    def read(cls, stream, named=False):
        """ Read a TAG_Byte_Array from the start of the given stream. Return the
        TAG_Byte_Array instance and the number of bytes read. """
        
        bytes_read = 0
        
        # Read name, if applicable
        if named:
            name, bytes = TAG_String.read(stream, False)
            stream = stream[bytes:]
            bytes_read += bytes
        else:
            name = None
        
        # Read length
        length, bytes = cls.length_type.read(stream, False)
        stream = stream[bytes:]
        bytes_read += bytes
        
        # Read bytes
        bytes_array = []
        for i in xrange(length.data):
            byte, bytes = cls.byte_type.read(stream, False)
            bytes_array.append(byte)
            stream = stream[bytes:]
            bytes_read += bytes
        
        return cls((length, bytes_array), name), bytes_read
    
    def __str__(self):
        if self.name:
            string = self.__class__.__name__ + '("' + self.name.data + '"): '
        else:
            string = self.__class__.__name__ + ': '
        string += '[' + str(self.length.data) + ' bytes]'
        return string

class TAG_Compound(TAG):
    
    def __init__(self, data, name=None):
        """ Create a new TAG_Compound with the given entries, and optionally
        a name. """
        
        self.entries = data
        self.length = len(self.entries)
        self.name = name
    
    @classmethod
    def read(cls, stream, named=False):
        """ Read a TAG_Compound from the start of the given stream. Return the
        name (if applicable), the length (number of entries) and the number of
        bytes read. """
        
        bytes_read = 0
        
        # Read name, if applicable
        if named:
            name, bytes = TAG_String.read(stream, False)
            stream = stream[bytes:]
            bytes_read += bytes
        else:
            name = None
        
        # Read entries
        entries = []
        while True:
            # Tag type
            tag_type, bytes = get_tag_type(stream)
            bytes_read += bytes
            stream = stream[bytes:]
            if tag_type == TAG_End: break
            # Tag data
            entry, bytes = tag_type.read(stream, True)
            entries.append(entry)
            bytes_read += bytes
            stream = stream[bytes:]
        
        return cls(entries, name), bytes_read
    
    def __str__(self):
        if self.name:
            string = self.__class__.__name__ + '("' + self.name.data + '"): '
        else:
            string = self.__class__.__name__ + ': '
        string += str(self.length) + ' entries\n'
        string += '{\n'
        for i in xrange(self.length):
            string += str(self.entries[i]) + '\n'
        string += '}'
        return string

class TAG_End(TAG):
    pass


### TAG types ##################################################################

type_bytes = {0: TAG_End,
              1: TAG_Byte,
              2: TAG_Short,
              3: TAG_Int,
              4: TAG_Long,
              5: TAG_Float,
              6: TAG_Double,
              7: TAG_Byte_Array,
              8: TAG_String,
              9: TAG_List,
              10: TAG_Compound}


### TAG type byte reader #######################################################

def get_tag_type(stream):
    """ Return the tag type directed by the first byte in the given stream
    and the number of bytes read. """
    
    format = 'b'
    size = 1
    
    type_byte = struct.unpack('>'+format, stream[:size])[0]
    tag_type = type_bytes[type_byte]
    
    return tag_type, size


### Parser class ###############################################################

class nbt(object):
    
    """ Named Binary Tag (nbt) file parser. """
    
    def __init__(self):
        """ Create a new nbt object. """
        
        self.tags = []
    
    def read(self, stream):
        """ Parse the given nbt file (ungzipped) and read it into memory. """
        
        self.tags = []
        while len(stream) > 0:
            tag, bytes = self.read_tag(stream)
            self.tags.append(tag)
            stream = stream[bytes:]
    
    def write(self):
        """ Return a string ready to be written to file. """
        
        string = ''
        for tag in self.tags:
            string += tag.write()
        
        return string
    
    def read_tag(self, stream):
        """ Read the tag from the start of the given stream, and return the tag
        type and the number of bytes read. """
        
        bytes_read = 0
        
        type, bytes = get_tag_type(stream)
        stream = stream[bytes:]
        bytes_read += bytes
        
        if type == TAG_End:
            pass
        else:
            tag, bytes = type.read(stream, True)
            stream = stream[bytes:]
            bytes_read += bytes
            print tag
        
        return tag, bytes_read
