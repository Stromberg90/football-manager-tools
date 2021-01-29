from enum import Enum
from io import BufferedReader
from struct import unpack
import os
from typing import Optional


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
    def read_from_file(sia_file):
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
    def __init__(self, x=0.0, y=0.0) -> None:
        self.x = x
        self.y = y


class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


class Vertex:
    def __init__(self, position=Vector3(), normal=Vector3(), uv=Vector2()) -> None:
        self.position = position
        self.normal = normal
        self.uv = uv


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
    def from_u8(u8):
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


class Model:
    def __init__(self):
        self.name: str
        self.bounding_box: BoundingBox
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
    def load(path):
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
                material_kind = read_string(sia_file)
                materials_num = read_u8(sia_file)
                for _ in range(materials_num):
                    material = Material()
                    material.kind = material_kind
                    material.name = read_string(sia_file)
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

            vertex_type = read_u32(sia_file)

            for i in range(meshes_num):
                mesh = model.meshes.get(i)

                for _ in range(mesh.vertices_num):
                    position = read_vector3(sia_file)
                    normal = read_vector3(sia_file)

                    uv = None
                    if vertex_type == 3:
                        uv = Vector2(0, 0)
                    else:
                        uv = read_vector2(sia_file)

                    if vertex_type == 3 or vertex_type == 7:
                        skip(sia_file, 0)
                    elif vertex_type == 39:
                        skip(sia_file, 16)
                    elif vertex_type == 47:
                        # This might be a second uv set, 24 bytes matches with another set of uv's
                        skip(sia_file, 24)
                    elif vertex_type == 199:
                        skip(sia_file, 20)
                    elif vertex_type == 231:
                        skip(sia_file, 36)
                    elif vertex_type == 239:
                        skip(sia_file, 44)
                    elif vertex_type == 487:
                        skip(sia_file, 56)
                    elif vertex_type == 495:
                        skip(sia_file, 64)
                    elif vertex_type == 551:
                        skip(sia_file, 20)
                    elif vertex_type == 559:
                        skip(sia_file, 28)
                    elif vertex_type == 575:
                        skip(sia_file, 36)
                    else:
                        raise SiaParseError(
                            "{} is a unknown vertex type".format(vertex_type))

                    mesh.vertices.append(Vertex(position, normal, uv))

            number_of_triangles = int(read_u32(sia_file) / 3)

            for i in range(meshes_num):
                mesh = model.meshes.get(i)
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
                            if cap_type == 0:
                                read_string(sia_file)
                                read_string(sia_file)
                            elif cap_type == 2:
                                read_string(sia_file)
                                read_u32(sia_file)
                            elif cap_type == 9:
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

            skip(sia_file, 4)
            model.read_file_end(sia_file, num)

            return model


def load_sia_file(path):
    return Model.load(path)
