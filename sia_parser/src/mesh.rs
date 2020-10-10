use crate::{
    material::Material,
    material::PyMaterial,
    triangle::PyTriangle,
    triangle::Triangle,
    vertex::{PyVertex, Vertex},
};
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub(crate) struct PyMesh {
    #[pyo3(get)]
    pub id: u32,
    #[pyo3(get)]
    pub materials: Vec<PyMaterial>,
    #[pyo3(get)]
    pub vertices: Vec<PyVertex>,
    #[pyo3(get)]
    pub triangles: Vec<PyTriangle>,
}

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

impl Into<PyMesh> for Mesh {
    fn into(self) -> PyMesh {
        PyMesh {
            id: self.id,
            materials: self.materials.into_iter().map(|m| m.into()).collect(),
            vertices: self.vertices.into_iter().map(|v| v.into()).collect(),
            triangles: self.triangles.into_iter().map(|v| v.into()).collect(),
        }
    }
}
