from io import BufferedReader
from struct import unpack
import os


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
        self.num_vertices: int
        self.num_triangles: int
        self.materials: list[Material] = []
        self.vertices = None
        self.triangles = None


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


def read_u8(file: BufferedReader) -> int:
    return unpack('<B', file.read(1))[0]


def read_f32(file: BufferedReader) -> float:
    return unpack('<f', file.read(4))[0]


def read_string(file: BufferedReader) -> str:
    length = read_u32(file)
    return unpack('<{}s'.format(length), file.read(length))[0]


class Model:
    def __init__(self):
        self.name: str
        self.bounding_box: BoundingBox
        self.meshes: dict[int, Mesh] = {}

    @staticmethod
    def read_header(sia_file):
        header = sia_file.read(4)
        if header != b'SHSM':
            raise SiaParseError(
                "Expexted header SHSM, but found {}".format(header))

    @staticmethod
    def load(path):
        if not os.path.exists(path) or os.path.splitext(path)[1] != ".sia":
            raise SiaParseError(
                "{} does not exist or is not a valid sia file".format(path))

        with open(path, "rb") as sia_file:
            model = Model()
            Model.read_header(sia_file)

            read_u32(sia_file)  # Version maybe?

            model.name = read_string(sia_file)

            # So far these bytes have only been zero, changing them did nothing
            skip(sia_file, 12)

            # This might be some sort of scale, since it tends to resemble
            # another bouding box value. Maybe sphere radius
            read_f32(sia_file)

            model.bounding_box = BoundingBox.read_from_file(sia_file)

            num_objects = read_u32(sia_file)

            for _ in range(num_objects):
                mesh = Mesh()

                skip(sia_file, 4)
                mesh.num_vertices = read_u32(sia_file)

                skip(sia_file, 4)
                mesh.num_triangles = read_u32(sia_file)

                mesh.id = read_u32(sia_file)
                skip(sia_file, 8)

                model.meshes[mesh.id] = mesh

            num_meshes = read_u32(sia_file)
            skip(sia_file, 16)

            for i in range(num_meshes):
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

            return model


if __name__ == "__main__":
    model = Model.load(
        r"D:\football_manager_extracted\simatchviewer\mesh\jumbo_screen\jumbo_screen_02.sia")
    print(model.name)
    print(model.bounding_box.__dict__)
    for mesh in model.meshes.values():
        print(mesh.__dict__)
        for material in mesh.materials:
            print(material.__dict__)
            for texture in material.textures:
                print(texture.__dict__)
