use pyo3::{
    types::{self, PyUnicode},
    PyAny,
};

use crate::texture::Texture;

#[derive(Debug, Default, PartialEq)]
pub struct Material {
    pub name: String,
    pub kind: String,
    pub textures: Vec<Texture>,
}

impl From<&PyAny> for Material {
    fn from(item: &PyAny) -> Self {
        Material {
            name: PyUnicode::from_object(item.getattr("name").unwrap(), "utf-8", "")
                .unwrap()
                .to_string(),
            kind: PyUnicode::from_object(item.getattr("kind").unwrap(), "utf-8", "")
                .unwrap()
                .to_string(),
            textures: item
                .getattr("textures")
                .unwrap()
                .downcast::<types::PyList>()
                .unwrap()
                .iter()
                .map(|t| t.into())
                .collect(),
        }
    }
}
