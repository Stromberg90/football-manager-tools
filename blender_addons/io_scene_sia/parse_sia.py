from io import BufferedReader
import os
import pprint
from . import data_types
from . import read_utils

pp = pprint.PrettyPrinter(indent=4)


class SiaParseError(Exception):
    pass


def read_header(sia_file: BufferedReader):
    header = sia_file.read(4)
    if header != b"SHSM":
        raise SiaParseError(
            "Expexted header SHSM, but found {!r}".format(header))


def read_file_end(sia_file: BufferedReader, num: int):
    end = sia_file.read(4)
    if end != b"EHSM":
        raise SiaParseError(
            "Expected EHSM, but found {!r} at file byte position: {} num is {}".format(
                end, sia_file.tell(), num
            )
        )


def load(path: str):
    if not os.path.exists(path) or os.path.splitext(path)[1] != ".sia":
        raise SiaParseError(
            "{} does not exist or is not a valid sia file".format(path))

    with open(path, "rb") as sia_file:
        model = data_types.Model()
        read_header(sia_file)

        read_utils.u32(sia_file)  # Version maybe?

        model.name = read_utils.string(sia_file)

        # So far these bytes have only been zero, changing them did nothing
        read_utils.skip(sia_file, 12)

        # This might be some sort of scale, since it tends to resemble
        # another bouding box value. Maybe sphere radius, I had a look but not sure.
        read_utils.f32(sia_file)

        model.bounding_box = data_types.BoundingBox.read_from_file(
            sia_file)

        objects_num = read_utils.u32(sia_file)

        for _ in range(objects_num):
            mesh = data_types.Mesh()

            # vertex_offset
            read_utils.skip(sia_file, 4)

            mesh.vertices_num = read_utils.u32(sia_file)

            # triangle_offset
            read_utils.skip(sia_file, 4)
            # Number of triangles when divided by 3
            mesh.triangles_num = int(read_utils.u32(sia_file) / 3)

            mesh.id = read_utils.u32(sia_file)

            # Been full bytes when I've checked
            read_utils.skip(sia_file, 8)

            model.meshes.insert(mesh.id, mesh)

        meshes_num = read_utils.u32(sia_file)

        for i in range(meshes_num):
            # Find out what this is.
            # did read them as floats, made no sense.
            # almost seems to be a hash or something,
            # it looks like when the material name is the same, so is this byte sequence.
            read_utils.skip(sia_file, 4)

            # Only observed as zeros
            read_utils.skip(sia_file, 4)
            # Only observed as full bytes
            read_utils.skip(sia_file, 4)
            # Only observed as zeros
            read_utils.skip(sia_file, 4)

            mesh = model.meshes[i]
            assert mesh is not None
            material_name = read_utils.string(sia_file)
            materials_num = read_utils.u8(sia_file)

            # materials_num is more like material variations it seems.
            # max I've seen is 2 named static and degraded.
            for _ in range(materials_num):
                material = data_types.Material(
                    material_name, read_utils.string(sia_file)
                )
                texture_num = read_utils.u8(sia_file)
                for _ in range(texture_num):
                    texture = data_types.Texture(
                        data_types.TextureKind.from_u8(
                            read_utils.u8(sia_file)),
                        read_utils.string(sia_file),
                    )
                    material.textures.append(texture)

                mesh.materials.append(material)

            read_utils.skip(sia_file, 64)

        vertices_total_num = read_utils.u32(sia_file)

        # There seems to be only 10 bits checked, so maybe it's a u16 instead,
        # and the other 16 bits are something else
        # could any of these be vertex color?, cause that would be handy
        model.settings = data_types.Bitfield.from_number(
            read_utils.u32(sia_file))

        # Result so far:
        # 1 and 2 Always checked, normal and position I think
        # 3 I think this is uv, also always checked
        # 4 Read 8 bits
        # 5 Read 8 bits
        # 6 Read 16 bits
        # 7 and 8 Read Unsure, but 12 or 8 I think for either one
        # 9 20 Read bits
        # 10 Read 4 bits, seems strange

        for i in range(meshes_num):
            mesh = model.meshes[i]

            for _ in range(mesh.vertices_num):
                position, normal, uv = (None, None, None)
                if model.settings[0]:
                    position = data_types.read_vector3(sia_file)
                else:
                    raise SiaParseError("Missing position flag")
                if model.settings[1]:
                    normal = data_types.read_vector3(sia_file)
                else:
                    raise SiaParseError("Missing normal flag")
                if model.settings[2]:  # First uv set flag
                    uv = data_types.read_vector2(sia_file)
                else:
                    uv = data_types.Vector2(0, 0)
                if model.settings[3]:
                    # Lightmap uvs or just the second uv set used for more reasons.
                    lightmap_uv = data_types.read_vector2(sia_file)
                if model.settings[4]:
                    read_utils.skip(sia_file, 8)
                if model.settings[5]:
                    tangent = data_types.read_vector3(sia_file)
                    read_utils.skip(sia_file, 4)
                if model.settings[6]:
                    # Thought this or [7] could be second uv sets, but the data don't quite make sense for that.
                    read_utils.skip(sia_file, 12)
                    # seems like 6 and 7 are checked together, so one can read the bytes interchangeably.
                if model.settings[7]:
                    read_utils.skip(sia_file, 8)
                if model.settings[8]:
                    # Printed these as floats, they where very small values(pretty much 0), so unsure what this could be.
                    read_utils.skip(sia_file, 20)
                if model.settings[9]:
                    # Don't know when this is set, but it only happens in some files.
                    # most of the time it seems to be a 255 byte, but I have seen others as well.
                    # can it be vertex color?
                    # one byte per color plus alpha
                    read_utils.skip(sia_file, 4)

                mesh.vertices.append(
                    data_types.Vertex(position, normal, uv))

        # This is how many indecies there is,
        number_of_triangles = int(read_utils.u32(sia_file) / 3)
        # then it reads through those, maybe something to consider changing in mine.
        for i in range(meshes_num):
            mesh = model.meshes[i]
            for _ in range(mesh.triangles_num):
                if vertices_total_num > 65535:
                    triangle = data_types.Triangle.read_u32(sia_file)
                else:
                    triangle = data_types.Triangle.read_u16(sia_file)

                if triangle.max() > len(mesh.vertices) - 1:
                    raise SiaParseError(
                        "Face index larger than available vertices\nFace Index: {}\nVertices Length: {}\n at file byte position: {}".format(
                            triangle.max(), len(mesh.vertices), sia_file.tell()
                        )
                    )

                mesh.triangles.append(triangle)

        # These two numbers seems to be related to how many bytes there
        # are to read after, maybe bones or something?  But I've yet to
        # find out exactly how they related to each other, it doesn't
        # seem to be as simple as some_number * some other number

        # this is my best guess for now
        is_skinned = read_utils.u32(sia_file) == 1
        # this is my best guess for now
        number_of_bones = read_utils.u32(sia_file)

        # Could be a bit field, not sure, but makes more sense than magic number
        # maybe a bit that says if it is a mesh_type of not.
        num = None
        if is_skinned:
            # This seems wierd, and I wonder what data is hiding there.
            read_utils.skip(sia_file, 4)
            read_utils.skip(sia_file, (number_of_bones * 56))
            num = read_utils.u8(sia_file)
        else:
            num = read_utils.u8(sia_file)

        if num == 2:
            read_utils.skip(sia_file, 16)
        elif num == 42:
            kind = read_utils.string_u8_len(sia_file)
            if kind == b"mesh_type":
                mesh_type = data_types.MeshType.from_u8(
                    read_utils.u8(sia_file))
                if mesh_type == data_types.MeshType.VariableLength:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string(sia_file)
                    )
                elif mesh_type == data_types.MeshType.RenderFlags:
                    read_utils.skip(sia_file, 4)
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_u8_len(sia_file)
                    )
                    read_utils.skip(sia_file, 5)
                    read_file_end(sia_file, num)
                    return model
                elif mesh_type == data_types.MeshType.BodyPart:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 4)
                    )
                elif mesh_type == data_types.MeshType.RearCap:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 8)
                    )
                    num_caps = read_utils.u32(sia_file)
                    for _ in range(num_caps):
                        cap_type = read_utils.u32(sia_file)
                        read_utils.skip(sia_file, 80)
                        # This is probably position and such
                        entries_num = read_utils.u32(sia_file)
                        read_utils.skip(
                            sia_file, int(entries_num * 48))
                        if cap_type == 0:
                            read_utils.string(sia_file)
                            read_utils.string(sia_file)
                        # TODO: Why are these are the same?
                        elif cap_type == 2:
                            read_utils.string(sia_file)
                            read_utils.u32(sia_file)
                        elif cap_type == 9:
                            read_utils.string(sia_file)
                            read_utils.u32(sia_file)
                        elif cap_type == 10:
                            read_utils.string(sia_file)
                            read_utils.u32(sia_file)
                        else:
                            raise SiaParseError(
                                "{} is a unknown cap type at file byte position: {}".format(
                                    cap_type, sia_file.tell()
                                )
                            )

                    read_file_end(sia_file, num)

                    return model
                elif mesh_type == data_types.MeshType.StadiumRoof:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 12)
                    )
                elif mesh_type == data_types.MeshType.Glasses:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 7)
                    )
                elif mesh_type == data_types.MeshType.PlayerTunnel:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 13)
                    )
                elif mesh_type == data_types.MeshType.SideCap:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 14)
                    )
                elif mesh_type == data_types.MeshType.Unknown:
                    raise SiaParseError(
                        "{} is a unknown mesh type at file byte position: {}".format(
                            mesh_type, sia_file.tell()
                        )
                    )
            elif kind == b"is_banner":
                model.end_kind = data_types.EndKind.IsBanner(
                    read_utils.u8(sia_file) != 0
                )
            elif kind == b"is_comp_banner":
                model.end_kind = data_types.EndKind.IsCompBanner(
                    read_utils.u8(sia_file) != 0
                )
            elif kind == b"is_match_ball":
                model.end_kind = data_types.EndKind.IsMatchBall(
                    read_utils.u8(sia_file) != 0
                )
            elif kind == b"is_team_logo":
                model.end_kind = data_types.EndKind.IsTeamLogo(
                    read_utils.u8(sia_file) != 0
                )
            else:
                raise SiaParseError(
                    "{} is a unknown kind = {} type at file byte position: {}".format(
                        num, kind, sia_file.tell()
                    )
                )
        elif num == None:
            raise SiaParseError(
                "{} type is None at position: {}".format(
                    num, sia_file.tell()
                )
            )
        else:
            pass

        instances = read_utils.u32(sia_file)
        for i in range(0, instances):
            # not sure what this means.
            instance_type = read_utils.u32(sia_file)
            # Side to side, no idea if X or not.
            x = read_utils.f32(sia_file)
            # Back and forwards, no idea if Z or not.
            z = read_utils.f32(sia_file)
            y = read_utils.f32(sia_file)  # Up and down
            read_utils.skip(
                sia_file, 40
            )  # From trying out different values I think this is a Transformation matrix
            # and it matches with 40 bytes I think
            read_utils.skip(
                sia_file, 28
            )  # This data seems separate from the previous one
            num1 = read_utils.u32(sia_file)
            for _ in range(0, num1):
                # Possibly mesh data
                read_utils.skip(sia_file, 48)
            name = read_utils.string(sia_file)
            path = read_utils.string(sia_file)

        read_file_end(sia_file, num)

        return model
