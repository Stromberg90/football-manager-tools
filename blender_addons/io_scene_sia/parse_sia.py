from enum import Enum
from io import BufferedReader
from struct import unpack
import os
from typing import Optional
from pprint import pprint


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


class SiaParseError(Exception):
    pass


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
        bounding_box.min_x = read_f32(sia_file)
        bounding_box.min_y = read_f32(sia_file)
        bounding_box.min_z = read_f32(sia_file)
        bounding_box.max_x = read_f32(sia_file)
        bounding_box.max_y = read_f32(sia_file)
        bounding_box.max_z = read_f32(sia_file)
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


class Vector3:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


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


class Texture:
    def __init__(self) -> None:
        self.id: int
        self.name: str


class Material:
    def __init__(self) -> None:
        self.name: str
        self.kind: str
        self.textures: list[Texture] = []


def skip(file: BufferedReader, offset: int) -> None:
    file.seek(offset, 1)


def read_u32(file: BufferedReader) -> int:
    return unpack('<I', file.read(4))[0]


def read_u16(file: BufferedReader) -> int:
    return unpack('<H', file.read(2))[0]


def read_u8(file: BufferedReader) -> int:
    return unpack('<B', file.read(1))[0]


def read_f32(file: BufferedReader) -> float:
    return unpack('<f', file.read(4))[0]


def read_vector2(file: BufferedReader) -> Vector2:
    x = read_f32(file)
    y = read_f32(file)
    return Vector2(x, y)


def read_vector3(file: BufferedReader) -> Vector3:
    x = read_f32(file)
    y = read_f32(file)
    z = read_f32(file)
    return Vector3(x, y, z)


def read_string(file: BufferedReader) -> str:
    length = read_u32(file)
    if length == 0:
        return ""
    return unpack('<{}s'.format(length), file.read(length))[0]


def read_string_with_length(file: BufferedReader, length: int) -> str:
    return unpack('<{}s'.format(length), file.read(length))[0]


def read_string_u8_len(file: BufferedReader) -> str:
    length = read_u8(file)
    return unpack('<{}s'.format(length), file.read(length))[0]


def read_triangle_u32(file: BufferedReader) -> Triangle:
    triangle = Triangle()
    triangle.index1 = read_u32(file)
    triangle.index2 = read_u32(file)
    triangle.index3 = read_u32(file)
    return triangle


def read_triangle_u16(file: BufferedReader) -> Triangle:
    triangle = Triangle()
    triangle.index1 = read_u16(file)
    triangle.index2 = read_u16(file)
    triangle.index3 = read_u16(file)
    return triangle


class MeshType(Enum):
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
        if u8 == 8:
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


