use bitfield_struct::bitfield;

#[derive(Default, Debug, PartialEq)]
pub enum EndKind {
    #[default]
    Unknown,
    MeshType(String),
    IsBanner(u8),
    IsCompBanner(u8),
    IsMatchBall(u8),
    IsTeamLogo(u8),
}

#[derive(Default, Debug)]
pub struct SiaFile {
    pub version_maybe: u32,
    pub name: String,
    pub unknown1: [u8; 12],
    pub maybe_scale: f32,
    pub bounding_box: [f32; 6],
    pub objects_num: u32,
    pub meshes: Vec<SiaMesh>,
    pub meshes_num: u32,
    pub vertices_total_num: u32,
    pub settings: SiaSettings,
    pub number_of_triangles: u32,
    pub is_skinned: bool,
    pub number_of_bones: u32,
    pub root_bone_hash_maybe: [u8; 4],
    pub bones: Vec<SiaBone>,
    pub num: u8,
    pub num2_data: [u8; 16],
    pub end_kind_kind: String,
    pub end_kind_mesh_type: MeshType,
    pub render_flags_extra_data: [u8; 4],
    pub end_mesh_type: EndKind,
    pub instances: Vec<SiaInstance>,
}

#[derive(Debug)]
pub struct SiaBone {
    pub data: [u8; 56],
}

#[bitfield(u32)]
pub struct SiaSettingsBitField {
    pub position: bool,
    pub normal: bool,
    pub uv_set1: bool,
    pub uv_set2: bool,
    pub unknown1: bool,
    pub tangent: bool,
    pub skinned: bool,
    pub unknown2: bool,
    pub unknown3: bool,
    pub unknown4: bool,
    #[bits(22)]
    pub _p: u32,
}

#[derive(Default, Clone, Debug)]
pub struct SiaSettings {
    pub position: bool,
    pub normal: bool,
    pub uv_set1: bool,
    pub uv_set2: bool,
    pub unknown1: bool,
    pub tangent: bool,
    pub skinned: bool,
    pub unknown2: bool,
    pub unknown3: bool,
    pub unknown4: bool,
}

impl From<SiaSettingsBitField> for SiaSettings {
    fn from(value: SiaSettingsBitField) -> Self {
        SiaSettings {
            position: value.position(),
            normal: value.normal(),
            uv_set1: value.uv_set1(),
            uv_set2: value.uv_set2(),
            unknown1: value.unknown1(),
            tangent: value.tangent(),
            skinned: value.skinned(),
            unknown2: value.unknown2(),
            unknown3: value.unknown3(),
            unknown4: value.unknown4(),
        }
    }
}

impl From<SiaSettings> for SiaSettingsBitField {
    fn from(value: SiaSettings) -> Self {
        SiaSettingsBitField::new()
            .with_position(value.position)
            .with_normal(value.normal)
            .with_uv_set1(value.uv_set1)
            .with_uv_set2(value.uv_set2)
            .with_unknown1(value.unknown1)
            .with_tangent(value.tangent)
            .with_skinned(value.skinned)
            .with_unknown2(value.unknown2)
            .with_unknown3(value.unknown3)
            .with_unknown4(value.unknown4)
    }
}

#[derive(Debug)]
pub struct SiaMesh {
    pub materials_num: u8,
    pub vertices_num: u32,
    pub triangles_num: u32,
    pub vertex_offset: u32,
    pub triangle_offset: u32,
    pub id: u32,
    pub unknown: [u8; 8],
    pub maybe_hash: [u8; 4],
    pub unknown1: [u8; 4],
    pub unknown2: [u8; 4],
    pub unknown3: [u8; 4],
    pub unknown4: [u8; 64],
    pub material_type: String,
    pub materials: Vec<SiaMaterial>,
    pub vertices: Vec<SiaVertex>,
    pub triangles: Vec<SiaTriangle>,
}

