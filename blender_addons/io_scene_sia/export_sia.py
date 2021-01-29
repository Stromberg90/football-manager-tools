import bpy
from struct import pack
import bmesh
import ntpath
import os
import sys
from collections import OrderedDict


def write_string(file, string):
    file.write(pack('<I', len(string)))
    file.write(bytes(string, "utf8"))


class VertWithUV(object):
    def __init__(self, vert, uv):
        self.inner_vert = vert
        self.uv = uv

# pub fn from_file(file: &mut File) -> Result<Model, SiaParseError> {
#     let mut model = Model::new();

#     read_header(file)?;

#     model.name = file.read_string()?;

#     // So far these bytes have only been zero, changing them did
#     // nothing
#     file.skip(12);

#     // This might be some sort of scale, since it tends to resemble
#     // another bouding box value.  Maybe sphere radius
#     file.read_f32::<LittleEndian>()?;

#     model.bounding_box = file.read_bounding_box();

#     model.objects_num = file.read_u32::<LittleEndian>()?;

#     for _ in 0..model.objects_num {
#         let mut mesh = Mesh::new();
#         file.skip(4); // What could this be?, when changing them away from zero's it either crashed or the mesh was invisible.

#         // Vertices
#         mesh.num_vertices = file.read_u32::<LittleEndian>()?;

#         file.skip(4); // What could this be?, when changing them away from zero's it crashed, I only tested once.

#         // Number of triangles when divided by 3
#         mesh.num_triangles = file.read_u32::<LittleEndian>()? / 3;

#         // ID
#         mesh.id = file.read_u32::<LittleEndian>()?;
#         file.skip(8); // All of these are set to 255, changing them to zero did crash the game.
#         model.meshes.insert(mesh.id as usize, mesh);
#     }

#     model.num_meshes = file.read_u32::<LittleEndian>()?;

#     file.skip(16); // After changing these to zero mesh is still there, but the lighting has changed, interesting.

#     for i in 0..model.num_meshes {
#         let mesh = model.meshes.get_mut(&(i as usize)).unwrap();
#         let material_kind = file.read_string()?;
#         let materials_num = file.read_u8()?;
#         for _ in 0..materials_num {
#             let mut material = Material::new();
#             material.kind = material_kind.to_owned();
#             material.name = file.read_string()?;
#             material.textures_num = file.read_u8()?;
#             for _ in 0..material.textures_num {
#                 let texture_id = file.read_u8()?;
#                 let texture = Texture::new(file.read_string()?, texture_id);
#                 material.textures.push(texture);
#             }
#             mesh.materials.push(material);
#         }
#         if i != model.num_meshes - 1 {
#             file.skip(80);
#         }
#     }

#     file.skip(64); // Changed all of these to 0, mesh still showed up and looked normal

#     let total_num_vertecies = file.read_u32::<LittleEndian>().unwrap();

#     let vertex_type = file.read_u32::<LittleEndian>()?;

#     for i in 0..model.num_meshes {
#         let mesh = model.meshes.get_mut(&(i as usize)).unwrap();

#         for _ in 0..mesh.num_vertices {
#             let pos = file.read_vector3();

#             // Think these are normals, when plotted out as vertices,
#             // they make a sphere.  Which makes sense if it's normals
#             // Actually, I'm second guessing myself
#             let normal = file.read_vector3();

#             let uv = match vertex_type {
#                 3 => Vector2::<f32>::new(0f32, 0f32),
#                 _ => file.read_vector2(),
#             };

#             // Thinking these are tangents or binormals, last one is
#             // always 1 or -1 Some of these probably use lightmaps and
#             // have 2 or more uv channels.
#             match vertex_type {
#                 3 => file.skip(0),
#                 7 => file.skip(0),
#                 39 => file.skip(16),
#                 47 => file.skip(24), // This might be a second uv set, 24 bytes matches with another set of uv's
#                 199 => file.skip(20),
#                 231 => file.skip(36),
#                 239 => file.skip(44),
#                 487 => file.skip(56),
#                 495 => file.skip(64),
#                 551 => file.skip(20),
#                 559 => file.skip(28),
#                 575 => file.skip(36),
#                 _ => return Err(SiaParseError::UnknownVertexType(vertex_type)),
#             }

#             mesh.vertices.push(Vertex {
#                 position: pos,
#                 uv,
#                 normals: normal,
#             })
#         }
#     }

#     let _number_of_triangles = file.read_u32::<LittleEndian>()? / 3;

#     for i in 0..model.num_meshes {
#         let mesh = model.meshes.get_mut(&(i as usize)).unwrap();
#         for _ in 0..mesh.num_triangles {
#             let triangle: Triangle<u32> = if total_num_vertecies > u16::MAX.into() {
#                 file.read_triangle()
#             } else {
#                 let triangle: Triangle<u16> = file.read_triangle();
#                 triangle.into()
#             };
#             if triangle.max() as usize > mesh.vertices.len() {
#                 return Err(SiaParseError::FaceVertexLenghtMismatch(
#                     triangle.max(),
#                     mesh.vertices.len(),
#                     file.position()?,
#                 ));
#             }
#             mesh.triangles.push(triangle);
#         }
#     }

