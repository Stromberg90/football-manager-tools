import os
import pprint
import mathutils
import math
from io import BufferedReader

from . import data_types, read_utils

pp = pprint.PrettyPrinter(indent=4)


class SiaParseError(Exception):
    pass


def read_header(sia_file: BufferedReader):
    header = sia_file.read(4)
    if header != b"SHSM":
        raise SiaParseError("Expexted header SHSM, but found {!r}".format(header))


def read_file_end(sia_file: BufferedReader, num: int):
    end = sia_file.read(4)
    if end != b"EHSM":
        raise SiaParseError(
            "Expected EHSM, but found {!r} at file byte position: {} num is {}".format(
                end, sia_file.tell(), num
            )
        )


def read_bones(sia_file: BufferedReader, number_of_bones: int):
    # I think this is the "hash" of the rootbone
    read_utils.u8_array(sia_file, 4)

    # print("bones")
    # print("Bones at: {}".format(sia_file.tell()))
    for _ in range(number_of_bones):
        # These are floats with weights and such
        read_utils.skip(sia_file, 56)


def read_end_kind(sia_file: BufferedReader, num: int):
    kind = read_utils.string_u8_len(sia_file)
    if kind == b"mesh_type":
        mesh_type = data_types.MeshType.from_u8(read_utils.u8(sia_file))
        if mesh_type == data_types.MeshType.VariableLength:
            return data_types.EndKind.MeshType(read_utils.string(sia_file))
        elif mesh_type == data_types.MeshType.RenderFlags:
            read_utils.skip(sia_file, 4)
            return data_types.EndKind.MeshType(read_utils.string_u8_len(sia_file))
        elif mesh_type == data_types.MeshType.BodyPart:
            return data_types.EndKind.MeshType(
                read_utils.string_with_length(sia_file, 4)
            )
        elif mesh_type == data_types.MeshType.RearCap:
            return data_types.EndKind.MeshType(
                read_utils.string_with_length(sia_file, 8)
            )
        elif mesh_type == data_types.MeshType.StadiumRoof:
            return data_types.EndKind.MeshType(
                read_utils.string_with_length(sia_file, 12)
            )
        elif mesh_type == data_types.MeshType.Glasses:
            return data_types.EndKind.MeshType(
                read_utils.string_with_length(sia_file, 7)
            )
        elif mesh_type == data_types.MeshType.PlayerTunnel:
            return data_types.EndKind.MeshType(
                read_utils.string_with_length(sia_file, 13)
            )
        elif mesh_type == data_types.MeshType.SideCap:
            return data_types.EndKind.MeshType(
                read_utils.string_with_length(sia_file, 14)
            )
        elif mesh_type == data_types.MeshType.Unknown:
            raise SiaParseError(
                "{} is a unknown mesh type at file byte position: {}".format(
                    mesh_type, sia_file.tell()
                )
            )
    elif kind == b"is_banner":
        return data_types.EndKind.IsBanner(read_utils.u8(sia_file) != 0)
    elif kind == b"is_comp_banner":
        return data_types.EndKind.IsCompBanner(read_utils.u8(sia_file) != 0)
    elif kind == b"is_match_ball":
        return data_types.EndKind.IsMatchBall(read_utils.u8(sia_file) != 0)
    elif kind == b"is_team_logo":
        return data_types.EndKind.IsTeamLogo(read_utils.u8(sia_file) != 0)
    else:
        raise SiaParseError(
            "{} is a unknown kind = {} type at file byte position: {}".format(
                num, kind, sia_file.tell()
            )
        )


