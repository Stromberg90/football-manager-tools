use crate::bounding_box::BoundingBox;
use crate::mesh::Mesh;

#[derive(Debug)]
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
    pub meshes: Vec<Mesh>,
}

impl Model {
    pub fn new() -> Self {
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
            meshes: Vec::new(),
        }
    }
}