impl Default for SiaMesh {
    fn default() -> Self {
        Self {
            materials_num: Default::default(),
            vertices_num: Default::default(),
            triangles_num: Default::default(),
            vertex_offset: Default::default(),
            triangle_offset: Default::default(),
            id: Default::default(),
            unknown: Default::default(),
            maybe_hash: Default::default(),
            unknown1: Default::default(),
            unknown2: Default::default(),
            unknown3: Default::default(),
            unknown4: [0; 64],
            material_type: Default::default(),
            materials: Default::default(),
            vertices: Default::default(),
            triangles: Default::default(),
        }
    }
}

#[derive(Default, Debug)]
pub struct SiaMaterial {
    pub kind: String,
    pub texture_num: u8,
    pub textures: Vec<SiaTexture>,
}

#[derive(Default, Clone, Debug, PartialEq)]
pub enum TextureKind {
    #[default]
    Albedo,
    RoughnessMetallicAmbientOcclusion,
    Normal,
    Mask,
    Lightmap,
    Flowmap,
}

impl From<u8> for TextureKind {
    fn from(value: u8) -> Self {
        match value {
            0 => Self::Albedo,
            1 => Self::RoughnessMetallicAmbientOcclusion,
            2 => Self::Normal,
            5 => Self::Mask,
            6 => Self::Lightmap,
            7 => Self::Flowmap,
            _ => unimplemented!(),
        }
    }
}

impl From<TextureKind> for u8 {
    fn from(value: TextureKind) -> Self {
        match value {
            TextureKind::Albedo => 0,
            TextureKind::RoughnessMetallicAmbientOcclusion => 1,
            TextureKind::Normal => 2,
            TextureKind::Mask => 5,
            TextureKind::Lightmap => 6,
            TextureKind::Flowmap => 7,
        }
    }
}

#[derive(Default, Debug)]
pub struct SiaTexture {
    pub kind: TextureKind,
    pub path: String,
}

#[derive(Default, Debug)]
pub struct SiaVector3 {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

#[derive(Default, Debug)]
pub struct SiaVector2 {
    pub x: f32,
    pub y: f32,
}

#[derive(Default, Debug)]
pub struct SiaBoneVertex {
    pub ids: Vec<u8>,
    pub influences: Vec<f32>,
}

#[derive(Default, Debug)]
pub struct SiaVertex {
    pub position: SiaVector3,
    pub normal: SiaVector3,
    pub texture_coords: Vec<SiaVector2>,
    pub tangent: SiaVector3,
    pub unknown1: [u8; 8],
    pub tangent_unknown: [u8; 4],
    pub unknown3: [u8; 20],
    pub unknown4: [u8; 4],
    pub bone: SiaBoneVertex,
}

#[derive(Default, Clone, Debug, PartialEq)]
pub enum MeshType {
    #[default]
    RenderFlags,
    VariableLength,
    BodyPart,
    RearCap,
    Glasses,
    StadiumRoof,
    PlayerTunnel,
    SideCap,
}

impl From<u8> for MeshType {
    fn from(value: u8) -> Self {
        match value {
            2 => Self::RenderFlags,
            8 => Self::VariableLength,
            88 => Self::BodyPart,
            152 => Self::RearCap,
            136 => Self::Glasses,
            216 => Self::StadiumRoof,
            232 => Self::PlayerTunnel,
            248 => Self::SideCap,
            _ => unimplemented!(),
        }
    }
}

impl From<MeshType> for u8 {
    fn from(value: MeshType) -> Self {
        match value {
            MeshType::RenderFlags => 2,
            MeshType::VariableLength => 8,
            MeshType::BodyPart => 88,
            MeshType::RearCap => 152,
            MeshType::Glasses => 136,
            MeshType::StadiumRoof => 216,
            MeshType::PlayerTunnel => 232,
            MeshType::SideCap => 248,
        }
    }
}

#[derive(Default, Debug)]
pub struct SiaTriangle(pub u32, pub u32, pub u32);

#[derive(Default, Debug)]
pub struct SiaInstance {
    pub kind: u32,
    pub matrix_values_and_unknown: Vec<f32>,
    pub unknown: [u8; 24],
    pub num1: u32,
    pub positions: Vec<SiaVector3>,
    pub name: String,
    pub path: String,
}