def read_instance(sia_file) -> data_types.Instance:
    instance = data_types.Instance()

    instance.kind = read_utils.u32(sia_file)

    matrix = mathutils.Matrix.Identity(4)
    matrix[0][3] = read_utils.f32(sia_file)
    matrix[1][3] = read_utils.f32(sia_file)
    matrix[2][3] = read_utils.f32(sia_file)
    matrix[3][3] = read_utils.f32(sia_file)

    matrix[0][0] = read_utils.f32(sia_file)
    matrix[1][0] = read_utils.f32(sia_file)
    matrix[2][0] = read_utils.f32(sia_file)

    matrix[0][1] = read_utils.f32(sia_file)
    matrix[1][1] = read_utils.f32(sia_file)
    matrix[2][1] = read_utils.f32(sia_file)

    matrix[0][2] = read_utils.f32(sia_file)
    matrix[1][2] = read_utils.f32(sia_file)
    matrix[2][2] = read_utils.f32(sia_file)
    matrix[3][2] = read_utils.f32(sia_file)

    (loc, rot, scale) = matrix.decompose()
    position = data_types.Vector3(loc.x, loc.y, loc.z)
    rotation = data_types.Vector3(rot.to_euler().x, rot.to_euler().y, rot.to_euler().z)
    scale = data_types.Vector3(scale.x, scale.y, scale.z)
    instance.transform = data_types.Transform(position, rotation, scale)

    # I don't know what these are but they seem to share the same values often
    read_utils.skip(sia_file, (4 * 6))

    num1 = read_utils.u32(sia_file)
    for _ in range(0, num1):
        for _ in range(0, 4):
            x = read_utils.f32(sia_file)
            y = read_utils.f32(sia_file)
            z = read_utils.f32(sia_file)
            instance.positions.append(data_types.Vector3(x, y, z))

    instance.name = read_utils.string(sia_file)
    instance.path = read_utils.string(sia_file)
    return instance


