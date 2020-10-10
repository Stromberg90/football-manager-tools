use nalgebra::{Vector2, Vector3};

use pyo3::prelude::*;

#[derive(Debug)]
pub struct Vertex {
    pub position: Vector3<f32>,
    pub uv: Vector2<f32>,
    pub normals: Vector3<f32>,
}

#[pyclass]
#[derive(Clone)]
pub struct PyVertex {
    #[pyo3(get)]
    pub position: [f32; 3],
    #[pyo3(get)]
    pub uv: [f32; 2],
    #[pyo3(get)]
    pub normals: [f32; 3],
}

impl Into<PyVertex> for Vertex {
    fn into(self) -> PyVertex {
        PyVertex {
            position: [self.position[0], self.position[1], self.position[2]],
            uv: [self.uv[0], self.uv[1]],
            normals: [self.normals[0], self.normals[1], self.normals[2]],
        }
    }
}