class Model:
    def __init__(self):
        self.name: str
        self.bounding_box: BoundingBox
        self.settings: Bitfield
        self.meshes: dict[int, Mesh] = {}
        self.end_kind: Optional[EndKind]

    @staticmethod
    def read_header(sia_file: BufferedReader):
        header = sia_file.read(4)
        if header != b'SHSM':
            raise SiaParseError(
                "Expexted header SHSM, but found {}".format(header))

    @staticmethod
    def read_file_end(sia_file: BufferedReader, num: int):
        end = sia_file.read(4)
        if end != b'EHSM':
            raise SiaParseError(
                "Expected EHSM, but found {} at file byte position: {} num is {}".format(
                    end, sia_file.tell(), num))

    @staticmethod
    def load(path: str):
        if not os.path.exists(path) or os.path.splitext(path)[1] != ".sia":
            raise SiaParseError(
                "{} does not exist or is not a valid sia file".format(path))

        with open(path, "rb") as sia_file:
            model = Model()
            model.read_header(sia_file)

            read_u32(sia_file)  # Version maybe?

            model.name = read_string(sia_file)

            # So far these bytes have only been zero, changing them did nothing
            skip(sia_file, 12)

            # This might be some sort of scale, since it tends to resemble
            # another bouding box value. Maybe sphere radius
            read_f32(sia_file)

            model.bounding_box = BoundingBox.read_from_file(sia_file)

            objects_num = read_u32(sia_file)

            for _ in range(objects_num):
                mesh = Mesh()

                skip(sia_file, 4)
                mesh.vertices_num = read_u32(sia_file)

                skip(sia_file, 4)
                # Number of triangles when divided by 3
                mesh.triangles_num = int(read_u32(sia_file) / 3)

                mesh.id = read_u32(sia_file)
                skip(sia_file, 8)

                model.meshes[mesh.id] = mesh

            meshes_num = read_u32(sia_file)
            # After changing these to zero mesh is still there, but the lighting has changed, interesting.
            skip(sia_file, 16)

            for i in range(meshes_num):
                mesh = model.meshes.get(i)
                assert(mesh is not None)
                material_name = read_string(sia_file)
                materials_num = read_u8(sia_file)
                for _ in range(materials_num):
                    material = Material()
                    material.kind = read_string(sia_file)
                    material.name = material_name
                    texture_num = read_u8(sia_file)
                    for _ in range(texture_num):
                        texture = Texture()
                        texture.id = read_u8(sia_file)
                        texture.name = read_string(sia_file)
                        material.textures.append(texture)
                    mesh.materials.append(material)

                if i != meshes_num - 1:
                    skip(sia_file, 80)

            # Changed all of these to 0, mesh still showed up and looked normal
            skip(sia_file, 64)

            vertices_total_num = read_u32(sia_file)

            # There seems to be only 10 bits checked, so maybe it's a u16 instead,
            # and the other 16 bits are something else
            model.settings = Bitfield.from_number(read_u32(sia_file))
            # Result so far:
            # 1 and 2 Always checked, normal and position I think
            # 3 I think this is uv, also always checked
            # 4 8 bits
            # 5 8 bits
            # 6 16 bits
            # 7 and 8 Unsure, but 12 or 8 I think for either one
            # 9 20 bits
            # 10 4 bits, seems strange

            for i in range(meshes_num):
                mesh = model.meshes.get(i)
                assert(mesh is not None)

                for _ in range(mesh.vertices_num):
                    position, normal, uv = (None, None, None)
                    if model.settings[0]:  # This and the normal might be flipped
                        position = read_vector3(sia_file)
                    else:
                        raise SiaParseError("Missing position flag")

                    if model.settings[1]:
                        normal = read_vector3(sia_file)
                    else:
                        raise SiaParseError("Missing normal flag")

                    if model.settings[2]:  # First uv set flag
                        uv = read_vector2(sia_file)
                    else:
                        uv = Vector2(0, 0)

                    if model.settings[3]:
                        skip(sia_file, 8)

                    if model.settings[4]:
                        skip(sia_file, 8)

                    if model.settings[5]:
                        skip(sia_file, 16)

                    if model.settings[6]:
                        skip(sia_file, 8)
                        # |---> These two are probably not correct
                    if model.settings[7]:
                        skip(sia_file, 12)

                    if model.settings[8]:
                        skip(sia_file, 20)

                    if model.settings[9]:
                        skip(sia_file, 4)

                    mesh.vertices.append(Vertex(position, normal, uv))

            number_of_triangles = int(read_u32(sia_file) / 3)

            for i in range(meshes_num):
                mesh = model.meshes.get(i)
                assert(mesh is not None)
                for _ in range(mesh.triangles_num):
                    triangle: Triangle
                    if vertices_total_num > 65535:
                        triangle = read_triangle_u32(sia_file)
                    else:
                        triangle = read_triangle_u16(sia_file)

                    if triangle.max() > len(mesh.vertices):
                        raise SiaParseError(
                            "Face index larger than available vertices\nFace Index: {}\nVertices Length: {}\n at file byte position: {}".format(triangle.max(), len(mesh.vertices), sia_file.tell()))

                    mesh.triangles.append(triangle)

            # These two numbers seems to be related to how many bytes there
            # are to read after, maybe bones or something?  But I've yet to
            # find out exactly how they related to each other, it doesn't
            # seem to be as simple as some_number * some other number
            some_number = read_u32(sia_file)
            some_number2 = read_u32(sia_file)

            # Could be a bit field, not sure, but makes more sense than magic number
            num = read_u8(sia_file)

            if num == 75 or num == 215:
                skip(sia_file, 3)
                skip(sia_file, (some_number2 * 56))
                # This seems wierd, and I wonder what data is hiding there.
                skip(sia_file, 1)

            if num == 0 or num == 215:
                pass
            elif num == 42 or num == 75:
                kind = read_string_u8_len(sia_file)
                if kind == b"mesh_type":
                    mesh_type = MeshType.from_u8(read_u8(sia_file))
                    if mesh_type == MeshType.VariableLength:
                        model.end_kind = EndKind.MeshType(
                            read_string(sia_file))
                    elif mesh_type == MeshType.BodyPart:
                        model.end_kind = EndKind.MeshType(
                            read_string_with_length(sia_file, 4))
                    elif mesh_type == MeshType.RearCap:
                        model.end_kind = EndKind.MeshType(
                            read_string_with_length(sia_file, 8))
                        num_caps = read_u32(sia_file)
                        for _ in range(num_caps):
                            cap_type = read_u32(sia_file)
                            skip(sia_file, 80)
                            # This is probably position and such
                            entries_num = read_u32(sia_file)
                            skip(sia_file, int(entries_num * 48))
			    # TODO: Why are these are the same?
                            if cap_type == 0:
                                read_string(sia_file)
                                read_string(sia_file)
                            elif cap_type == 2:
                                read_string(sia_file)
                                read_u32(sia_file)
                            elif cap_type == 9:
                                read_string(sia_file)
                                read_u32(sia_file)
                            elif cap_type == 10:
                                read_string(sia_file)
                                read_u32(sia_file)
                            else:
                                raise SiaParseError("{} is a unknown cap type at file byte position: {}".format(
                                    cap_type, sia_file.tell()))

                        model.read_file_end(sia_file, num)

                        return model
                    elif mesh_type == MeshType.StadiumRoof:
                        model.end_kind = EndKind.MeshType(
                            read_string_with_length(sia_file, 12))
                    elif mesh_type == MeshType.Glasses:
                        model.end_kind = EndKind.MeshType(
                            read_string_with_length(sia_file, 7))
                    elif mesh_type == MeshType.PlayerTunnel:
                        model.end_kind = EndKind.MeshType(
                            read_string_with_length(sia_file, 13))
                    elif mesh_type == MeshType.SideCap:
                        model.end_kind = EndKind.MeshType(
                            read_string_with_length(sia_file, 14))
                    elif mesh_type == MeshType.Unknown:
                        raise SiaParseError("{} is a unknown mesh type at file byte position: {}".format(
                            mesh_type, sia_file.tell()))
                elif kind == b"is_banner":
                    model.end_kind = EndKind.IsBanner(read_u8(sia_file) != 0)
                elif kind == b"is_comp_banner":
                    model.end_kind = EndKind.IsBanner(read_u8(sia_file) != 0)
                else:
                    raise SiaParseError(
                        "{} is a unknown kind = {} type at file byte position: {}".format(num, kind, sia_file.tell()))
            else:
                raise SiaParseError("{} is a unknown type at file byte position: {}".format(
                    num, sia_file.tell()))

            instances = read_u32(sia_file)
            print("instances", instances, " at ", sia_file.tell())
            for i in range(0, instances):
                instance_type = read_u32(sia_file)
                # unknown or instance, could be a bitflag or similar
                if instance_type == 1 or instance_type == 2 or instance_type == 3:
                    skip(sia_file, 132)
                elif instance_type == 9:
                    skip(sia_file, 80)
                    num1 = read_u32(sia_file)
                    print("num1: ", num1)
                    print("Type 9 Skip at:", sia_file.tell())
                    for _ in range(0, num1):
                        skip(sia_file, 48)
                elif instance_type == 0:
                    skip(sia_file, 80)
                    num1 = read_u32(sia_file)
                    for _ in range(0, num1):
                        skip(sia_file, 48)
                else:
                    print("mesh_type: ", mesh_type)
                    print("model.end_kind.value: ", model.end_kind.value)
                    raise SiaParseError("{} is a unknown instance_type at file byte position: {}".format(
                        instance_type, sia_file.tell()))
                # print(instance_type)
                # Could it be that only some of them have name and paths, for type 9 I skip over some stuff
                print("before name:", sia_file.tell())
                pprint(locals())
                name = read_string(sia_file)
                print(name)
                path = read_string(sia_file)
                print(path)

            model.read_file_end(sia_file, num)

            return model


def load_sia_file(path: str):
    return Model.load(path)
