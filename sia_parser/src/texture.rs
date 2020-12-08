#[derive(Debug)]
pub enum TextureType {
    Albedo,
    Normal,
    RoughnessMetallicAmbientOcclusion,
    Mask, // [ma] looks to be some sort of mask, but I don't quite know how it is used.
    Lightmap,
    Flow,
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
            7 => TextureType::Flow,
            _ => panic!("Couldn't convert {} to TextureType", id),
        }
    }
}
