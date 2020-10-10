use pyo3::prelude::*;

#[derive(Debug)]
pub enum TextureType {
    Albedo,
    Normal,
    RoughnessMetallicAmbientOcclusion,
    Mask, // [ma] looks to be some sort of mask, but I don't quite how it is used.
    Lightmap,
}

type PyTextureType = String;

#[pyclass]
#[derive(Clone)]
pub(crate) struct PyTexture {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub id: PyTextureType,
}

#[derive(Debug)]
pub struct Texture {
    pub name: String,
    pub id: TextureType,
}

impl Texture {
    pub(crate) fn new<S: Into<String>>(name: S, id: u8) -> Self {
        Texture {
            name: name.into(),
            id: id.into(),
        }
    }
}

impl From<u8> for TextureType {
    fn from(id: u8) -> Self {
        match id {
            0 => TextureType::Albedo,
            1 => TextureType::RoughnessMetallicAmbientOcclusion,
            2 => TextureType::Normal,
            5 => TextureType::Mask,
            6 => TextureType::Lightmap,
            _ => panic!("Couldn't convert {} to TextureType", id),
        }
    }
}

impl From<TextureType> for PyTextureType {
    fn from(t: TextureType) -> Self {
        match t {
            TextureType::Albedo => "Albedo".into(),
            TextureType::Normal => "Normal".into(),
            TextureType::RoughnessMetallicAmbientOcclusion => {
                "RoughnessMetallicAmbientOcclusion".into()
            }
            TextureType::Mask => "Mask".into(),
            TextureType::Lightmap => "Lightmap".into(),
        }
    }
}

impl Into<PyTexture> for Texture {
    fn into(self) -> PyTexture {
        PyTexture {
            name: self.name,
            id: self.id.into(),
        }
    }
}
