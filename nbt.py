
import struct


### TAG Handlers ###############################################################

class TAG(object):
    
    """ General TAG class, super class of all the other TAG handlers. """
    
    def __init__(self, data, name=None):
        """ Create a new TAG with the given data and optional name. Name must be
        an instance of TAG_String. """
        
        self.data = data
        self.name = name
    
    def write(self, type_byte=True):
        """ Return a string ready for writing to file. If type_byte is true,
        the tag type byte is written to the start of the string, o'wise not. """
        
        string = ''
        if type_byte:
            string += struct.pack('>b', self.byte)
        if self.name:
            string += self.name.write(False)
        return string
    
    def __str__(self):
        if self.name:
            string = '%s("%s"): %s' % (self.__class__.__name__, self.name.data,
                                       str(self.data))
        else:
            string = '%s: %s' % (self.__class__.__name__, str(self.data))
        return string

class TAG_Basic(TAG):
    
    """ General basic data type TAG handler, super class of all basic TAG
    handlers (e.g., byte, short, int, etc). """
    
    @classmethod
    def read(cls, stream, named=False):
        """ Return an instance of the class as read from the start of the given
        stream, as well as the number of bytes read from the steam. """
        
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
    
    def write(self, type_byte=True):
        """ Return a string ready for writing to file. If type_byte is true,
        the tag type byte is written to the start of the string, o'wise not. """
        
        string = TAG.write(self, type_byte)
        string += struct.pack('>' + self.format, self.data)
        return string

class TAG_Byte(TAG_Basic):
    
    byte = 1
    size = 1
    format = 'b'

class TAG_Short(TAG_Basic):
    
    byte = 2
    size = 2
    format = 'h'

class TAG_Int(TAG_Basic):
    
    byte = 3
    size = 4
    format = 'i'

class TAG_Long(TAG_Basic):
    
    byte = 4
    size = 8
    format = 'q'

class TAG_Float(TAG_Basic):
    
    byte = 5
    size = 4
    format = 'f'

class TAG_Double(TAG_Basic):
    
    byte = 6
    size = 8
    format = 'd'


class TAG_String(TAG):
    
    byte = 8
    length_type = TAG_Short
    
    def __init__(self, data, name=None):
        """ Create a new TAG_String with the given data and optional name. Data
        must be a pair of TAG_Short (length of the string) and the string
        itself. Name must be an instance of TAG_String. """
        
        self.length, self.data = data
        self.name = name
    
    @classmethod
    def read(cls, stream, named=False):
        """ Return an instance of the class as read from the start of the given
        stream, as well as the number of bytes read from the steam. """
        
        bytes_read = 0
        
        # Read name, if applicable
        if named:
            name, bytes = TAG_String.read(stream, False)
            stream = stream[bytes:]
            bytes_read += bytes
        else:
            name = None
        
        # Get string size
        length, bytes = cls.length_type.read(stream, False)
        size = length.data
        stream = stream[bytes:]
        bytes_read += bytes
        
        # Read string
        string = stream[:size]
        bytes_read += size
        
        return cls((length, string), name), bytes_read
    
    def write(self, type_byte=True):
        """ Return a string ready for writing to file. If type_byte is true,
        the tag type byte is written to the start of the string, o'wise not. """
        
        string = TAG.write(self, type_byte)
        string += self.length.write(False)
        string += self.data
        return string

class TAG_List(TAG):
    
    byte = 9
    id_size = 1
    id_format = 'b'
    length_type = TAG_Int
    
    def __init__(self, data, name=None):
        """ Create a new TAG_List with the given data and optional name. Data
        must be a triple of TAG_Int (length of the list), type as a class, and
        the entries as a list. Name must be an instance of TAG_String. """
        
        self.length, self.type, self.entries = data
        self.name = name
    
    @classmethod
    def read(cls, stream, named=False):
        """ Return an instance of the class as read from the start of the given
        stream, as well as the number of bytes read from the steam. """
        
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
    
    def add_entry(self, entry):
        """ Add the given entry to the list. Entry must be the correct type. """
        
        self.length.data += 1
        self.entries.append(entry)
    
    def write(self, type_byte=True):
        """ Return a string ready for writing to file. If type_byte is true,
        the tag type byte is written to the start of the string, o'wise not. """
        
        string = TAG.write(self, type_byte)
        string += TAG_Byte(self.type.byte).write(False)
        string += self.length.write(False)
        for entry in self.entries:
            string += entry.write(False)
        return string
    
    def __str__(self):
        if self.name:
            string =  '%s("%s"): ' % (self.__class__.__name__, self.name.data)
        else:
            string = '%s: ' % self.__class__.__name__
        string += '%i entries of type %s\n' % (self.length.data,
                                               self.type.__name__)
        string += '{\n'
        for entry in self.entries:
            string += str(entry) + '\n'
        string += '}'
        return string

