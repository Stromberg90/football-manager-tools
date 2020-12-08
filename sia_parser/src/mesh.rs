use crate::{material::Material, triangle::Triangle, vertex::Vertex};

#[derive(Debug, Default)]
pub struct Mesh {
    pub num_vertices: u32,
    pub num_triangles: u32,
    pub id: u32,
    pub materials_num: u8,
    pub materials: Vec<Material>,
    pub vertices: Vec<Vertex>,
    pub triangles: Vec<Triangle<u32>>,
}

impl Mesh {
    pub(crate) fn new() -> Self {
        Mesh {
            num_vertices: 0,
            num_triangles: 0,
            id: 0,
            materials_num: 0,
            materials: Vec::new(),
            vertices: Vec::new(),
            triangles: Vec::new(),
        }
    }
}
