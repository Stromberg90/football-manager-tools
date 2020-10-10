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
use model::{Model, PyModel};
use stream_ext::{ReadTriangle, StreamExt};
use texture::Texture;

use vertex::Vertex;

use nalgebra::Vector2;
use thiserror::Error;

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[derive(Error, Debug)]
pub enum SiaParseError {
    #[error("Expexted header SHSM, but found {0}")]
    Header(String),
    #[error("Face index larger than available vertices\nFace Index: {0}\nVertices Length: {1}\n at file byte position: {2}")]
    FaceVertexLenghtMismatch(u32, usize, u64),
    #[error("{0} is a unkown vertex type")]
    UnknownVertexType(u32),
    #[error("{0} is a unkown type at file byte position: {1}")]
    UnknownType(u8, u64),
    #[error("Expected EHSM, but found {0:#?} at file byte position: {1} num is {2}")]
    EndTagB([u8; 4], u64, u8),
    #[error("Expected EHSM, but found {0} at file byte position: {1} num is {2}")]
    EndTagS(String, u64, u8),
    #[error(transparent)]
    File(#[from] std::io::Error),
    #[error(transparent)]
    Utf8(#[from] std::str::Utf8Error),
}

#[pyfunction]
fn load_file(filepath: String) -> PyResult<PyModel> {
    if let Ok(model) = from_path(&filepath) {
        Ok(model.into())
    } else {
        Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "Couldn't load file: {}",
            filepath
        )))
    }
}

#[pyfunction]
fn save_file() {}

#[pymodule]
fn sia_parser(_: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(load_file, m)?)?;
    m.add_function(wrap_pyfunction!(save_file, m)?)?;

    Ok(())
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
                return Err(SiaParseError::EndTagS(s.into(), file.position()?, num));
            }
        }
        Err(_) => {
            return Err(SiaParseError::EndTagB(end_file_tag, file.position()?, num));
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
        file.skip(4); // What could this be?

        // Vertices
        mesh.num_vertices = file.read_u32::<LittleEndian>()?;

        file.skip(4); // What could this be?

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
            // Some of these probably use lightmaps and have 2 or more uv channels.
            match vertex_type {
                3 => file.skip(0),
                39 => file.skip(16),
                47 => file.skip(24), // This might be a second uv set, 24 bytes matches with another set of uv's
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
        let mesh = model.meshes.get_mut(i as usize).unwrap();
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

    file.skip(8);
    // match vertex_type {
    //     39 => file.skip(9),
    //     _ => {}
    // }

    // match vertex_type {
    //     231 => {
    //         let other_num = file.read_u32::<LittleEndian>().unwrap();
    //         if other_num != 0 {
    //             let number_of_something = file.read_u32::<LittleEndian>().unwrap();
    //             file.skip(((56 * number_of_something) + 4).into());
    //         }
    //     }
    //     39 => {
    //         let other_num = file.read_u16::<LittleEndian>().unwrap();
    //         if other_num != 0 {
    //             let number_of_something = file.read_u32::<LittleEndian>().unwrap();
    //             file.skip((44 * number_of_something).into());
    //         }
    //     }
    //     _ => {}
    // }

    let num = file.read_u8()?;

    // match num {
    //     0 => {}
    //     7 => file.skip(10),
    //     2 => file.skip(16),
    //     58 => {
    //         let kind = file.read_string_u8_len()?;
    //         match kind.as_ref() {
    //             "mesh_type" => {
    //                 file.skip(5);
    //                 let _ = file.read_string_u8_len()?;
    //                 file.skip(1);
    //             }
    //             _ => return Err(SiaParseError::UnknownType(0, file.position()?)),
    //         }
    //     }
    //     42 => {
    //         let kind = file.read_string_u8_len()?;
    //         match kind.as_ref() {
    //             "mesh_type" => {
    //                 let type_kind = file.read_u8().unwrap();
    //                 match type_kind {
    //                     // hair
    //                     88 => file.skip(4),
    //                     // STADIUM_ROOF
    //                     216 => file.skip(12),
    //                     _ => return Err(SiaParseError::UnknownType(type_kind, file.position()?)),
    //                 }
    //             }
    //             "is_banner" => {
    //                 let _ = file.read_u8().unwrap() != 0;
    //             }
    //             _ => return Err(SiaParseError::UnknownType(0, file.position()?)),
    //         }
    //     }
    //     _ => {
    //         return Err(SiaParseError::UnknownType(num, file.position()?));
    //     }
    // }
    file.skip(4);

    read_file_end(file, num)?;

    Ok(model)
}
