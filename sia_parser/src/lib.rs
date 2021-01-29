use pyo3::{types::PyModule, PyErr, Python};
use std::path::Path;

mod bounding_box;
mod material;
mod mesh;
pub mod model;
pub mod texture;
mod triangle;
mod vertex;

use model::Model;
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

pub fn from_path<P: AsRef<Path>>(filepath: P) -> Result<Model, PyErr> {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let parse_sia_str = include_str!("../../blender_addons/io_scene_sia/parse_sia.py");
    let parse_sia = PyModule::from_code(py, parse_sia_str, "parse_sia.py", "parse_sia")?;
    match parse_sia.call1("load_sia_file", (filepath.as_ref().display().to_string(),)) {
        Ok(o) => Ok(o.into()),
        Err(e) => Err(e),
    }
}
