mod read;
pub mod types;
mod write;
use byteorder::{LittleEndian, ReadBytesExt, WriteBytesExt};
use read::SiaRead;
use write::{write_string, write_string_u8_len};

use crate::types::{
    EndKind, MeshType, SiaBone, SiaBoneVertex, SiaFile, SiaInstance, SiaMaterial, SiaMesh,
    SiaSettings, SiaSettingsBitField, SiaTexture, SiaTriangle, SiaVector2, SiaVector3, SiaVertex,
    TextureKind,
};
use std::{
    io::{Cursor, Read, Write},
    path::Path,
};

pub fn from_path<T>(path: T) -> SiaFile
where
    T: AsRef<Path>,
{
    let mut reader = Cursor::new(std::fs::read(&path).unwrap());

    let mut sia_file = SiaFile::default();
    let mut buffer: [u8; 4] = [0; 4];
    reader.read_exact(&mut buffer).unwrap();
    let _ = String::from_utf8_lossy(&buffer);

    sia_file.version_maybe = reader.read_u32::<LittleEndian>().unwrap();
    sia_file.name = reader.read_string();
    sia_file.unknown1 = reader.read_byte_array();
    sia_file.maybe_scale = reader.read_f32::<LittleEndian>().unwrap();
    sia_file.bounding_box = reader.read_bounding_box();
    sia_file.objects_num = reader.read_u32::<LittleEndian>().unwrap();

    for _ in 0..sia_file.objects_num {
        let mesh = SiaMesh {
            vertex_offset: reader.read_u32::<LittleEndian>().unwrap(),
            vertices_num: reader.read_u32::<LittleEndian>().unwrap(),
            triangle_offset: reader.read_u32::<LittleEndian>().unwrap(),
            triangles_num: reader.read_u32::<LittleEndian>().unwrap() / 3,
            id: reader.read_u32::<LittleEndian>().unwrap(),
            unknown: reader.read_byte_array(),
            ..Default::default()
        };

        sia_file.meshes.push(mesh);
    }

    sia_file.meshes_num = reader.read_u32::<LittleEndian>().unwrap();

    for i in 0..sia_file.meshes_num {
        let mesh = sia_file.meshes.get_mut(i as usize).unwrap();

        mesh.maybe_hash = reader.read_byte_array();
        mesh.unknown1 = reader.read_byte_array();
        mesh.unknown2 = reader.read_byte_array();
        mesh.unknown3 = reader.read_byte_array();

        mesh.material_type = reader.read_string();
        mesh.materials_num = reader.read_u8().unwrap();

        for _ in 0..mesh.materials_num {
            let mut material = SiaMaterial {
                kind: reader.read_string(),
                texture_num: reader.read_u8().unwrap(),
                textures: Vec::new(),
            };
            for _ in 0..material.texture_num {
                material.textures.push(SiaTexture {
                    kind: TextureKind::from(reader.read_u8().unwrap()),
                    path: reader.read_string(),
                });
            }
            mesh.materials.push(material);
        }
        mesh.unknown4 = reader.read_byte_array();
    }

    sia_file.vertices_total_num = reader.read_u32::<LittleEndian>().unwrap();

    sia_file.settings = SiaSettings::from(SiaSettingsBitField::from_bits(
        reader.read_u32::<LittleEndian>().unwrap(),
    ));

    for i in 0..sia_file.meshes_num {
        let mesh = sia_file.meshes.get_mut(i as usize).unwrap();

        for _ in 0..mesh.vertices_num {
            let mut vertex = SiaVertex::default();

            if sia_file.settings.position {
                vertex.position = SiaVector3 {
                    x: reader.read_f32::<LittleEndian>().unwrap(),
                    y: reader.read_f32::<LittleEndian>().unwrap(),
                    z: reader.read_f32::<LittleEndian>().unwrap(),
                };
            }
            if sia_file.settings.normal {
                vertex.normal = SiaVector3 {
                    x: reader.read_f32::<LittleEndian>().unwrap(),
                    y: reader.read_f32::<LittleEndian>().unwrap(),
                    z: reader.read_f32::<LittleEndian>().unwrap(),
                };
            }
            if sia_file.settings.uv_set1 {
                vertex.texture_coords.push(SiaVector2 {
                    x: reader.read_f32::<LittleEndian>().unwrap(),
                    y: reader.read_f32::<LittleEndian>().unwrap(),
                });
            } else {
                vertex.texture_coords.push(SiaVector2 { x: 0f32, y: 0f32 });
            }
            if sia_file.settings.uv_set2 {
                vertex.texture_coords.push(SiaVector2 {
                    x: reader.read_f32::<LittleEndian>().unwrap(),
                    y: reader.read_f32::<LittleEndian>().unwrap(),
                });
            }
            if sia_file.settings.unknown1 {
                vertex.unknown1 = reader.read_byte_array();
            }
            if sia_file.settings.unknown2 {
                // Seems to be lacking any info?
            }
            if sia_file.settings.tangent {
                vertex.tangent = SiaVector3 {
                    x: reader.read_f32::<LittleEndian>().unwrap(),
                    y: reader.read_f32::<LittleEndian>().unwrap(),
                    z: reader.read_f32::<LittleEndian>().unwrap(),
                };
                vertex.tangent_unknown = reader.read_byte_array();
            }
            if sia_file.settings.skinned {
                let mut bone = SiaBoneVertex::default();
                for _ in 0..4 {
                    bone.ids.push(reader.read_u8().unwrap());
                }
                for _ in 0..4 {
                    bone.influences
                        .push(reader.read_f32::<LittleEndian>().unwrap());
                }
                vertex.bone = bone;
            }
            if sia_file.settings.unknown3 {
                vertex.unknown3 = reader.read_byte_array();
            }
            if sia_file.settings.unknown4 {
                vertex.unknown4 = reader.read_byte_array();
            }

            mesh.vertices.push(vertex);
        }
    }

    sia_file.number_of_triangles = reader.read_u32::<LittleEndian>().unwrap() / 3;

    for i in 0..sia_file.meshes_num {
        let mesh = sia_file.meshes.get_mut(i as usize).unwrap();

        for _ in 0..mesh.triangles_num {
            let triangle = if sia_file.vertices_total_num > u16::MAX as u32 {
                SiaTriangle(
                    reader.read_u32::<LittleEndian>().unwrap(),
                    reader.read_u32::<LittleEndian>().unwrap(),
                    reader.read_u32::<LittleEndian>().unwrap(),
                )
            } else {
                SiaTriangle(
                    reader.read_u16::<LittleEndian>().unwrap() as u32,
                    reader.read_u16::<LittleEndian>().unwrap() as u32,
                    reader.read_u16::<LittleEndian>().unwrap() as u32,
                )
            };

            mesh.triangles.push(triangle);
        }
    }

    sia_file.is_skinned = reader.read_u32::<LittleEndian>().unwrap() == 1;
    sia_file.number_of_bones = reader.read_u32::<LittleEndian>().unwrap();

    if sia_file.is_skinned {
        sia_file.root_bone_hash_maybe = reader.read_byte_array();
        for _ in 0..sia_file.number_of_bones {
            sia_file.bones.push(SiaBone {
                data: reader.read_byte_array(),
            });
        }
    }

    sia_file.num = reader.read_u8().unwrap();
    if sia_file.num == 2 {
        sia_file.num2_data = reader.read_byte_array();
    } else if sia_file.num == 42 {
        sia_file.end_kind_kind = reader.read_string_u8_len();
        if sia_file.end_kind_kind == "mesh_type" {
            sia_file.end_kind_mesh_type = MeshType::from(reader.read_u8().unwrap());
            match sia_file.end_kind_mesh_type {
                MeshType::VariableLength => {
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string());
                }
                MeshType::RenderFlags => {
                    sia_file.render_flags_extra_data = reader.read_byte_array();
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string_u8_len());
                }
                MeshType::BodyPart => {
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string_with_length(4));
                }
                MeshType::RearCap => {
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string_with_length(8));
                }
                MeshType::StadiumRoof => {
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string_with_length(12));
                }
                MeshType::Glasses => {
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string_with_length(7));
                }
                MeshType::PlayerTunnel => {
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string_with_length(13));
                }
                MeshType::SideCap => {
                    sia_file.end_mesh_type = EndKind::MeshType(reader.read_string_with_length(14));
                }
            }
        } else if sia_file.end_kind_kind == "is_banner" {
            sia_file.end_mesh_type = EndKind::IsBanner(reader.read_u8().unwrap());
        } else if sia_file.end_kind_kind == "is_comp_banner" {
            sia_file.end_mesh_type = EndKind::IsCompBanner(reader.read_u8().unwrap());
        } else if sia_file.end_kind_kind == "is_match_ball" {
            sia_file.end_mesh_type = EndKind::IsMatchBall(reader.read_u8().unwrap());
        } else if sia_file.end_kind_kind == "is_team_logo" {
            sia_file.end_mesh_type = EndKind::IsTeamLogo(reader.read_u8().unwrap());
        }
    }

    let instances_num = reader.read_u32::<LittleEndian>().unwrap();

    for _ in 0..instances_num {
        let mut instance = SiaInstance {
            kind: reader.read_u32::<LittleEndian>().unwrap(),
            ..Default::default()
        };

        for _ in 0..14 {
            instance
                .matrix_values_and_unknown
                .push(reader.read_f32::<LittleEndian>().unwrap());
        }

        instance.unknown = reader.read_byte_array();

        instance.num1 = reader.read_u32::<LittleEndian>().unwrap();

        for _ in 0..instance.num1 {
            for _ in 0..4 {
                instance.positions.push(SiaVector3 {
                    x: reader.read_f32::<LittleEndian>().unwrap(),
                    y: reader.read_f32::<LittleEndian>().unwrap(),
                    z: reader.read_f32::<LittleEndian>().unwrap(),
                });
            }
        }

        instance.name = reader.read_string();
        instance.path = reader.read_string();

        sia_file.instances.push(instance);
    }

    let mut buffer: [u8; 4] = [0; 4];
    reader.read_exact(&mut buffer).unwrap();
    let _ = String::from_utf8_lossy(&buffer);

    sia_file
}

