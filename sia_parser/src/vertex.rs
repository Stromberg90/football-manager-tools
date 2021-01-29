use nalgebra::{Vector2, Vector3};
use pyo3::PyAny;

#[derive(Debug)]
pub struct Vertex {
    pub position: Vector3<f32>,
    pub uv: Vector2<f32>,
    pub normals: Vector3<f32>,
}

impl From<&PyAny> for Vertex {
    fn from(item: &PyAny) -> Self {
        let position = item.getattr("position").unwrap();
        let normal = item.getattr("normal").unwrap();
        let uv = item.getattr("uv").unwrap();
        Vertex {
            position: Vector3::new(
                position.getattr("x").unwrap().extract().unwrap(),
                position.getattr("y").unwrap().extract().unwrap(),
                position.getattr("z").unwrap().extract().unwrap(),
            ),
            uv: Vector2::new(
                uv.getattr("x").unwrap().extract().unwrap(),
                uv.getattr("y").unwrap().extract().unwrap(),
            ),
            normals: Vector3::new(
                normal.getattr("x").unwrap().extract().unwrap(),
                normal.getattr("y").unwrap().extract().unwrap(),
                normal.getattr("z").unwrap().extract().unwrap(),
            ),
        }
    }
}
