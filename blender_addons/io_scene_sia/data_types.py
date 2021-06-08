from enum import Enum
import sys
from io import BufferedReader
from . import read_utils

class Bitfield():
    def __init__(self):
        self.__bits = 0

    @staticmethod
    def from_number(number: int):
        bitfield = Bitfield()
        bitfield.__bits = number
        return bitfield

    def number(self):
        return self.__bits

    def __getitem__(self, key: int):
        return (self.__bits & 1 << key) != 0

    def __setitem__(self, key: int, value: bool):
        if value:
            self.__bits |= 1 << key
        else:
            self.__bits != 1 << key

            
class Model:
    def __init__(self):
        self.name = ""
        self.bounding_box = BoundingBox()
        self.settings = None
        self.meshes = {}
        self.end_kind = None

        
class BoundingBox:
    def __init__(self):
        self.max_x = sys.float_info.min
        self.max_y = sys.float_info.min
        self.max_z = sys.float_info.min
        self.min_x = sys.float_info.max
        self.min_y = sys.float_info.max
        self.min_z = sys.float_info.max

    def update_with_vector(self, v):
        self.min_x = min(self.min_x, v.x)
        self.min_y = min(self.min_y, v.y)
        self.min_z = min(self.min_z, v.z)

        self.max_x = max(self.max_x, v.x)
        self.max_y = max(self.max_y, v.y)
        self.max_z = max(self.max_z, v.z)

    @staticmethod
    def read_from_file(sia_file: BufferedReader):
        bounding_box = BoundingBox()
        bounding_box.min_x = read_utils.read_f32(sia_file)
        bounding_box.min_y = read_utils.read_f32(sia_file)
        bounding_box.min_z = read_utils.read_f32(sia_file)
        bounding_box.max_x = read_utils.read_f32(sia_file)
        bounding_box.max_y = read_utils.read_f32(sia_file)
        bounding_box.max_z = read_utils.read_f32(sia_file)
        return bounding_box


class Mesh:
    def __init__(self):
        self.id = 0
        self.vertices_num = 0
        self.triangles_num = 0
        self.materials = []
        self.vertices = []
        self.triangles = []


class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

        
def read_vector2(file):
    x = read_utils.read_f32(file)
    y = read_utils.read_f32(file)
    return Vector2(x, y)


class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

        
def read_vector3(file):
    x = read_utils.read_f32(file)
    y = read_utils.read_f32(file)
    z = read_utils.read_f32(file)
    return Vector3(x, y, z)


class Vertex:
    def __init__(self, position=Vector3(), normal=Vector3(), uv=Vector2()):
        self.position = position
        self.normal = normal
        self.uv = uv


class Triangle:
    def __init__(self, i1, i2, i3):
        self.index1 = i1
        self.index2 = i2
        self.index3 = i3

    def max(self):
        return max(self.index1, self.index2, self.index3)

    
def read_triangle_u32(file):
    return Triangle(
        read_utils.read_u32(file),
        read_utils.read_u32(file),
        read_utils.read_u32(file)
    )


def read_triangle_u16(file):
    return Triangle(
        read_utils.read_u16(file),
        read_utils.read_u16(file),
        read_utils.read_u16(file)
    )

class Texture:
    def __init__(self):
        self.id = 0
        self.name = ""


class Material:
    def __init__(self):
        self.name = ""
        self.kind = ""
        self.textures = []

        
class MeshType(Enum):
    RenderFlags = 2
    VariableLength = 8
    BodyPart = 88
    RearCap = 152
    Glasses = 136
    StadiumRoof = 216
    PlayerTunnel = 232
    SideCap = 248
    Unknown = 0

    @staticmethod
    def from_u8(u8):
        if u8 == 2:
            return MeshType.RenderFlags
        elif u8 == 8:
            return MeshType.VariableLength
        elif u8 == 88:
            return MeshType.BodyPart
        elif u8 == 152:
            return MeshType.RearCap
        elif u8 == 136:
            return MeshType.Glasses
        elif u8 == 216:
            return MeshType.StadiumRoof
        elif u8 == 232:
            return MeshType.PlayerTunnel
        elif u8 == 248:
            return MeshType.SideCap
        else:
            return MeshType.Unknown


class EndKindType(Enum):
    MeshType = 0
    IsBanner = 1
    IsCompBanner = 2


class EndKind():
    def __init__(self):
        self.type = None
        self.value = None

    @staticmethod
    def MeshType(value):
        result = EndKind()
        result.type = EndKindType.MeshType
        result.value = value
        return result

    @staticmethod
    def IsBanner(value):
        result = EndKind()
        result.type = EndKindType.IsBanner
        result.value = value
        return result

    @staticmethod
    def IsCompBanner(value):
        result = EndKind()
        result.type = EndKindType.IsCompBanner
        result.value = value
        return result
