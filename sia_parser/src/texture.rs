use pyo3::{types::PyUnicode, PyAny};

#[derive(Debug, PartialEq)]
pub enum TextureType {
    Albedo,
    Normal,
    RoughnessMetallicAmbientOcclusion,
    Mask, // [ma] looks to be some sort of mask, but I don't quite know how it is used.
    Lightmap,
    Flow,
}

#[derive(Debug, PartialEq)]
pub struct Texture {
    pub name: String,
    pub id: TextureType,
}

impl From<u8> for TextureType {
    fn from(id: u8) -> Self {
        match id {
            0 => TextureType::Albedo,
            1 => TextureType::RoughnessMetallicAmbientOcclusion,
            2 => TextureType::Normal,
            5 => TextureType::Mask,
            6 => TextureType::Lightmap,
            7 => TextureType::Flow,
            _ => panic!("Couldn't convert {} to TextureType", id),
        }
    }
}

impl From<&PyAny> for Texture {
    fn from(item: &PyAny) -> Self {
        let id: u8 = item.getattr("id").unwrap().extract().unwrap();
        Texture {
            name: PyUnicode::from_object(item.getattr("name").unwrap(), "utf-8", "")
                .unwrap()
                .to_string(),
            id: id.into(),
        }
    }
}
