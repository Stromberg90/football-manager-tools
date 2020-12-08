use crate::texture::Texture;

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