#     // These two numbers seems to be related to how many bytes there
#     // are to read after, maybe bones or something?  But I've yet to
#     // find out exactly how they related to each other, it doesn't
#     // seem to be as simple as some_number * some other number
#     let some_number = file.read_u32::<LittleEndian>()?;
#     let some_number2 = file.read_u32::<LittleEndian>()?;
#     if some_number != 0 {
#         // println!("some_number: {}", some_number);
#     }
#     if some_number2 != 0 {
#         // println!("some_number2: {}", some_number2);
#     }

#     let num = file.read_u8()?;

#     if num == 75 || num == 215 {
#         file.skip(3);
#         file.skip((some_number2 * 56) as i64); // This seems wierd, and I wonder what data is hiding there.
#         file.skip(1);
#     }

#     match num {
#         0 | 215 => {}
#         42 | 75 => {
#             let kind = file.read_string_u8_len()?;
#             match kind.as_ref() {
#                 "mesh_type" => {
#                     let mesh_type: MeshType = file.read_u8().unwrap().into();
#                     match mesh_type {
#                         MeshType::VariableLength => {
#                             model.end_kind = Some(EndKind::MeshType(file.read_string()?));
#                         }
#                         MeshType::BodyPart => {
#                             model.end_kind =
#                                 Some(EndKind::MeshType(file.read_string_with_length(4)?));
#                         }
#                         MeshType::RearCap => {
#                             model.end_kind =
#                                 Some(EndKind::MeshType(file.read_string_with_length(8)?));
#                             let num_caps = file.read_u32::<LittleEndian>()?;
#                             for _ in 0..num_caps {
#                                 let cap_type = file.read_u32::<LittleEndian>()?;
#                                 file.skip(80); // This is probably position and such
#                                 let entries_num = file.read_u32::<LittleEndian>()?;
#                                 file.skip((entries_num * 48) as i64);
#                                 match cap_type {
#                                     0 => {
#                                         file.read_string()?;
#                                         file.read_string()?;
#                                     }
#                                     2 => {
#                                         file.read_string()?;
#                                         file.read_u32::<LittleEndian>()?;
#                                     }
#                                     9 => {
#                                         file.read_string()?;
#                                         file.read_u32::<LittleEndian>()?;
#                                     }
#                                     _ => {
#                                         return Err(SiaParseError::InvalidCapType(
#                                             cap_type,
#                                             file.position()?,
#                                         ))
#                                     }
#                                 }
#                             }

#                             read_file_end(file, num)?;

#                             return Ok(model);
#                         }
#                         MeshType::StadiumRoof => {
#                             model.end_kind =
#                                 Some(EndKind::MeshType(file.read_string_with_length(12)?));
#                         }
#                         MeshType::Glasses => {
#                             model.end_kind =
#                                 Some(EndKind::MeshType(file.read_string_with_length(7)?));
#                         }
#                         MeshType::PlayerTunnel => {
#                             model.end_kind =
#                                 Some(EndKind::MeshType(file.read_string_with_length(13)?));
#                         }
#                         MeshType::SideCap => {
#                             model.end_kind =
#                                 Some(EndKind::MeshType(file.read_string_with_length(14)?));
#                         }
#                         MeshType::Unknown => {
#                             return Err(SiaParseError::UnknownMeshType(
#                                 mesh_type as u8,
#                                 file.position()?,
#                             ))
#                         }
#                     }
#                 }
#                 "is_banner" => {
#                     model.end_kind = Some(EndKind::IsBanner(file.read_u8().unwrap() != 0));
#                 }
#                 "is_comp_banner" => {
#                     model.end_kind = Some(EndKind::IsBanner(file.read_u8().unwrap() != 0));
#                 }
#                 _ => return Err(SiaParseError::UnknownKindType(num, kind, file.position()?)),
#             }
#         }
#         _ => {
#             return Err(SiaParseError::UnknownType(num, file.position()?));
#         }
#     }

#     file.skip(4);

#     read_file_end(file, num)?;

#     Ok(model)
# }


