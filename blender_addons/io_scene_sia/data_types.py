from enum import IntEnum
import sys
from io import BufferedReader
from . import read_utils
from . import write_utils


class Bitfield:
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
        self.meshes = []
        self.end_kind = None


class BoundingBox:
    float_min = sys.float_info.min
    float_max = sys.float_info.max

    def __init__(
        self,
        min_x=float_max,
        min_y=float_max,
        min_z=float_max,
        max_x=float_min,
        max_y=float_min,
        max_z=float_min,
    ):
        self.min_x = min_x
        self.min_y = min_y
        self.min_z = min_z
        self.max_x = max_x
        self.max_y = max_y
        self.max_z = max_z

    def update_with_vector(self, v):
        self.min_x = min(self.min_x, v.x)
        self.min_y = min(self.min_y, v.y)
        self.min_z = min(self.min_z, v.z)

        self.max_x = max(self.max_x, v.x)
        self.max_y = max(self.max_y, v.y)
        self.max_z = max(self.max_z, v.z)

    @staticmethod
    def read_from_file(sia_file: BufferedReader):
        return BoundingBox(
            read_utils.f32(sia_file),
            read_utils.f32(sia_file),
            read_utils.f32(sia_file),
            read_utils.f32(sia_file),
            read_utils.f32(sia_file),
            read_utils.f32(sia_file),
        )

    def write(self, file):
        write_utils.f32(file, self.min_x)
        write_utils.f32(file, self.min_y)
        write_utils.f32(file, self.min_z)

        write_utils.f32(file, self.max_x)
        write_utils.f32(file, self.max_y)
        write_utils.f32(file, self.max_z)


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
    x = read_utils.f32(file)
    y = read_utils.f32(file)
    return Vector2(x, y)


class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


def read_vector3(file):
    x = read_utils.f32(file)
    y = read_utils.f32(file)
    z = read_utils.f32(file)
    return Vector3(x, y, z)


class Vertex:
    def __init__(
        self, position=Vector3(), normal=Vector3(), uv=Vector2(), tangent=Vector3()
    ):
        self.position = position
        self.normal = normal
        self.uv = uv
        self.tangent = tangent


class Triangle:
    def __init__(self, i1, i2, i3):
        self.index1 = i1
        self.index2 = i2
        self.index3 = i3

    def max(self):
        return max(self.index1, self.index2, self.index3)

    @staticmethod
    def read_u32(file):
        return Triangle(
            read_utils.u32(file), read_utils.u32(file), read_utils.u32(file)
        )

    @staticmethod
    def read_u16(file):
        return Triangle(
            read_utils.u16(file), read_utils.u16(file), read_utils.u16(file)
        )

    def write_u32(self, file):
        write_utils.u32(file, self.index1)
        write_utils.u32(file, self.index2)
        write_utils.u32(file, self.index3)

    def write_u16(self, file):
        write_utils.u16(file, self.index1)
        write_utils.u16(file, self.index2)
        write_utils.u16(file, self.index3)


class TextureKind(IntEnum):
    Albedo = 0
    RoughnessMetallicAmbientOcclusion = 1
    Normal = 2
    Mask = 5

    @staticmethod
    def from_u8(u8):
        for kind in TextureKind:
            if kind == u8:
                return kind


class Texture:
    def __init__(self, kind=None, name=""):
        self.kind = kind
        self.path = name

    def __eq__(self, other):
        if isinstance(other, Texture):
            return self.kind == other.kind and self.path == other.path

    def write(self, file):
        write_utils.u8(file, int(self.kind))
        write_utils.string(file, self.path)


class Material:
    def __init__(self, name="", kind=""):
        self.name = name
        self.kind = kind
        self.textures = []

    def __hash__(self):
        hashstr = str(self.name) + str(self.kind)
        for texture in self.textures:
            hashstr += str(texture.path)
        return hash(hashstr)

    def __eq__(self, other):
        if isinstance(other, Material):
            if self.name != other.name or self.kind != other.kind:
                return False
            for texture in self.textures:
                if texture not in other.textures:
                    return False
            return True

        return False


class MeshType(IntEnum):
    Unknown = 0
    RenderFlags = 2
    VariableLength = 8
    BodyPart = 88
    RearCap = 152
    Glasses = 136
    StadiumRoof = 216
    PlayerTunnel = 232
    SideCap = 248

    @staticmethod
    def from_u8(u8):
        for mesh_type in MeshType:
            if mesh_type == u8:
                return mesh_type


class EndKindType(IntEnum):
    MeshType = 0
    IsBanner = 1
    IsCompBanner = 2

    @staticmethod
    def from_u8(u8):
        for end_kind in EndKindType:
            if end_kind == u8:
                return end_kind


class EndKind:
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