class TAG_Byte_Array(TAG):
    
    byte = 7
    length_type = TAG_Int
    byte_type = TAG_Byte
    
    def __init__(self, data, name=None):
        """ Create a new TAG_Byte_Array with the given data and optional name.
        Data must be a pair of TAG_Int (length of the list) and the bytes as a
        list of bytes. Name must be an instance of TAG_String. """
        
        self.length, self.bytes_array = data
        self.name = name
    
    @classmethod
    def read(cls, stream, named=False):
        """ Return an instance of the class as read from the start of the given
        stream, as well as the number of bytes read from the steam. """
        
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
        format = '>' + cls.byte_type.format*length.data
        size = cls.byte_type.size*length.data
        bytes_array = struct.unpack(format, stream[:size])
        bytes_read += size
        
        return cls((length, bytes_array), name), bytes_read
    
    def write(self, type_byte=True):
        """ Return a string ready for writing to file. If type_byte is true,
        the tag type byte is written to the start of the string, o'wise not. """
        
        string = TAG.write(self, type_byte)
        string += self.length.write(False)
        format = '>' + self.byte_type.format*self.length.data
        string += struct.pack(format, *self.bytes_array)
        return string
    
    def __str__(self):
        if self.name:
            string = '%s("%s"): ' % (self.__class__.__name__, self.name.data)
        else:
            string = '%s: ' % self.__class__.__name__
        string += '[%i bytes]' % self.length.data
        return string

class TAG_Compound(TAG):
    
    byte = 10
    
    def __init__(self, data, name=None):
        """ Create a new TAG_Compound with the given data and optional name.
        Data must a list of TAG's. Name must be an instance of TAG_String. """
        
        self.entries = data
        self.length = len(self.entries)
        self.name = name
    
    @classmethod
    def read(cls, stream, named=False):
        """ Return an instance of the class as read from the start of the given
        stream, as well as the number of bytes read from the steam. """
        
        bytes_read = 0
        
        # Read name, if applicable
        if named:
            name, bytes = TAG_String.read(stream, False)
            stream = stream[bytes:]
            bytes_read += bytes
        else:
            name = None
        
        # Read entries
        # Note: It's okay to index the entries by name, as the NBT spec states
        #       that the names must be unqiue within each TAG_Compound.
        entries = {}
        while True:
            # Tag type
            tag_type, bytes = get_tag_type(stream)
            bytes_read += bytes
            stream = stream[bytes:]
            # End of TAG_Compound
            if tag_type == TAG_End:
                break
            # Tag data
            entry, bytes = tag_type.read(stream, True)
            entries[entry.name.data] = entry
            bytes_read += bytes
            stream = stream[bytes:]
        
        return cls(entries, name), bytes_read
    
    def write(self, type_byte=True):
        """ Return a string ready for writing to file. If type_byte is true,
        the tag type byte is written to the start of the string, o'wise not. """
        
        string = TAG.write(self, type_byte)
        for entry in self.entries.values():
            string += entry.write()
        string += TAG_End().write()
        return string
    
    def __str__(self):
        if self.name:
            string = '%s("%s"): ' % (self.__class__.__name__, self.name.data)
        else:
            string = '%s: ' % self.__class__.__name__
        string += '%i entries\n' % self.length
        string += '{\n'
        for entry in self.entries.values():
            string += str(entry) + '\n'
        string += '}'
        return string

class TAG_End(TAG):
    
    byte = 0
    
    def __init__(self):
        """ Create a new TAG_End. """
        
        self.name = None
    
    def write(self):
        """ Return a string ready for writing to file. If type_byte is true,
        the tag type byte is written to the start of the string, o'wise not. """
        
        string = TAG.write(self, True)
        return string
    
    def __str__(self):
        return 'TAG_End'


### TAG Type Bytes #############################################################

type_bytes = {0: TAG_End, 1: TAG_Byte, 2: TAG_Short, 3: TAG_Int, 4: TAG_Long,
              5: TAG_Float, 6: TAG_Double, 7: TAG_Byte_Array, 8: TAG_String,
              9: TAG_List, 10: TAG_Compound}


### Helper Function ############################################################

def get_tag_type(stream):
    """ Return the tag type class specified by the first byte in the given
    stream, as well as the number of bytes read from the stream (one). """
    
    format = 'b'
    size = 1
    
    type_byte = struct.unpack('>'+format, stream[:size])[0]
    tag_type = type_bytes[type_byte]
    
    return tag_type, size


### Main NBT Parser Class ######################################################

class nbt(object):
    
    """ Named Binary Tag (NBT) file parser. """
    
    def __init__(self):
        """ Create a new NBT object. """
        
        self.tags = []
    
    def read(self, stream):
        """ Parse the given (ungzipped) NBT file and read it into memory. """
        
        self.tags = []
        while len(stream) > 0:
            tag, bytes = self.read_tag(stream)
            self.tags.append(tag)
            stream = stream[bytes:]
    
    def write(self):
        """ Return a string ready for writing to file. """
        
        string = ''
        for tag in self.tags:
            string += tag.write()
        
        return string
    
    def display(self):
        """ Print out a representation of the NBT data structure. """
        
        for tag in self.tags:
            print tag
    
    def read_tag(self, stream):
        """ Read the tag from the start of the given stream, and return the TAG
        class instance and the number of bytes read from the steam. """
        
        bytes_read = 0
        
        type, bytes = get_tag_type(stream)
        stream = stream[bytes:]
        bytes_read += bytes
        
        if type != TAG_End:
            tag, bytes = type.read(stream, True)
            stream = stream[bytes:]
            bytes_read += bytes
        
        return tag, bytes_read
