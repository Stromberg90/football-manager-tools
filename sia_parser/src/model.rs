use std::collections::HashMap;

use crate::bounding_box::BoundingBox;
use crate::mesh::Mesh;

#[derive(Debug)]
pub enum EndKind {
    MeshType(String),
    IsBanner(bool),
    IsCompBanner(bool),
}

#[derive(Debug, Default)]
pub struct Model {
    pub who_knows: f32,
    pub objects_num: u32,
    pub object_id: u32,
    pub something_about_faces_or_vertices: u32,
    pub maybe_version: u32,
    pub name: String,
    pub bounding_box: BoundingBox,
    pub num_vertices: u32,
    pub num_meshes: u32,
    pub meshes: HashMap<usize, Mesh>,
    pub end_kind: Option<EndKind>,
}

impl Model {
    pub(crate) fn new() -> Self {
        Model {
            who_knows: 0f32,
            objects_num: 0,
            object_id: 0,
            something_about_faces_or_vertices: 0,
            maybe_version: 0,
            name: String::new(),
            bounding_box: BoundingBox::new(),
            num_vertices: 0,
            num_meshes: 0,
            meshes: HashMap::new(), // I'm using this instead of a vec, cause I need to make sure that the indecies match
            end_kind: None,
        }
    }
}
