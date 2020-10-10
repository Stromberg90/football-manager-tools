use std::cmp::max;

use pyo3::prelude::*;

#[derive(Debug)]
pub struct Triangle<T>(pub T, pub T, pub T);

#[pyclass]
#[derive(Clone)]
pub struct PyTriangle {
    #[pyo3(get)]
    index_1: u32,
    #[pyo3(get)]
    index_2: u32,
    #[pyo3(get)]
    index_3: u32,
}

impl Triangle<u16> {
    pub fn max(&self) -> u16 {
        max(max(self.0, self.1), self.2)
    }
}

impl Triangle<u32> {
    pub fn max(&self) -> u32 {
        max(max(self.0, self.1), self.2)
    }
}

impl From<Triangle<u16>> for Triangle<u32> {
    fn from(triangle: Triangle<u16>) -> Self {
        Self {
            0: triangle.0.into(),
            1: triangle.1.into(),
            2: triangle.2.into(),
        }
    }
}

impl Into<PyTriangle> for Triangle<u32> {
    fn into(self) -> PyTriangle {
        PyTriangle {
            index_1: self.0.into(),
            index_2: self.1.into(),
            index_3: self.2.into(),
        }
    }
}
