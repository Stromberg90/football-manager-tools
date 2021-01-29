use pyo3::PyAny;

#[derive(Debug)]
pub struct Triangle<T>(pub T, pub T, pub T);

impl From<Triangle<u16>> for Triangle<u32> {
    fn from(triangle: Triangle<u16>) -> Self {
        Self {
            0: triangle.0.into(),
            1: triangle.1.into(),
            2: triangle.2.into(),
        }
    }
}

impl From<&PyAny> for Triangle<u32> {
    fn from(item: &PyAny) -> Self {
        Triangle {
            0: item.getattr("index1").unwrap().extract().unwrap(),
            1: item.getattr("index2").unwrap().extract().unwrap(),
            2: item.getattr("index3").unwrap().extract().unwrap(),
        }
    }
}
