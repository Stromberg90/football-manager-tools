
mod egui_helpers;
use sia_parser::types::EndKind;
use sia_parser::types::MeshType;
use sia_parser::types::SiaFile;
use sia_parser::types::SiaTriangle;
use sia_parser::types::SiaVector2;
use sia_parser::types::SiaVertex;
use sia_parser::types::TextureKind;
use std::sync::LazyLock;
use eframe::egui;
use eframe::egui::mutex::Mutex;
use egui_helpers::byte_array_helper;
use egui_helpers::numeric_helper;
use egui_helpers::text_edit_helper;
use egui_helpers::vector2_helper;
use egui_helpers::vector3_helper;

static SIA_FILE: LazyLock<Mutex<Option<SiaFile>>> = LazyLock::new(|| Mutex::new(None));

fn main() -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([900.0, 900.0]),
        ..Default::default()
    };

    eframe::run_simple_native("Sia Editor", options, move |ctx, _frame| {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.horizontal(|ui| {
                if ui.button("Load").clicked() {
                    if let Some(path) = rfd::FileDialog::new()
                        .add_filter("sia", &["sia"])
                        .pick_file() {
                            let _ = SIA_FILE.lock().insert(sia_parser::from_path(path));
                        }
                }
                if SIA_FILE.lock().is_some() && ui.button("Save As").clicked() {
                    if let Some(path) = rfd::FileDialog::new()
                        .add_filter("sia", &["sia"]).save_file() {
                            SIA_FILE.lock().as_ref().unwrap().write_to(path);
                    }
                }
            });
            if let Some(sia_file) = SIA_FILE.lock().as_mut() {
                egui::ScrollArea::new([false, true]).show(ui, |ui| {
                numeric_helper(ui, "version_maybe", &mut sia_file.version_maybe);
                text_edit_helper(ui, "name", &mut sia_file.name);
                byte_array_helper(ui, "unknown1", &mut sia_file.unknown1);
                numeric_helper(ui, "maybe_scale", &mut sia_file.maybe_scale);
                ui.collapsing("bounding_box", |ui| {
                    for value in &mut sia_file.bounding_box {
                        ui.add(egui::DragValue::new(value).speed(0.01));
                    }
                });
                numeric_helper(ui, "objects_num", &mut sia_file.objects_num);
                ui.collapsing("meshes", |ui| {
                    for (mesh_ui_id, mesh) in &mut sia_file.meshes.iter_mut().enumerate() {
                        ui.push_id(mesh_ui_id, |ui| {
                            ui.collapsing("mesh", |ui| {
                                numeric_helper(ui, "vertex_offset", &mut mesh.vertex_offset);
                                numeric_helper(ui, "triangle_offset", &mut mesh.triangle_offset);
                                numeric_helper(ui, "id", &mut mesh.id);
                                byte_array_helper(ui, "unknown", &mut mesh.unknown);
                                byte_array_helper(ui, "maybe_hash", &mut mesh.maybe_hash);
                                byte_array_helper(ui, "unknown1", &mut mesh.unknown1);
                                byte_array_helper(ui, "unknown2", &mut mesh.unknown2);
                                byte_array_helper(ui, "unknown3", &mut mesh.unknown3);
                                byte_array_helper(ui, "unknown4", &mut mesh.unknown4);
                                text_edit_helper(ui, "material_type", &mut mesh.material_type);
                                ui.collapsing("materials", |ui| {
                                    for (material_ui_id, material) in &mut mesh.materials.iter_mut().enumerate() {
                                        ui.push_id(material_ui_id, |ui| {
                                            text_edit_helper(ui, "kind", &mut material.kind);
                                            numeric_helper(ui, "texture_num", &mut material.texture_num);
                                            ui.collapsing("textures", |ui| {
                                                for (texture_ui_id, texture) in &mut material.textures.iter_mut().enumerate() {
                                                    ui.horizontal(|ui| {
                                                        ui.label("kind");
                                                        egui::ComboBox::from_id_salt(texture_ui_id)
                                                            .selected_text(format!("{:?}", texture.kind))
                                                            .show_ui(ui, |ui| {
                                                                ui.selectable_value(
                                                                    &mut texture.kind,
                                                                    TextureKind::Albedo,
                                                                    "Albedo",
                                                                );
                                                                ui.selectable_value(
                                                                    &mut texture.kind,
                                                                    TextureKind::RoughnessMetallicAmbientOcclusion,
                                                                    "RoughnessMetallicAmbientOcclusion",
                                                                );
                                                                ui.selectable_value(
                                                                    &mut texture.kind,
                                                                    TextureKind::Normal,
                                                                    "Normal",
                                                                );
                                                                ui.selectable_value(
                                                                    &mut texture.kind,
                                                                    TextureKind::Mask,
                                                                    "Mask",
                                                                );
                                                                ui.selectable_value(
                                                                    &mut texture.kind,
                                                                    TextureKind::Lightmap,
                                                                    "Lightmap",
                                                                );
                                                                ui.selectable_value(
                                                                    &mut texture.kind,
                                                                    TextureKind::Flowmap,
                                                                    "Flowmap",
                                                                );
                                                            });
                                                    });
                                                    text_edit_helper(ui, "path", &mut texture.path);
                                                }
                                            });
                                        });
                                    }                        
                                });
                                ui.collapsing("vertices", |ui| {
                                    if ui.button("clear").clicked() {
                                        mesh.vertices.clear();
                                    }
                                    if ui.button("add").clicked() {
                                        let mut vertex = SiaVertex { 
                                            texture_coords: vec![SiaVector2::default()],
                                            ..Default::default() 
                                        };
                                        if sia_file.settings.tangent {
                                            vertex.tangent_unknown = [0, 0, 128, 63];
                                        }
                                        if sia_file.settings.unknown4 {
                                            vertex.unknown4 = [255, 255, 255, 255];
                                        }
                                        mesh.vertices.push(vertex);
                                    }
                                    for (vertex_ui_id, vertex) in mesh.vertices.iter_mut().enumerate() {
                                        ui.push_id(vertex_ui_id, |ui| {
                                            ui.collapsing("vertex", |ui   | {
                                                vector3_helper(ui, "position", &mut vertex.position);
                                                vector3_helper(ui, "normal", &mut vertex.normal);
                                                ui.collapsing("texture_coords", |ui| {
                                                    if ui.button("add").clicked() {
                                                        vertex.texture_coords.push(SiaVector2::default());
                                                    }
                                                    for (texture_coords_ui_id, texture_coord) in vertex.texture_coords.iter_mut().enumerate() {
                                                        ui.push_id(texture_coords_ui_id, |ui| {
                                                            vector2_helper(ui, "texture_coord", texture_coord);
                                                        });
                                                    }
                                                });
                                                vector3_helper(ui, "tangent", &mut vertex.tangent);
                                                byte_array_helper(ui, "unknown1", &mut vertex.unknown1);
                                                byte_array_helper(ui, "tangent_unknown", &mut vertex.tangent_unknown);
                                                byte_array_helper(ui, "unknown3", &mut vertex.unknown3);
                                                byte_array_helper(ui, "unknown4", &mut vertex.unknown4);
                                                if !vertex.bone.ids.is_empty() {
                                                    ui.collapsing("bone", |ui| {
                                                        byte_array_helper(ui, "ids", &mut vertex.bone.ids);
                                                        ui.collapsing("influences", |ui| {
                                                            ui.horizontal_wrapped(|ui| {
                                                                for value in &mut vertex.bone.influences {
                                                                    ui.add(egui::DragValue::new(value));
                                                                }
                                                            });
                                                        });
                                                    });
                                                }
                                            });
                                        });
                                    }
                                });
                                ui.collapsing("triangles", |ui| {
                                    if ui.button("clear").clicked() {
                                        mesh.triangles.clear();
                                    }
                                    if ui.button("add").clicked() {
                                        mesh.triangles.push(SiaTriangle(0, 0, 0));
                                    }
                                    for (triangle_ui_id, triangle) in mesh.triangles.iter_mut().enumerate() {
                                        ui.push_id(triangle_ui_id, |ui| {
                                            ui.collapsing("triangle", |ui| {
                                                numeric_helper(ui, "0", &mut triangle.0);
                                                numeric_helper(ui, "1", &mut triangle.1);
                                                numeric_helper(ui, "2", &mut triangle.2);
                                            });
                                        }); 
                                    }
                                });
                            });
                        });
                    }
                });
                numeric_helper(ui, "meshes_num", &mut sia_file.meshes_num);
                ui.collapsing("settings", |ui| {
                    ui.checkbox(&mut sia_file.settings.position, "position");
                    ui.checkbox(&mut sia_file.settings.normal, "normal");
                    ui.checkbox(&mut sia_file.settings.uv_set1, "uv_set1");
                    ui.checkbox(&mut sia_file.settings.uv_set2, "uv_set2");
                    ui.checkbox(&mut sia_file.settings.unknown1, "unknown1");
                    ui.checkbox(&mut sia_file.settings.tangent, "tangent");
                    ui.checkbox(&mut sia_file.settings.skinned, "skinned");
                    ui.checkbox(&mut sia_file.settings.unknown2, "unknown2");
                    ui.checkbox(&mut sia_file.settings.unknown3, "unknown3");
                    ui.checkbox(&mut sia_file.settings.unknown4, "unknown4");
                });
                ui.checkbox(&mut sia_file.is_skinned, "is_skinned");
                numeric_helper(ui, "number_of_bones", &mut sia_file.number_of_bones);
                byte_array_helper(ui, "root_bone_hash_maybe", &mut sia_file.root_bone_hash_maybe);
                ui.collapsing("bones", |ui| {
                    for (bone_ui_id, bone) in &mut sia_file.bones.iter_mut().enumerate() {
                        ui.push_id(bone_ui_id, |ui|{
                            byte_array_helper(ui, "bone", &mut bone.data);
                        });
                    }
                });
                numeric_helper(ui, "num", &mut sia_file.num);
                byte_array_helper(ui, "num2_data", &mut sia_file.num2_data);
                if !sia_file.end_kind_kind.is_empty() {
                    text_edit_helper(ui, "end_kind_kind", &mut sia_file.end_kind_kind);
                    ui.horizontal(|ui| {
                        ui.label("end_kind_mesh_type");
                        egui::ComboBox::from_id_salt("end_kind_mesh_type")
                            .selected_text(format!("{:?}", sia_file.end_kind_mesh_type))
                            .show_ui(ui, |ui| {
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::RenderFlags,
                                    "RenderFlags",
                                );
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::VariableLength,
                                    "VariableLength",
                                );
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::BodyPart,
                                    "BodyPart",
                                );
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::RearCap,
                                    "RearCap",
                                );
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::Glasses,
                                    "Glasses",
                                );
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::StadiumRoof,
                                    "StadiumRoof",
                                );
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::PlayerTunnel,
                                    "PlayerTunnel",
                                );
                                ui.selectable_value(
                                    &mut sia_file.end_kind_mesh_type,
                                    MeshType::SideCap,
                                    "SideCap",
                                );
                        });
                    });
                    byte_array_helper(ui, "render_flags_extra_data", &mut sia_file.render_flags_extra_data);
                }
                ui.horizontal(|ui| {
                    ui.label("end_mesh_type");
                    egui::ComboBox::from_id_salt("end_mesh_type")
                        .selected_text(format!("{:?}", sia_file.end_mesh_type))
                        .show_ui(ui, |ui| {
                            ui.selectable_value(
                                &mut sia_file.end_mesh_type,
                                EndKind::Unknown,
                                "Unknown",
                            );
                            ui.selectable_value(
                                &mut sia_file.end_mesh_type,
                                EndKind::MeshType(String::new()),
                                "MeshType",
                            );
                            ui.selectable_value(
                                &mut sia_file.end_mesh_type,
                                EndKind::IsBanner(1),
                                "IsBanner",
                            );
                            ui.selectable_value(
                                &mut sia_file.end_mesh_type,
                                EndKind::IsCompBanner(1),
                                "IsCompBanner",
                            );
                            ui.selectable_value(
                                &mut sia_file.end_mesh_type,
                                EndKind::IsMatchBall(1),
                                "IsMatchBall",
                            );
                            ui.selectable_value(
                                &mut sia_file.end_mesh_type,
                                EndKind::IsTeamLogo(1),
                                "IsTeamLogo",
                            );
                    });
                });
                if !sia_file.instances.is_empty() {
                    let mut instance_remove_index = None;
                    ui.collapsing("instances", |ui| {
                        for (instance_ui_id, instance) in &mut sia_file.instances.iter_mut().enumerate() {
                            ui.push_id(instance_ui_id, |ui|{
                                ui.horizontal(|ui| {
                                    if ui.button("-").clicked() {
                                        instance_remove_index = Some(instance_ui_id);
                                    }
                                    ui.collapsing("instance", |ui| {
                                        numeric_helper(ui, "kind", &mut instance.kind);
                                        ui.collapsing("matrix_values_and_unknown", |ui|{
                                            for value in &mut instance.matrix_values_and_unknown {
                                                ui.add(egui::DragValue::new(value));
                                            }
                                        });
                                        ui.collapsing("unknown", |ui|{
                                            for value in &mut instance.unknown {
                                                ui.add(egui::DragValue::new(value));
                                            }
                                        });
                                        numeric_helper(ui, "num1", &mut instance.num1);
                                        ui.collapsing("positions", |ui| {
                                            for position in &mut instance.positions {
                                                ui.horizontal(|ui| {
                                                    ui.label("x");
                                                    ui.add(egui::DragValue::new(&mut position.x).speed(0.01));
                                                });
                                                ui.horizontal(|ui| {
                                                    ui.label("y");
                                                    ui.add(egui::DragValue::new(&mut position.y).speed(0.01));
                                                });
                                                ui.horizontal(|ui| {
                                                    ui.label("z");
                                                    ui.add(egui::DragValue::new(&mut position.z).speed(0.01));
                                                });
                                            };
                                        });
                                        text_edit_helper(ui, "name", &mut instance.name);
                                        text_edit_helper(ui, "path", &mut instance.path);
                                    });
                                });
                            });
                        }
                        if let Some(index) = instance_remove_index {
                            sia_file.instances.remove(index);
                        }
                    });
                }
            });
            }
        });
    })
}