def save(context, filepath):
    print(filepath)
    with open(filepath, "wb") as file:
        vertices = OrderedDict()
        me = bpy.context.object.data

        bm = bmesh.new()   # create an empty BMesh
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        me.calc_tangents()
        bm.from_mesh(me)

        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()

        min_x = sys.float_info.max
        min_y = sys.float_info.max
        min_z = sys.float_info.max

        max_x = sys.float_info.min
        max_y = sys.float_info.min
        max_z = sys.float_info.min

        uv_lay = bm.loops.layers.uv.active

        for face in bm.faces:
            for loop in face.loops:
                vert = loop.vert
                vertices[vert.index] = VertWithUV(vert, loop[uv_lay].uv)

                min_x = min(min_x, vert.co.x)
                min_y = min(min_y, vert.co.y)
                min_z = min(min_z, vert.co.z)

                max_x = max(max_x, vert.co.x)
                max_y = max(max_y, vert.co.y)
                max_z = max(max_z, vert.co.z)

        for index, vert in sorted(vertices.items()):
            print("Vertex Index: ", index)
            print("Vertex Position: (%f,%f,%f)" % vert.inner_vert.co[:])
            print("Vertex Normal: (%f,%f,%f)" % vert.inner_vert.normal[:])

            uv = vert.uv
            print("Vertex UV: %f, %f" % uv[:])

        # return {'FINISHED'}

        file.write(b"SHSM")
        # Is this the version?
        file.write(pack('<I', 35))

        filename = os.path.splitext(ntpath.basename(filepath))[0]
        write_string(file, filename)

        # So far these bytes have only been zero
        file.write(bytearray(12))

        # This might be some sort of scale, since it tends to resemble another bounding box value
        # changing it did nothing
        file.write(pack('<f', max_x))

        # model.bounding_box.min_x
        file.write(pack('<f', min_x))
        # model.bounding_box.min_y
        file.write(pack('<f', min_y))
        # model.bounding_box.min_z
        file.write(pack('<f', min_z))

        # model.bounding_box.max_x
        file.write(pack('<f', max_x))
        # model.bounding_box.max_y
        file.write(pack('<f', max_y))
        # model.bounding_box.max_z
        file.write(pack('<f', max_z))

        # model.objects_num
        file.write(pack('<I', 1))

        # So far has been 0's, when I changed it the mesh became invisible
        file.write(bytearray(4))

        # num_vertices
        file.write(pack('<I', len(vertices)))

        # Zero's, changing it made it invisible
        file.write(bytearray(4))

        # This diveded by 3 gives the amount of faces, like another set of bytes later on
        # I'm wondering if this is the total amount of faces, and the other one is per mesh
        # model.something_about_faces_or_vertices
        file.write(pack('<I', len(bm.faces) * 3))
        file.write(bytearray(4))  # Unknown
        # Unknown
        file.write(bytearray([255, 255, 255, 255, 255, 255, 255, 255]))

        # This needs to be moved into the mesh, then maybe when reading faces/vertices/materials one can match against it.
        # model.object_id
        file.write(pack('<I', 1))

        # Changing these did nothing
        file.write(bytearray(16))

        # model.num_meshes
        # file.write(pack('<I', 1))

        # Changing these did nothing
        # file.write(bytearray(16))

        for _ in range(0, 1):  # 0, num_meshes
            write_string(file, "ball")  # material name
            # materials_num
            file.write(pack('<B', 1))
            for _ in range(0, 1):  # 0, materials_num
                # I should figure out why this is "base" maybe it needs to be
                write_string(file, "base")
                file.write(pack('<B', 4))  # textures num
                for _ in range(0, 1):  # 0, textures num
                    # Maybe a way to identify which texture it is, like a id
                    file.write(pack('<B', 0))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[al]")

                    file.write(pack('<B', 1))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[ro]_[me]_[ao]")

                    file.write(pack('<B', 2))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[no]")

                    file.write(pack('<B', 5))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[ma]")

        # Not sure what these are
        file.write(bytearray(24))
        file.write(bytearray(24))
        file.write(bytearray(16))

        # Maybe this is for this mesh, and the earlier one is for the entire file.
        # local_num_vertecies
        file.write(pack('<I', len(vertices)))

        # Seems to be important for the mesh to show up
        file.write(pack('<I', 39))

        for index, vert in sorted(vertices.items()):
            file.write(pack('<f', vert.inner_vert.co.x))
            file.write(pack('<f', vert.inner_vert.co.y))
            file.write(pack('<f', vert.inner_vert.co.z))

            # Unsure if these are normals or not
            # I should find a simple object, like a flat plane and check to see
            # where the normals are, or whatever it might be
            # From checking again, I'm confident these are the normals, don't know what the others are.
            # file.write(bytearray(12))
            file.write(pack('<f', vert.inner_vert.normal.x))
            file.write(pack('<f', vert.inner_vert.normal.y))
            file.write(pack('<f', vert.inner_vert.normal.z))

            uv = vert.uv
            file.write(pack('<f', uv.x))
            file.write(pack('<f', uv.y))

            # Changed these, did nothing
            # Adding them did add shading to the mesh ingame
            # print(vert.inner_vert.tangent)
            # file.write(pack('<f', 10))
            # file.write(bytearray(8))
            # file.write(pack('<f', 0))
            # file.write(pack('<f', 0))
            # Last one is usually 1 or -1
            # file.write(pack('<f', 0))
            file.write(bytearray(16))

        # number of entries, so the triangle amount * 3
        file.write(pack('<I', len(bm.faces) * 3))
        for face in bm.faces:
            for loop in face.loops:
                vert = loop.vert
                file.write(pack('<H', vert.index))

        file.write(bytearray(13))

        file.write(b"EHSM")
        bm.free()
        return {'FINISHED'}

    return {'CANCELED'}