def load(path: str):
    if not os.path.exists(path) or os.path.splitext(path)[1] != ".sia":
        raise SiaParseError("{} does not exist or is not a valid sia file".format(path))

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

        model.bounding_box = data_types.BoundingBox.read_from_file(sia_file)

        objects_num = read_utils.u32(sia_file)

        for _ in range(objects_num):
            mesh = data_types.Mesh()

            read_utils.skip(sia_file, 4)
            mesh.vertices_num = read_utils.u32(sia_file)

            read_utils.skip(sia_file, 4)
            # Number of triangles when divided by 3
            mesh.triangles_num = int(read_utils.u32(sia_file) / 3)

            mesh.id = read_utils.u32(sia_file)

            # Been full bytes when I've checked
            read_utils.skip(sia_file, 8)

            model.meshes.insert(mesh.id, mesh)

        meshes_num = read_utils.u32(sia_file)

        for mesh_index in range(meshes_num):
            # Find out what this is.
            # did read them as floats, made no sense.
            # almost seems to be a hash or something,
            # it looks like when the material name is the same, so is this byte sequence.
            # bits = '{0:08b}'.format(read_utils.u32(sia_file))
            read_utils.skip(sia_file, 4)

            # Only observed as zeros
            read_utils.skip(sia_file, 4)
            # Only observed as full bytes
            read_utils.skip(sia_file, 4)
            # Only observed as zeros
            read_utils.skip(sia_file, 4)

            mesh = model.meshes[mesh_index]
            assert mesh is not None
            material_kind = read_utils.string(sia_file)
            materials_num = read_utils.u8(sia_file)

            # materials_num is more like material variations it seems.
            # max I've seen is 2, type static and degraded.
            # I think degraded is more like a flag, which if it has one it will replace "new" in the texture name
            # with "old" and use that texture
            for _ in range(materials_num):
                material = data_types.Material(
                    read_utils.string(sia_file), material_kind
                )
                texture_num = read_utils.u8(sia_file)
                for _ in range(texture_num):
                    texture = data_types.Texture(
                        data_types.TextureKind.from_u8(read_utils.u8(sia_file)),
                        read_utils.string(sia_file),
                    )
                    material.textures.append(texture)

                mesh.materials.append(material)

            # I've changed these every which way, and not seen a visual difference
            read_utils.skip(sia_file, 64)

        vertices_total_num = read_utils.u32(sia_file)

        # There seems to be only 10 bits checked, so maybe it's a u16 instead,
        # and the other 16 bits are something else
        # could any of these be vertex color?, cause that would be handy
        model.vertex_flags = data_types.VertexFlags.from_number(
            read_utils.u32(sia_file)
        )

        for mesh in model.meshes:
            for _ in range(mesh.vertices_num):
                texture_coords = []
                position, normal = (None, None)
                if model.vertex_flags.position:
                    position = data_types.read_vector3(sia_file)
                else:
                    raise SiaParseError("Missing position flag")
                if model.vertex_flags.normal:
                    normal = data_types.read_vector3(sia_file)
                else:
                    raise SiaParseError("Missing normal flag")
                if model.vertex_flags.uv_set1:  # First uv set flag
                    texture_coords.append(data_types.read_vector2(sia_file))
                else:
                    texture_coords.append(data_types.Vector2(0, 0))
                if model.vertex_flags.uv_set2:
                    # Lightmap uvs or just the second uv set used for more reasons.
                    texture_coords.append(data_types.read_vector2(sia_file))
                if model.vertex_flags.unknown:
                    # print("model.settings[4]: ", read_utils.u8_array(sia_file, 8))
                    read_utils.skip(sia_file, 8)
                if model.vertex_flags.tangent:
                    # This is what the shader documentation says
                    # // tangent + uv winding for binormal direction
                    #
                    data_types.read_vector3(sia_file)
                    read_utils.skip(sia_file, 4)
                if model.vertex_flags.skin:
                    # I think this is data about what bone it is skinned to and such
                    # I wonder if there are a max of 4 bone influences, so there are 4 u8s telling what bone they're skinned to.
                    for bone_n in range(4):
                        # print(
                        #     "vertex bone influence ",
                        #     bone_n,
                        #     " is bone: ",
                        read_utils.u8(sia_file)
                        # ,
                        # )
                    for bone_n in range(4):
                        # print(
                        #     "vertex bone influence ",
                        #     bone_n,
                        #     " amount is ",
                        read_utils.f32(sia_file)
                        # ,
                        # )
                if model.vertex_flags.unknown2:
                    # Seems to be lacking any info?
                    pass
                if model.vertex_flags.unknown3:
                    # Printed these as floats, they where very small values(pretty much 0), so unsure what this could be.
                    # print("model.settings[8]: ", read_utils.u8_array(sia_file, 20))
                    # Only used on manager files
                    read_utils.skip(sia_file, 20)
                if model.vertex_flags.unknown4:
                    # Don't know when this is set, but it only happens in some files.
                    # most of the time it seems to be a 255 byte, but I have seen others as well.
                    # can it be vertex color?
                    # one byte per color plus alpha
                    # print("model.settings[9]: ", read_utils.u8_array(sia_file, 4))
                    # Only used on stadium pieces
                    read_utils.skip(sia_file, 4)

                mesh.vertices.append(
                    data_types.Vertex(position, normal, texture_coords)
                )

        # This is how many indecies there is,
        _number_of_triangles = int(read_utils.u32(sia_file) / 3)
        for mesh in model.meshes:
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

        is_skinned = read_utils.u32(sia_file) == 1
        number_of_bones = read_utils.u32(sia_file)

        # Could be a bit field, not sure, but makes more sense than magic number
        # maybe a bit that says if it is a mesh_type of not.
        # print("Is skinned: ", is_skinned)
        if is_skinned:
            # print("Number of bones: ", number_of_bones)
            read_bones(sia_file, number_of_bones)

        num = read_utils.u8(sia_file)

        if num == 2:
            read_utils.skip(sia_file, 16)
        elif num == 42:
            model.end_kind = read_end_kind(sia_file, num)
        elif num is None:
            raise SiaParseError(
                "{} type is None at position: {}".format(num, sia_file.tell())
            )

        number_of_instances = read_utils.u32(sia_file)
        for _ in range(0, number_of_instances):
            instance = read_instance(sia_file)
            model.instances.append(instance)

        read_file_end(sia_file, num)

        return model
