use crate::show_error_dialog;

use obj_exporter::{Geometry, ObjSet, Object, Primitive, Shape, TVertex, Vertex};
use std::{env, fs, path::PathBuf};

use sia_parser::model::Model;
use sia_parser::texture::TextureType;

pub(crate) fn save_as_obj(model: &Model, texture_dir: &Option<PathBuf>) {
    let mut objects = Vec::new();
    for mesh in model.meshes.values().collect::<Vec<_>>() {
        let object = Object {
            name: model.name.to_owned(),
            vertices: mesh
                .vertices
                .iter()
                .map(|v| v.position)
                .map(|v| Vertex {
                    x: v.x.into(),
                    y: v.y.into(),
                    z: v.z.into(),
                })
                .collect(),
            tex_vertices: mesh
                .vertices
                .iter()
                .map(|v| v.uv)
                .map(|uv| TVertex {
                    u: uv.x.into(),
                    v: (uv.y - 1f32).abs().into(),
                    w: 0.0,
                })
                .collect(),
            normals: vec![],
            geometry: vec![Geometry {
                material_name: Some(model.name.to_owned()),
                shapes: mesh
                    .triangles
                    .iter()
                    .map(|t| Shape {
                        primitive: Primitive::Triangle(
                            (t.0 as usize, Some(t.0 as usize), None),
                            (t.1 as usize, Some(t.1 as usize), None),
                            (t.2 as usize, Some(t.2 as usize), None),
                        ),
                        groups: vec![],
                        smoothing_groups: vec![0],
                    })
                    .collect(),
            }],
        };
        objects.push(object);
    }
    let set = ObjSet {
        material_library: None,
        objects,
    };

    let obj_folder_path = env::current_dir()
        .unwrap()
        .join(format!("objs/{}", model.name));
    match fs::create_dir_all(&obj_folder_path) {
        Ok(_) => {
            match obj_exporter::export_to_file(
                &set,
                obj_folder_path.join(format!("{}{}", model.name, ".obj")),
            ) {
                Ok(_) => {
                    if let Some(texture_dir) = &texture_dir {
                        let textures = model
                            .meshes
                            .values()
                            .collect::<Vec<_>>()
                            .iter()
                            .flat_map(|m| &m.materials)
                            .into_iter()
                            .flat_map(|m| &m.textures)
                            .collect::<Vec<_>>();
                        for texture in textures {
                            let mut source_path = texture_dir.join(&texture.name);
                            source_path.set_extension("dds");

                            match texture.id {
                                TextureType::RoughnessMetallicAmbientOcclusion => {
                                    {
                                        let mut roughness = PathBuf::from(format!(
                                            "{}{}",
                                            texture
                                                .name
                                                .split('_')
                                                .collect::<Vec<_>>()
                                                .first()
                                                .cloned()
                                                .unwrap(),
                                            "_roughness"
                                        ));
                                        roughness.set_extension("tga");

                                        if let Ok(source_img) = image::open(&source_path) {
                                            let mut source_img = source_img.to_rgba8();
                                            for pixel in source_img.pixels_mut() {
                                                let image::Rgba(data) = *pixel;
                                                *pixel =
                                                    image::Rgba([data[0], data[0], data[0], 255]);
                                            }
                                            source_img
                                                .save(
                                                    obj_folder_path
                                                        .join(roughness.file_name().unwrap()),
                                                )
                                                .unwrap();
                                        }
                                    }
                                    {
                                        let mut metallic = PathBuf::from(format!(
                                            "{}{}",
                                            texture
                                                .name
                                                .split('_')
                                                .collect::<Vec<_>>()
                                                .first()
                                                .cloned()
                                                .unwrap(),
                                            "_metallic"
                                        ));
                                        metallic.set_extension("tga");

                                        if let Ok(source_img) = image::open(&source_path) {
                                            let mut source_img = source_img.to_rgba8();
                                            for pixel in source_img.pixels_mut() {
                                                let image::Rgba(data) = *pixel;
                                                *pixel =
                                                    image::Rgba([data[1], data[1], data[1], 255]);
                                            }
                                            source_img
                                                .save(
                                                    obj_folder_path
                                                        .join(metallic.file_name().unwrap()),
                                                )
                                                .unwrap();
                                        }
                                    }
                                    {
                                        let mut ambient_occlusion = PathBuf::from(format!(
                                            "{}{}",
                                            texture
                                                .name
                                                .split('_')
                                                .collect::<Vec<_>>()
                                                .first()
                                                .cloned()
                                                .unwrap(),
                                            "_ambient_occlusion"
                                        ));
                                        ambient_occlusion.set_extension("tga");

                                        if let Ok(source_img) = image::open(&source_path) {
                                            let mut source_img = source_img.to_rgba8();
                                            for pixel in source_img.pixels_mut() {
                                                let image::Rgba(data) = *pixel;
                                                *pixel =
                                                    image::Rgba([data[3], data[3], data[3], 255]);
                                            }
                                            source_img
                                                .save(
                                                    obj_folder_path.join(
                                                        ambient_occlusion.file_name().unwrap(),
                                                    ),
                                                )
                                                .unwrap();
                                        }
                                    }
                                }
                                TextureType::Normal => {
                                    let mut normal = PathBuf::from(format!(
                                        "{}{}",
                                        texture
                                            .name
                                            .split('_')
                                            .collect::<Vec<_>>()
                                            .first()
                                            .cloned()
                                            .unwrap(),
                                        "_normal"
                                    ));
                                    normal.set_extension("tga");

                                    if let Ok(source_img) = image::open(&source_path) {
                                        let mut source_img = source_img.to_rgba8();
                                        for pixel in source_img.pixels_mut() {
                                            let image::Rgba(data) = *pixel;
                                            *pixel = image::Rgba([data[3], data[1], 255, 255]);
                                        }
                                        source_img
                                            .save(obj_folder_path.join(normal.file_name().unwrap()))
                                            .unwrap();
                                    }
                                }
                                _ => {
                                    let mut target_path = PathBuf::from(&texture.name);
                                    target_path.set_extension("tga");

                                    if let Ok(source_img) = image::open(source_path) {
                                        source_img
                                            .save(
                                                obj_folder_path
                                                    .join(target_path.file_name().unwrap()),
                                            )
                                            .unwrap();
                                    }
                                }
                            }
                        }
                    }
                }
                Err(e) => {
                    show_error_dialog("Obj", &format!("Failed to save obj\n{}", e));
                }
            }
        }
        Err(e) => {
            show_error_dialog("Obj Folder", &format!("Failed to create obj folder\n{}", e));
        }
    }
}
