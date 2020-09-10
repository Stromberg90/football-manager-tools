use byteorder::{LittleEndian, ReadBytesExt};
use triangle::Triangle;

use std::fs::File;

use std::io::Read;
use std::path::Path;
use std::str;

mod bounding_box;
mod material;
mod mesh;
mod model;
mod stream_ext;
pub mod texture;
mod triangle;
mod vertex;

use material::Material;
use mesh::Mesh;
use model::Model;
use stream_ext::{ReadTriangle, StreamExt};
use texture::Texture;

use vertex::Vertex;

use nalgebra::Vector2;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum SiaParseError {
    #[error("Expexted header SHSM, but found {0}")]
    Header(String),
    #[error("Face index larger than available vertices\nFace Index: {0}\nVertices Length: {1}\n at file byte position: {2}")]
    FaceVertexLenghtMismatch(u32, usize, u64),
    #[error("{0} is a unkown vertex type")]
    UnknownVertexType(u32),
    #[error("Expected EHSM, but found {0:#?} at file byte position: {1}")]
    EndTagB([u8; 4], u64),
    #[error("Expected EHSM, but found {0} at file byte position: {1}")]
    EndTagS(String, u64),
    #[error("file error")]
    File(#[from] std::io::Error),
    #[error("utf-8 error")]
    Utf8(#[from] std::str::Utf8Error),
}

pub fn parse<P: AsRef<Path>>(filepath: P) -> Result<Model, SiaParseError> {
    let mut file = File::open(&filepath)?;

    let mut model = Model::new();

    let mut begin_file_tag = [0u8; 4];
    file.read_exact(&mut begin_file_tag)?;
    let begin_file_tag = str::from_utf8(&begin_file_tag)?;
    if begin_file_tag != "SHSM" {
        return Err(SiaParseError::Header(begin_file_tag.into()));
    }

    model.maybe_version = file.read_u32::<LittleEndian>()?;

    model.name = file.read_string();

    // So far these bytes have only been zero,
    // changing them did nothing
    file.skip(12);

    // This might be some sort of scale, since it tends to resemble another bouding box value
    // changing it did nothing
    model.who_knows = file.read_f32::<LittleEndian>()?;

    model.bounding_box = file.read_bounding_box();

    model.objects_num = file.read_u32::<LittleEndian>()?;

    for _ in 0..model.objects_num {
        let mut mesh = Mesh::new();
        file.read_u32::<LittleEndian>()?;

        // Vertices
        mesh.num_vertices = file.read_u32::<LittleEndian>()?;

        file.read_u32::<LittleEndian>()?;

        // Number of triangles when divided by 3
        mesh.num_triangles = file.read_u32::<LittleEndian>()? / 3;

        // ID
        mesh.id = file.read_u32::<LittleEndian>()?;
        file.skip(8);
        model.meshes.push(mesh);
    }

    model.num_meshes = file.read_u32::<LittleEndian>()?;

    // Changing these did nothing
    file.skip(16);

    for i in 0..model.num_meshes {
        let mut mesh = model.meshes.get_mut(i as usize).unwrap();
        let material_kind = file.read_string();
        mesh.materials_num = file.read_u8()?;
        for _ in 0..mesh.materials_num {
            let mut material = Material::new();
            material.kind = material_kind.to_owned();
            material.name = file.read_string();
            material.textures_num = file.read_u8()?;
            for _ in 0..material.textures_num {
                let texture_id = file.read_u8()?;
                let texture = Texture::new(file.read_string(), texture_id);
                material.textures.push(texture);
            }
            mesh.materials.push(material);
        }
        if i != model.num_meshes - 1 {
            file.skip(80);
        }
    }
    file.skip(64);

    let total_num_vertecies = file.read_u32::<LittleEndian>().unwrap();

    // dbg!(&file.position());
    let vertex_type = file.read_u32::<LittleEndian>()?;
    // dbg!(vertex_type);

    // dbg!(&file.position());
    for i in 0..model.num_meshes {
        let mesh = model.meshes.get_mut(i as usize).unwrap();

        for _ in 0..mesh.num_vertices {
            let pos = file.read_vector3();

            // Think these are normals, when plotted out as vertices, they make a sphere.
            // Which makes sense if it's normals
            // Actually, I'm second guessing myself
            let normal = file.read_vector3();

            let uv = match vertex_type {
                3 => Vector2::<f32>::new(0f32, 0f32),
                _ => file.read_vector2(),
            };

            // Thinking these are tangents or binormals, last one is always 1 or -1
            match vertex_type {
                3 => file.skip(0),
                39 => file.skip(16),
                47 => file.skip(24),
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
    // dbg!(&file.position());

    let _number_of_triangles = file.read_u32::<LittleEndian>()? / 3;

    if total_num_vertecies > u16::MAX.into() {
        for i in 0..model.num_meshes {
            let mesh = model.meshes.get_mut(i as usize).unwrap();
            for _ in 0..mesh.num_triangles {
                let triangle: Triangle<u32> = file.read_triangle();
                if triangle.max() as usize > mesh.vertices.len() {
                    return Err(SiaParseError::FaceVertexLenghtMismatch(
                        triangle.max(),
                        mesh.vertices.len(),
                        file.position()?,
                    ));
                }
                mesh.triangles.push(triangle.into());
            }
        }
    } else {
        for i in 0..model.num_meshes {
            let mesh = model.meshes.get_mut(i as usize).unwrap();
            for _ in 0..mesh.num_triangles {
                let triangle: Triangle<u16> = file.read_triangle();
                if triangle.max() as usize > mesh.vertices.len() {
                    return Err(SiaParseError::FaceVertexLenghtMismatch(
                        triangle.max().into(),
                        mesh.vertices.len(),
                        file.position()?,
                    ));
                }
                mesh.triangles.push(triangle.into());
            }
        }
    }

    file.skip(8);
    let _num = file.read_u8()?;
    // if num != 0 {
    //     dbg!(&num);
    //     return Ok(model);
    // }
    file.skip(4);
    let mut end_file_tag = [0u8; 4];
    file.read_exact(&mut end_file_tag)?;

    match str::from_utf8(&end_file_tag) {
        Ok(s) => {
            if s != "EHSM" {
                return Err(SiaParseError::EndTagS(s.into(), file.position()?));
            }
        }
        Err(_) => {
            return Err(SiaParseError::EndTagB(end_file_tag, file.position()?));
        }
    }

    Ok(model)
}
