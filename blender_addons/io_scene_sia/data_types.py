from enum import Enum
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

class BoundingBox:
    def __init__(self):
        self.max_x = float
        self.max_y = float
        self.max_z = float
        self.min_x = float
        self.min_y = float
        self.min_z = float

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
    def __init__(self) -> None:
        self.id: int
        self.vertices_num: int
        self.triangles_num: int
        self.materials: list[Material] = []
        self.vertices: list[Vertex] = []
        self.triangles: list[Triangle] = []


class Vector2:
    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = x
        self.y = y

        
def read_vector2(file: BufferedReader) -> Vector2:
    x = read_utils.read_f32(file)
    y = read_utils.read_f32(file)
    return Vector2(x, y)


class Vector3:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z

        
def read_vector3(file: BufferedReader) -> Vector3:
    x = read_utils.read_f32(file)
    y = read_utils.read_f32(file)
    z = read_utils.read_f32(file)
    return Vector3(x, y, z)        


class Vertex:
    def __init__(self, position: Vector3 = Vector3(), normal: Vector3 = Vector3(), uv: Vector2 = Vector2()) -> None:
        self.position: Vector3 = position
        self.normal: Vector3 = normal
        self.uv: Vector2 = uv


class Triangle:
    def __init__(self) -> None:
        self.index1: int
        self.index2: int
        self.index3: int

    def max(self) -> int:
        return max(self.index1, self.index2, self.index3)

    
def read_triangle_u32(file: BufferedReader) -> Triangle:
    triangle = Triangle()
    triangle.index1 = read_utils.read_u32(file)
    triangle.index2 = read_utils.read_u32(file)
    triangle.index3 = read_utils.read_u32(file)
    return triangle


def read_triangle_u16(file: BufferedReader) -> Triangle:
    triangle = Triangle()
    triangle.index1 = read_utils.read_u16(file)
    triangle.index2 = read_utils.read_u16(file)
    triangle.index3 = read_utils.read_u16(file)
    return triangle    

class Texture:
    def __init__(self) -> None:
        self.id: int
        self.name: str


class Material:
    def __init__(self) -> None:
        self.name: str
        self.kind: str
        self.textures: list[Texture] = []

        
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
    def from_u8(u8: int):
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
    def __init__(self) -> None:
        self.type: EndKindType
        self.value = None

    @staticmethod
    def MeshType(value: str):
        result = EndKind()
        result.type = EndKindType.MeshType
        result.value = value
        return result

    @staticmethod
    def IsBanner(value: int):
        result = EndKind()
        result.type = EndKindType.IsBanner
        result.value = value
        return result

    @staticmethod
    def IsCompBanner(value: int):
        result = EndKind()
        result.type = EndKindType.IsCompBanner
        result.value = value
        return result