impl SiaFile {
    pub fn write_to<T>(&self, path: T)
    where
        T: AsRef<Path>,
    {
        let mut bytes = std::fs::File::create(path).unwrap();
        bytes.write_all("SHSM".as_bytes()).unwrap();

        bytes.write_u32::<LittleEndian>(self.version_maybe).unwrap();
        write_string(&mut bytes, &self.name);
        bytes.write_all(&self.unknown1).unwrap();
        bytes.write_f32::<LittleEndian>(self.maybe_scale).unwrap();
        for value in self.bounding_box {
            bytes.write_f32::<LittleEndian>(value).unwrap();
        }
        bytes.write_u32::<LittleEndian>(self.objects_num).unwrap();

        for mesh in &self.meshes {
            bytes.write_u32::<LittleEndian>(mesh.vertex_offset).unwrap();
            bytes
                .write_u32::<LittleEndian>(mesh.vertices.len() as u32)
                .unwrap();
            bytes
                .write_u32::<LittleEndian>(mesh.triangle_offset)
                .unwrap();
            bytes
                .write_u32::<LittleEndian>(mesh.triangles.len() as u32 * 3)
                .unwrap();
            bytes.write_u32::<LittleEndian>(mesh.id).unwrap();
            bytes.write_all(&mesh.unknown).unwrap();
        }

        bytes.write_u32::<LittleEndian>(self.meshes_num).unwrap();

        for mesh in &self.meshes {
            bytes.write_all(&mesh.maybe_hash).unwrap();
            bytes.write_all(&mesh.unknown1).unwrap();
            bytes.write_all(&mesh.unknown2).unwrap();
            bytes.write_all(&mesh.unknown3).unwrap();

            write_string(&mut bytes, &mesh.material_type);
            bytes.write_u8(mesh.materials.len() as u8).unwrap();

            for material in &mesh.materials {
                write_string(&mut bytes, &material.kind);
                bytes.write_u8(material.texture_num).unwrap();
                for texture in &material.textures {
                    bytes.write_u8(texture.kind.clone().into()).unwrap();
                    write_string(&mut bytes, &texture.path);
                }
            }
            bytes.write_all(&mesh.unknown4).unwrap();
        }

        let vertices_total_num = self.meshes.iter().map(|m| m.vertices.len() as u32).sum();
        bytes.write_u32::<LittleEndian>(vertices_total_num).unwrap();

        bytes
            .write_u32::<LittleEndian>(SiaSettingsBitField::from(self.settings.clone()).into_bits())
            .unwrap();

        for mesh in &self.meshes {
            for vertex in &mesh.vertices {
                if self.settings.position {
                    bytes.write_f32::<LittleEndian>(vertex.position.x).unwrap();
                    bytes.write_f32::<LittleEndian>(vertex.position.y).unwrap();
                    bytes.write_f32::<LittleEndian>(vertex.position.z).unwrap();
                }
                if self.settings.normal {
                    bytes.write_f32::<LittleEndian>(vertex.normal.x).unwrap();
                    bytes.write_f32::<LittleEndian>(vertex.normal.y).unwrap();
                    bytes.write_f32::<LittleEndian>(vertex.normal.z).unwrap();
                }
                if self.settings.uv_set1 {
                    bytes
                        .write_f32::<LittleEndian>(vertex.texture_coords[0].x)
                        .unwrap();
                    bytes
                        .write_f32::<LittleEndian>(vertex.texture_coords[0].y)
                        .unwrap();
                } else {
                    bytes.write_f32::<LittleEndian>(0f32).unwrap();
                    bytes.write_f32::<LittleEndian>(0f32).unwrap();
                }
                if self.settings.uv_set2 {
                    bytes
                        .write_f32::<LittleEndian>(vertex.texture_coords[1].x)
                        .unwrap();
                    bytes
                        .write_f32::<LittleEndian>(vertex.texture_coords[1].y)
                        .unwrap();
                }
                if self.settings.unknown1 {
                    bytes.write_all(&vertex.unknown1).unwrap();
                }
                if self.settings.tangent {
                    bytes.write_f32::<LittleEndian>(vertex.tangent.x).unwrap();
                    bytes.write_f32::<LittleEndian>(vertex.tangent.y).unwrap();
                    bytes.write_f32::<LittleEndian>(vertex.tangent.z).unwrap();
                    bytes.write_all(&vertex.tangent_unknown).unwrap();
                }
                if self.settings.skinned {
                    for id in &vertex.bone.ids {
                        bytes.write_u8(*id).unwrap();
                    }
                    for influence in &vertex.bone.influences {
                        bytes.write_f32::<LittleEndian>(*influence).unwrap();
                    }
                }
                if self.settings.unknown3 {
                    bytes.write_all(&vertex.unknown3).unwrap();
                }
                if self.settings.unknown4 {
                    bytes.write_all(&vertex.unknown4).unwrap();
                }
            }
        }

        let number_of_triangles: u32 = self.meshes.iter().map(|m| m.triangles.len() as u32).sum();
        bytes
            .write_u32::<LittleEndian>(number_of_triangles * 3)
            .unwrap();

        for mesh in &self.meshes {
            for triangle in &mesh.triangles {
                if vertices_total_num > u16::MAX as u32 {
                    bytes.write_u32::<LittleEndian>(triangle.0).unwrap();
                    bytes.write_u32::<LittleEndian>(triangle.1).unwrap();
                    bytes.write_u32::<LittleEndian>(triangle.2).unwrap();
                } else {
                    bytes.write_u16::<LittleEndian>(triangle.0 as u16).unwrap();
                    bytes.write_u16::<LittleEndian>(triangle.1 as u16).unwrap();
                    bytes.write_u16::<LittleEndian>(triangle.2 as u16).unwrap();
                }
            }
        }

        bytes
            .write_u32::<LittleEndian>(if self.is_skinned { 1 } else { 0 })
            .unwrap();
        bytes
            .write_u32::<LittleEndian>(self.number_of_bones)
            .unwrap();

        if self.is_skinned {
            bytes.write_all(&self.root_bone_hash_maybe).unwrap();
            for bone in &self.bones {
                bytes.write_all(&bone.data).unwrap();
            }
        }

        bytes.write_u8(self.num).unwrap();

        if self.num == 2 {
            bytes.write_all(&self.num2_data).unwrap();
        } else if self.num == 42 {
            write_string_u8_len(&mut bytes, &self.end_kind_kind);
            if self.end_kind_kind == "mesh_type" {
                bytes
                    .write_u8(self.end_kind_mesh_type.clone().into())
                    .unwrap();
                match self.end_kind_mesh_type {
                    MeshType::VariableLength => {
                        if let EndKind::MeshType(str) = &self.end_mesh_type {
                            write_string(&mut bytes, str);
                        } else {
                            unreachable!();
                        }
                    }
                    MeshType::RenderFlags => {
                        bytes.write_all(&self.render_flags_extra_data).unwrap();
                        if let EndKind::MeshType(str) = &self.end_mesh_type {
                            write_string_u8_len(&mut bytes, str);
                        } else {
                            unreachable!();
                        }
                    }
                    MeshType::SideCap
                    | MeshType::PlayerTunnel
                    | MeshType::StadiumRoof
                    | MeshType::Glasses
                    | MeshType::RearCap
                    | MeshType::BodyPart => {
                        if let EndKind::MeshType(str) = &self.end_mesh_type {
                            bytes.write_all(str.as_bytes()).unwrap();
                        } else {
                            unreachable!();
                        }
                    }
                }
            } else if self.end_kind_kind == "is_banner" {
                if let EndKind::IsBanner(value) = self.end_mesh_type {
                    bytes.write_u8(value).unwrap();
                }
            } else if self.end_kind_kind == "is_comp_banner" {
                if let EndKind::IsCompBanner(value) = self.end_mesh_type {
                    bytes.write_u8(value).unwrap();
                }
            } else if self.end_kind_kind == "is_match_ball" {
                if let EndKind::IsMatchBall(value) = self.end_mesh_type {
                    bytes.write_u8(value).unwrap();
                }
            } else if self.end_kind_kind == "is_team_logo" {
                if let EndKind::IsTeamLogo(value) = self.end_mesh_type {
                    bytes.write_u8(value).unwrap();
                }
            }
        }

        bytes
            .write_u32::<LittleEndian>(self.instances.len() as u32)
            .unwrap();

        for instance in &self.instances {
            bytes.write_u32::<LittleEndian>(instance.kind).unwrap();

            for v in &instance.matrix_values_and_unknown {
                bytes.write_f32::<LittleEndian>(*v).unwrap();
            }

            for b in &instance.unknown {
                bytes.write_u8(*b).unwrap();
            }

            bytes.write_u32::<LittleEndian>(instance.num1).unwrap();

            for position in &instance.positions {
                bytes.write_f32::<LittleEndian>(position.x).unwrap();
                bytes.write_f32::<LittleEndian>(position.y).unwrap();
                bytes.write_f32::<LittleEndian>(position.z).unwrap();
            }

            write_string(&mut bytes, &instance.name);
            write_string(&mut bytes, &instance.path);
        }

        bytes.write_all("EHSM".as_bytes()).unwrap();

        bytes.flush().unwrap();
    }
}
