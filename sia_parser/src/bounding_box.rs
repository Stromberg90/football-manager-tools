use pyo3::{types::PyFloat, PyAny};

#[derive(Debug, Default, Clone)]
pub struct BoundingBox {
    pub max_x: f32,
    pub max_y: f32,
    pub max_z: f32,
    pub min_x: f32,
    pub min_y: f32,
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

impl From<&PyAny> for BoundingBox {
    fn from(item: &PyAny) -> Self {
        let mut bounding_box = BoundingBox::new();
        bounding_box.max_x = item
            .getattr("max_x")
            .unwrap()
            .cast_as::<PyFloat>()
            .unwrap()
            .value() as f32;
        bounding_box.max_y = item
            .getattr("max_y")
            .unwrap()
            .cast_as::<PyFloat>()
            .unwrap()
            .value() as f32;
        bounding_box.max_z = item
            .getattr("max_z")
            .unwrap()
            .cast_as::<PyFloat>()
            .unwrap()
            .value() as f32;
        bounding_box.min_x = item
            .getattr("min_x")
            .unwrap()
            .cast_as::<PyFloat>()
            .unwrap()
            .value() as f32;
        bounding_box.min_y = item
            .getattr("min_y")
            .unwrap()
            .cast_as::<PyFloat>()
            .unwrap()
            .value() as f32;
        bounding_box.min_z = item
            .getattr("min_z")
            .unwrap()
            .cast_as::<PyFloat>()
            .unwrap()
            .value() as f32;
        bounding_box
    }
}
