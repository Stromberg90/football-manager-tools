use byteorder::{LittleEndian, ReadBytesExt};
use triangle::Triangle;

use std::fs::File;

use std::io::Read;
use std::path::Path;
use std::str;

mod bounding_box;
mod material;
mod mesh;
pub mod model;
mod stream_ext;
pub mod texture;
mod triangle;
mod vertex;

use material::Material;
use mesh::Mesh;
use model::{EndKind, Model};
use stream_ext::{ReadTriangle, StreamExt};
use texture::Texture;

use vertex::Vertex;

use nalgebra::Vector2;
use thiserror::Error;

enum MeshType {
    VariableLength,
    BodyPart,
    RearCap,
	Glasses,
    StadiumRoof,
	PlayerTunnel,
	SideCap,
    Unknown,
}

impl From<u8> for MeshType {
    fn from(value: u8) -> Self {
        match value {
            8 => Self::VariableLength,
            88 => Self::BodyPart,
            152 => Self::RearCap,
            136 => Self::Glasses,
            216 => Self::StadiumRoof,
            232 => Self::PlayerTunnel,
            248 => Self::SideCap,
            _ => Self::Unknown,
        }
    }
}

#[derive(Error, Debug)]
pub enum SiaParseError {
    #[error("Expexted header SHSM, but found {0}")]
    Header(String),
    #[error("Face index larger than available vertices\nFace Index: {0}\nVertices Length: {1}\n at file byte position: {2}")]
    FaceVertexLenghtMismatch(u32, usize, u64),
    #[error("{0} is a unknown vertex type")]
    UnknownVertexType(u32),
    #[error("{0} is a unknown type at file byte position: {1}")]
    UnknownType(u8, u64),
    #[error("{0} is a unknown mesh type at file byte position: {1}")]
    UnknownMeshType(u8, u64),
    #[error("{0} is a unknown kind = {1} type at file byte position: {2}")]
    UnknownKindType(u8, String, u64),
    #[error("Expected EHSM, but found {0:#?} at file byte position: {1} num is {2}")]
    EndTagB([u8; 4], u64, u8),
    #[error("Expected EHSM, but found {0} at file byte position: {1} num is {2}")]
    EndTagS(String, u64, u8),
    #[error("{0} is a unknown cap type at file byte position: {1}")]
    InvalidCapType(u32, u64),
    #[error("{0} is a unknown cap type id at file byte position: {1}")]
    InvalidCapTypeId(u32, u64),
    #[error(transparent)]
    File(#[from] std::io::Error),
    #[error(transparent)]
    Utf8(#[from] std::str::Utf8Error),
}

fn read_header(file: &mut File) -> Result<(), SiaParseError> {
    let mut begin_file_tag = [0u8; 4];
    file.read_exact(&mut begin_file_tag)?;
    let begin_file_tag = str::from_utf8(&begin_file_tag)?;
    if begin_file_tag != "SHSM" {
        return Err(SiaParseError::Header(begin_file_tag.into()));
    }
    Ok(())
}

fn read_file_end(file: &mut File, num: u8) -> Result<(), SiaParseError> {
    let mut end_file_tag = [0u8; 4];
    file.read_exact(&mut end_file_tag)?;

    match str::from_utf8(&end_file_tag) {
        Ok(s) => {
            if s != "EHSM" {
                let mut replaced_invalid_utf8 = String::new();
                for c in s.chars() {
                    if c.is_alphanumeric() {
                        replaced_invalid_utf8.push(c);
                    } else {
                        replaced_invalid_utf8.push('.');
                    }
                }
                return Err(SiaParseError::EndTagS(
                    replaced_invalid_utf8.into(),
                    file.position()?,
                    num,
                ));
            }
        }
        Err(_) => {
            return Err(SiaParseError::EndTagS(
                "invalid utf-8".into(),
                file.position()?,
                num,
            ));
        }
    }
    Ok(())
}

pub fn from_path<P: AsRef<Path>>(filepath: P) -> Result<Model, SiaParseError> {
    let mut file = File::open(&filepath)?;
    from_file(&mut file)
}

pub fn from_file(file: &mut File) -> Result<Model, SiaParseError> {
    let mut model = Model::new();

    read_header(file)?;

    model.maybe_version = file.read_u32::<LittleEndian>()?;

    model.name = file.read_string()?;

    // So far these bytes have only been zero, changing them did
    // nothing
    file.skip(12);

    // This might be some sort of scale, since it tends to resemble
    // another bouding box value.  Maybe sphere radius
    model.who_knows = file.read_f32::<LittleEndian>()?;

    model.bounding_box = file.read_bounding_box();

    model.objects_num = file.read_u32::<LittleEndian>()?;

    for _ in 0..model.objects_num {
        let mut mesh = Mesh::new();
        file.skip(4); // What could this be?, when changing them away from zero's it either crashed or the mesh was invisible.

        // Vertices
        mesh.num_vertices = file.read_u32::<LittleEndian>()?;

        file.skip(4); // What could this be?, when changing them away from zero's it crashed I only tested once.

        // Number of triangles when divided by 3
        mesh.num_triangles = file.read_u32::<LittleEndian>()? / 3;

        // ID
        mesh.id = file.read_u32::<LittleEndian>()?;
        file.skip(8); // All of these are set to 255, changing them to zero did crash the game.
        model.meshes.insert(mesh.id as usize, mesh);
    }

    model.num_meshes = file.read_u32::<LittleEndian>()?;

    file.skip(16); // After changing these to zero mesh is still there, but the lighting has changed, interesting.

    for i in 0..model.num_meshes {
        let mut mesh = model.meshes.get_mut(&(i as usize)).unwrap();
        let material_kind = file.read_string()?;
        mesh.materials_num = file.read_u8()?;
        for _ in 0..mesh.materials_num {
            let mut material = Material::new();
            material.kind = material_kind.to_owned();
            material.name = file.read_string()?;
            material.textures_num = file.read_u8()?;
            for _ in 0..material.textures_num {
                let texture_id = file.read_u8()?;
                let texture = Texture::new(file.read_string()?, texture_id);
                material.textures.push(texture);
            }
            mesh.materials.push(material);
        }
        if i != model.num_meshes - 1 {
            file.skip(80);
        }
    }

    file.skip(64); // Changed all of these to 0, mesh still showed up and looked normal

    let total_num_vertecies = file.read_u32::<LittleEndian>().unwrap();

    let vertex_type = file.read_u32::<LittleEndian>()?;

    for i in 0..model.num_meshes {
        let mesh = model.meshes.get_mut(&(i as usize)).unwrap();

        for _ in 0..mesh.num_vertices {
            let pos = file.read_vector3();

            // Think these are normals, when plotted out as vertices,
            // they make a sphere.  Which makes sense if it's normals
            // Actually, I'm second guessing myself
            let normal = file.read_vector3();

            let uv = match vertex_type {
                3 => Vector2::<f32>::new(0f32, 0f32),
                _ => file.read_vector2(),
            };

            // Thinking these are tangents or binormals, last one is
            // always 1 or -1 Some of these probably use lightmaps and
            // have 2 or more uv channels.
            match vertex_type {
                3 => file.skip(0),
                7 => file.skip(0),
                39 => file.skip(16),
                47 => file.skip(24), // This might be a second uv set, 24 bytes matches with another set of uv's
                199 => file.skip(20),
                231 => file.skip(36),
                239 => file.skip(44),
                487 => file.skip(56),
                495 => file.skip(64),
                551 => file.skip(20),
                559 => file.skip(28),
                575 => file.skip(36),
                _ => return Err(SiaParseError::UnknownVertexType(vertex_type)),
            }

            mesh.vertices.push(Vertex {
                position: pos,
                uv,
                normals: normal,
            })
        }
    }

    let _number_of_triangles = file.read_u32::<LittleEndian>()? / 3;

    for i in 0..model.num_meshes {
        let mesh = model.meshes.get_mut(&(i as usize)).unwrap();
        for _ in 0..mesh.num_triangles {
            let triangle: Triangle<u32> = if total_num_vertecies > u16::MAX.into() {
                file.read_triangle()
            } else {
                let triangle: Triangle<u16> = file.read_triangle();
                triangle.into()
            };
            if triangle.max() as usize > mesh.vertices.len() {
                return Err(SiaParseError::FaceVertexLenghtMismatch(
                    triangle.max(),
                    mesh.vertices.len(),
                    file.position()?,
                ));
            }
            mesh.triangles.push(triangle);
        }
    }

    // These two numbers seems to be related to how many bytes there
    // are to read after, maybe bones or something?  But I've yet to
    // find out exactly how they related to each other, it doesn't
    // seem to be as simple as some_number * some other number
    let some_number = file.read_u32::<LittleEndian>()?;
    let some_number2 = file.read_u32::<LittleEndian>()?;
    if some_number != 0 {
        // println!("some_number: {}", some_number);
    }
    if some_number2 != 0 {
        // println!("some_number2: {}", some_number2);
    }

    let num = file.read_u8()?;

    if num == 75 || num == 215 {
        file.skip(3);
        file.skip((some_number2 * 56) as i64); // This seems wierd, and I wonder what data is hiding there.
        file.skip(1);
    }

    match num {
        0 | 215 => {}
        42 | 75 => {
            let kind = file.read_string_u8_len()?;
            match kind.as_ref() {
                "mesh_type" => {
                    let mesh_type: MeshType = file.read_u8().unwrap().into();
                    match mesh_type {
                        MeshType::VariableLength => {
                            model.end_kind = Some(EndKind::MeshType(file.read_string()?));
                        }
                        MeshType::BodyPart => {
                            model.end_kind =
                                Some(EndKind::MeshType(file.read_string_with_length(4)?));
                        }
                        MeshType::RearCap => {
                            model.end_kind =
                                Some(EndKind::MeshType(file.read_string_with_length(8)?));
                            let num_caps = file.read_u32::<LittleEndian>()?;
                            for _ in 0..num_caps {
                                let cap_type = file.read_u32::<LittleEndian>()?;
                                file.skip(80); // This is probably position and such
                                let entries_num = file.read_u32::<LittleEndian>()?;
                                file.skip((entries_num * 48) as i64);
                                match cap_type {
                                    0 => {
                                        file.read_string()?;
                                        file.read_string()?;
                                    }
                                    2 => {
                                        file.read_string()?;
                                        file.read_u32::<LittleEndian>()?;
                                    }
                                    9 => {
                                        file.read_string()?;
                                        file.read_u32::<LittleEndian>()?;
                                    }
                                    _ => {
                                        return Err(SiaParseError::InvalidCapType(
                                            cap_type,
                                            file.position()?,
                                        ))
                                    }
                                }
                            }

                            read_file_end(file, num)?;

                            return Ok(model);
                        }
                        MeshType::StadiumRoof => {
                            model.end_kind =
                                Some(EndKind::MeshType(file.read_string_with_length(12)?));
                        }
                        MeshType::Glasses => {
                            model.end_kind =
                                Some(EndKind::MeshType(file.read_string_with_length(7)?));
                        }
                        MeshType::PlayerTunnel => {
                            model.end_kind =
                                Some(EndKind::MeshType(file.read_string_with_length(13)?));
						}
                        MeshType::SideCap => {
                            model.end_kind =
                                Some(EndKind::MeshType(file.read_string_with_length(14)?));
						}
                        MeshType::Unknown => {
                            return Err(SiaParseError::UnknownMeshType(
                                mesh_type as u8,
                                file.position()?,
                            ))
                        }
                    }
                }
                "is_banner" => {
                    model.end_kind = Some(EndKind::IsBanner(file.read_u8().unwrap() != 0));
                }
                "is_comp_banner" => {
                    model.end_kind = Some(EndKind::IsBanner(file.read_u8().unwrap() != 0));
                }
                _ => return Err(SiaParseError::UnknownKindType(num, kind, file.position()?)),
            }
        }
        _ => {
            return Err(SiaParseError::UnknownType(num, file.position()?));
        }
    }

    file.skip(4);

    read_file_end(file, num)?;

    Ok(model)
}
