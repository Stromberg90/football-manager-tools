use nalgebra::{Vector2, Vector3};

#[derive(Debug)]
pub struct Vertex {
    pub position: Vector3<f32>,
    pub uv: Vector2<f32>,
    pub normals: Vector3<f32>,
}
