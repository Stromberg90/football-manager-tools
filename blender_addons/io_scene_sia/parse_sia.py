from io import BufferedReader
import os
from . import data_types
from . import read_utils

class SiaParseError(Exception):
    pass


def read_header(sia_file: BufferedReader):
    header = sia_file.read(4)
    if header != b'SHSM':
        raise SiaParseError(
            "Expexted header SHSM, but found {}".format(header))


def read_file_end(sia_file: BufferedReader, num: int):
    end = sia_file.read(4)
    if end != b'EHSM':
        raise SiaParseError(
            "Expected EHSM, but found {} at file byte position: {} num is {}".format(
                end, sia_file.tell(), num))


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

        model.bounding_box = data_types.BoundingBox.read_from_file(sia_file)

        objects_num = read_utils.u32(sia_file)

        for _ in range(objects_num):
            mesh = data_types.Mesh()

            read_utils.skip(sia_file, 4)  # Been 0 when I've looked
            mesh.vertices_num = read_utils.u32(sia_file)

            read_utils.skip(sia_file, 4)  # Been 0 when I've looked
            # Number of triangles when divided by 3
            mesh.triangles_num = int(read_utils.u32(sia_file) / 3)

            mesh.id = read_utils.u32(sia_file)
            read_utils.skip(sia_file, 8)

            model.meshes[mesh.id] = mesh

        meshes_num = read_utils.u32(sia_file)
        # After changing these to zero mesh is still there,
        # but the lighting has changed, interesting.
        # well, when exporting my own mesh, having these at 0 made it crash.
        read_utils.skip(sia_file, 16)

        for i in range(meshes_num):
            mesh = model.meshes.get(i)
            assert(mesh is not None)
            material_name = read_utils.string(sia_file)
            materials_num = read_utils.u8(sia_file)
            for _ in range(materials_num):
                material = data_types.Material(
                    material_name,
                    read_utils.string(sia_file)
                )
                texture_num = read_utils.u8(sia_file)
                for _ in range(texture_num):
                    texture = data_types.Texture(
                        read_utils.u8(sia_file),
                        read_utils.string(sia_file)
                    )
                    material.textures.append(texture)

                mesh.materials.append(material)

            if i != meshes_num - 1:
                read_utils.skip(sia_file, 80)

        # Changed all of these to 0, mesh still showed up and looked normal
        read_utils.skip(sia_file, 64)

        vertices_total_num = read_utils.u32(sia_file)

        # There seems to be only 10 bits checked, so maybe it's a u16 instead,
        # and the other 16 bits are something else
        # could any of these be vertex color?, cause that would be handy
        model.settings = data_types.Bitfield.from_number(read_utils.u32(sia_file))

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
            mesh = model.meshes.get(i)

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
                    read_utils.skip(sia_file, 8)

                if model.settings[4]:
                    read_utils.skip(sia_file, 8)

                if model.settings[5]:
                    read_utils.skip(sia_file, 16)
                    
                if model.settings[6]:
                    read_utils.skip(sia_file, 8)
                    # |---> These two are probably not correct
                    
                if model.settings[7]:
                    read_utils.skip(sia_file, 12)
                    
                if model.settings[8]:
                    read_utils.skip(sia_file, 20)
                    
                if model.settings[9]:
                    read_utils.skip(sia_file, 4)

                mesh.vertices.append(data_types.Vertex(position, normal, uv))

        # This is how many indecies there is,
        number_of_triangles = int(read_utils.u32(sia_file) / 3)
        # then it reads through those, maybe something to consider changing in mine.
        for i in range(meshes_num):
            mesh = model.meshes.get(i)
            for _ in range(mesh.triangles_num):
                if vertices_total_num > 65535:
                    triangle = data_types.Triangle.read_u32(sia_file)
                else:
                    triangle = data_types.Triangle.read_u16(sia_file)

                if triangle.max() > len(mesh.vertices) - 1:
                    raise SiaParseError(
                        "Face index larger than available vertices\nFace Index: {}\nVertices Length: {}\n at file byte position: {}".format(triangle.max(), len(mesh.vertices), sia_file.tell()))

                mesh.triangles.append(triangle)

        # These two numbers seems to be related to how many bytes there
        # are to read after, maybe bones or something?  But I've yet to
        # find out exactly how they related to each other, it doesn't
        # seem to be as simple as some_number * some other number
        some_number = read_utils.u32(sia_file)
        some_number2 = read_utils.u32(sia_file)

        # Could be a bit field, not sure, but makes more sense than magic number
        # probably a bit that says if it is a mesh_type of not.
        num = read_utils.u8(sia_file)
        num2 = 0
        if num == 75 or num == 215 or num == 10 or num == 212 or num == 255 or num == 34 or num == 221 or num == 114 or num == 70 or num == 198 or num == 40 or num == 104 or num == 220 or num == 252 or num == 87 or num == 102 or num == 129 or num == 183 or num == 216 or num == 223 or num == 225 or num == 233 or num == 245 or num == 254 or num == 5:
            # This seems wierd, and I wonder what data is hiding there.
            read_utils.skip(sia_file, 3)
            read_utils.skip(sia_file, (some_number2 * 56))
            num2 = read_utils.u8(sia_file)

        # num did not immediately seem like a bitfield
        if num == 0 or num == 212 or num == 255 or num == 40 or num == 104 or num == 102 or num == 129 or num == 183 or num == 216 or num == 223:
            pass
        # TODO: These can be combined and concened a lot
        elif (num == 75 and num2 == 0) or (num == 225 and num2 == 0) or (num == 221 and num2 == 0) or (num == 114 and num2 == 0) or (num == 70 and num2 == 0) or (num == 245 and num2 == 0) or (num == 254 and num2 == 0) or (num == 215 and num2 == 0) or (num == 220 and num2 == 0) or (num == 198 and num2 == 0) or (num == 233 and num2 == 0) or (num == 252 and num2 == 0) or (num == 5 and num2 == 0) or (num == 87 and num2 == 0):
            pass
        elif (num == 114 and num2 != 0) or (num == 70 and num2 != 0) or (num == 254 and num2 != 0) or (num == 215 and num2 != 0) or (num == 220 and num2 != 0) or (num == 198 and num2 != 0) or (num == 233 and num2 != 0) or (num == 252 and num2 != 0) or (num == 5 and num2 != 0) or (num == 87 and num2 != 0) or (num == 221 and num2 == 2):
            read_utils.skip(sia_file, 16)
        elif num == 42 or num == 75 or num == 58 or num == 10 or num == 34 or (num == 225 and num2 != 0) or (num == 245 and num2 != 0) or (num == 221 and num2 == 42):
            kind = read_utils.string_u8_len(sia_file)
            if kind == b"mesh_type":
                mesh_type = data_types.MeshType.from_u8(read_utils.u8(sia_file))
                if mesh_type == data_types.MeshType.VariableLength:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string(sia_file))
                elif mesh_type == data_types.MeshType.RenderFlags:
                    read_utils.skip(sia_file, 4)
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_u8_len(sia_file))
                    read_utils.skip(sia_file, 5)
                    read_file_end(sia_file, num)
                    return model
                elif mesh_type == data_types.MeshType.BodyPart:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 4))
                elif mesh_type == data_types.MeshType.RearCap:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 8))
                    num_caps = read_utils.u32(sia_file)
                    for _ in range(num_caps):
                        cap_type = read_utils.u32(sia_file)
                        read_utils.skip(sia_file, 80)
                        # This is probably position and such
                        entries_num = read_utils.u32(sia_file)
                        read_utils.skip(sia_file, int(entries_num * 48))
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
                            raise SiaParseError("{} is a unknown cap type at file byte position: {}".format(
                                cap_type, sia_file.tell()))

                    read_file_end(sia_file, num)

                    return model
                elif mesh_type == data_types.MeshType.StadiumRoof:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 12))
                elif mesh_type == data_types.MeshType.Glasses:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 7))
                elif mesh_type == data_types.MeshType.PlayerTunnel:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 13))
                elif mesh_type == data_types.MeshType.SideCap:
                    model.end_kind = data_types.EndKind.MeshType(
                        read_utils.string_with_length(sia_file, 14))
                elif mesh_type == data_types.MeshType.Unknown:
                    raise SiaParseError("{} is a unknown mesh type at file byte position: {}".format(
                        mesh_type, sia_file.tell()))
            elif kind == b"is_banner":
                model.end_kind = data_types.EndKind.IsBanner(read_utils.u8(sia_file) != 0)
            elif kind == b"is_comp_banner":
                model.end_kind = data_types.EndKind.IsBanner(read_utils.u8(sia_file) != 0)
            else:
                raise SiaParseError(
                    "{} is a unknown kind = {} type at file byte position: {}".format(num, kind, sia_file.tell()))
        else:
            raise SiaParseError("{} is a unknown type at file byte position: {}".format(
                num, sia_file.tell()))

        instances = read_utils.u32(sia_file)
        for i in range(0, instances):
            instance_type = read_utils.u32(sia_file) # not sure what this means.
            x = read_utils.f32(sia_file) # Side to side, no idea if X or not.
            z = read_utils.f32(sia_file) # Back and forwards, no idea if Z or not.
            y = read_utils.f32(sia_file) # Up and down
            read_utils.skip(sia_file, 40) # From trying out different values I think this is a Transformation matrix
            # and it matches with 40 bytes I think
            read_utils.skip(sia_file, 28) # This data seems separate from the previous one
            num1 = read_utils.u32(sia_file)
            for _ in range(0, num1):
                # Possibly mesh data
                read_utils.skip(sia_file, 48)
            name = read_utils.string(sia_file)
            path = read_utils.string(sia_file)

        read_file_end(sia_file, num)

        return model
