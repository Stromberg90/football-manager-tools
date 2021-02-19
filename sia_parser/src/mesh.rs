use pyo3::{types, PyAny};

use crate::{material::Material, triangle::Triangle, vertex::Vertex};

#[derive(Debug, Default, PartialEq)]
pub struct Mesh {
    pub num_vertices: u32,
    pub num_triangles: u32,
    pub id: u32,
    pub materials: Vec<Material>,
    pub vertices: Vec<Vertex>,
    pub triangles: Vec<Triangle<u32>>,
}

impl From<&PyAny> for Mesh {
    fn from(item: &PyAny) -> Self {
        let materials = item
            .getattr("materials")
            .unwrap()
            .downcast::<types::PyList>()
            .unwrap();
        let vertices = item
            .getattr("vertices")
            .unwrap()
            .downcast::<types::PyList>()
            .unwrap();
        let triangles = item
            .getattr("triangles")
            .unwrap()
            .downcast::<types::PyList>()
            .unwrap();
        let mesh = Mesh {
            num_vertices: item.getattr("vertices_num").unwrap().extract().unwrap(),
            num_triangles: item.getattr("triangles_num").unwrap().extract().unwrap(),
            id: item.getattr("id").unwrap().extract().unwrap(),
            materials: materials.iter().map(|m| m.into()).collect(),
            vertices: vertices.iter().map(|m| m.into()).collect(),
            triangles: triangles.iter().map(|m| m.into()).collect(),
        };
        mesh
    }
}
