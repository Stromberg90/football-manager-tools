use crate::texture::{PyTexture, Texture};

use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub(crate) struct PyMaterial {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub kind: String,
    #[pyo3(get)]
    pub textures: Vec<PyTexture>,
}

#[derive(Debug, Default)]
pub struct Material {
    pub name: String,
    pub kind: String,
    pub textures_num: u8,
    pub textures: Vec<Texture>,
}

impl Material {
    pub fn new() -> Self {
        Material {
            name: String::new(),
            kind: String::new(),
            textures_num: 0,
            textures: Vec::new(),
        }
    }
}

impl Into<PyMaterial> for Material {
    fn into(self) -> PyMaterial {
        PyMaterial {
            name: self.name,
            kind: self.kind,
            textures: self.textures.into_iter().map(|t| t.into()).collect(),
        }
    }
}
