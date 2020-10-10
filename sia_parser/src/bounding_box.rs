use pyo3::prelude::*;

#[pyclass]
#[derive(Debug, Default, Clone)]
pub struct BoundingBox {
    #[pyo3(get)]
    pub max_x: f32,
    #[pyo3(get)]
    pub max_y: f32,
    #[pyo3(get)]
    pub max_z: f32,
    #[pyo3(get)]
    pub min_x: f32,
    #[pyo3(get)]
    pub min_y: f32,
    #[pyo3(get)]
    pub min_z: f32,
}

impl BoundingBox {
    pub fn new() -> Self {
        BoundingBox {
            max_x: 0f32,
            max_y: 0f32,
            max_z: 0f32,
            min_x: 0f32,
            min_y: 0f32,
            min_z: 0f32,
        }
    }
}
