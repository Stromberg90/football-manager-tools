#![feature(get_mut_unchecked)]

use kiss3d::light::Light;
use kiss3d::resource::{Mesh, TextureManager, TextureWrapping};
use kiss3d::{camera::ArcBall, event::WindowEvent, window::Window};
use nalgebra::{Point2, Point3, Vector3};
use native_dialog::*;
use nfd2::Response;
use std::{
    cell::RefCell,
    env, fs,
    path::{Path, PathBuf},
    rc::Rc,
};

use obj_exporter::{Geometry, ObjSet, Object, Primitive, Shape, TVertex, Vertex};
use sia_parser::texture::TextureType;

struct Options {
    wireframe: bool,
}

impl Options {
    fn new() -> Self {
        Options { wireframe: false }
    }
}

fn show_error_dialog(title: &str, text: &str) {
    let _ = MessageAlert {
        title,
        text,
        typ: MessageType::Error,
    }
    .show();
}

fn show_info_dialog(title: &str, text: &str) {
    let _ = MessageAlert {
        title,
        text,
        typ: MessageType::Info,
    }
    .show();
}

fn main() {
    let mut window = Window::new("Football Manager Model Viewer");
    let mut scene_nodes = Vec::new();
    let mut options = Options::new();

    window.set_light(Light::StickToCamera);
    let mut camera = ArcBall::new(Point3::new(0.0f32, 10.0, -10.0), Point3::origin());
    camera.rebind_drag_button(Some(kiss3d::event::MouseButton::Button3));

    let mut texture_manager = TextureManager::new();
    let mut texture_dir: Option<PathBuf> = None;

    let mut model = None;

    match nfd2::open_file_dialog(None, None).expect("Couldn't open file") {
        Response::Okay(filepath) => {
            if filepath.extension().unwrap() == "sia" {
                model = Some(sia_parser::parse(filepath));
                match model.as_ref().unwrap() {
                    Ok(model) => {
                        show_info_dialog(
                            "Texture Folder",
                            "Please select simatchviewer-pc folder for texture support",
                        );
                        if let Ok(Response::Okay(folder)) = nfd2::open_pick_folder(None) {
                            texture_dir = Some(folder);
                        }

                        for mesh in &model.meshes {
                            let mut coords = Vec::new();
                            let mut normals = Vec::new();
                            let mut triangles: Vec<Point3<u16>> = Vec::new();
                            let mut uvs = Vec::new();

                            for vertex in &mesh.vertices {
                                coords.push(Point3::from(vertex.position));
                                normals.push(Vector3::from(vertex.normals));
                                uvs.push(Point2::from(vertex.uv));
                            }

                            for triangle in &mesh.triangles {
                                triangles.push(Point3::new(
                                    triangle.0 as u16,
                                    triangle.1 as u16,
                                    triangle.2 as u16,
                                ));
                            }

                            let mut c = window.add_mesh(
                                Rc::new(RefCell::new(Mesh::new(
                                    coords,
                                    triangles,
                                    Some(normals),
                                    Some(uvs),
                                    false,
                                ))),
                                Vector3::new(1.0, 1.0, 1.0),
                            );
                            c.reorient(
                                &Point3::new(0.0, 0.0, 0.0),
                                &Point3::new(0.0, 1.0, 0.0),
                                &Vector3::new(1.0, 0.0, 0.0),
                            );
                            c.enable_backface_culling(true);

                            if let Some(texture_dir) = &texture_dir {
                                if let Some(material) = mesh.materials.get(0) {
                                    if let Some(diffuse) = material.textures.get(0) {
                                        let diffuse_relative_path = &diffuse.name;
                                        let mut diffuse_absolute_path =
                                            texture_dir.join(diffuse_relative_path);
                                        diffuse_absolute_path.set_extension("dds");

                                        if let Ok(texture) = image::open(diffuse_absolute_path) {
                                            let mut texture_resource = texture_manager
                                                .add_image(texture, diffuse_relative_path);

                                            unsafe {
                                                let text =
                                                    Rc::get_mut_unchecked(&mut texture_resource);
                                                text.set_wrapping_s(TextureWrapping::Repeat);
                                                text.set_wrapping_t(TextureWrapping::Repeat);
                                            }
                                            c.set_texture(texture_resource);
                                        }
                                    }
                                }
                            }

                            scene_nodes.push(c);
                        }
                    }
                    Err(e) => {
                        eprintln!("Error: {}", e);
                        std::process::exit(1)
                    }
                }
            }
        }
        _ => {}
    }

    while window.render_with_camera(&mut camera) {
        for mut event in window.events().iter() {
            match event.value {
                WindowEvent::Key(kiss3d::event::Key::S, kiss3d::event::Action::Press, modifers) => {
                    if modifers.contains(kiss3d::event::Modifiers::Control) {
                        let mut objects = Vec::new();
                        if let Ok(model) = model.as_ref().unwrap() {
                            for mesh in &model.meshes {
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
                                                    .iter()
                                                    .flat_map(|m| &m.materials)
                                                    .into_iter()
                                                    .flat_map(|m| &m.textures)
                                                    .collect::<Vec<_>>();
                                                for texture in textures {
                                                    let mut source_path =
                                                        texture_dir.join(&texture.name);
                                                    source_path.set_extension("dds");

                                                    match texture.id {
                                                        TextureType::RoughnessMetallicAmbientOcclusion => {
                                                            {
                                                                let mut roughness = PathBuf::from(format!("{}{}", texture.name.split('_').collect::<Vec<_>>().first().cloned().unwrap(), "_roughness"));
                                                                roughness.set_extension("tga");

                                                                if let Ok(source_img) =
                                                                image::open(&source_path) {
                                                                    let mut source_img =
                                                                        source_img.to_rgba();
                                                                    for pixel in source_img.pixels_mut() {
                                                                        let image::Rgba(data) = *pixel;
                                                                        *pixel = image::Rgba([
                                                                            data[0], data[0], data[0], 255,
                                                                        ]);
                                                                    }
                                                                    source_img
                                                                        .save(
                                                                            obj_folder_path.join(
                                                                                roughness
                                                                                    .file_name()
                                                                                    .unwrap(),
                                                                            ),
                                                                        )
                                                                        .unwrap();
                                                                }
                                                            }
                                                            {
                                                                let mut metallic = PathBuf::from(format!("{}{}", texture.name.split('_').collect::<Vec<_>>().first().cloned().unwrap(), "_metallic"));
                                                                metallic.set_extension("tga");

                                                                if let Ok(source_img) =
                                                                image::open(&source_path) {
                                                                    let mut source_img =
                                                                    source_img.to_rgba();
                                                                    for pixel in source_img.pixels_mut() {
                                                                        let image::Rgba(data) = *pixel;
                                                                        *pixel = image::Rgba([
                                                                            data[1], data[1], data[1], 255,
                                                                            ]);
                                                                        }
                                                                        source_img
                                                                        .save(
                                                                            obj_folder_path.join(
                                                                                metallic
                                                                                .file_name()
                                                                                .unwrap(),
                                                                            ),
                                                                        )
                                                                        .unwrap();
                                                                    }
                                                            }
                                                            {
                                                                let mut ambient_occlusion = PathBuf::from(format!("{}{}", texture.name.split('_').collect::<Vec<_>>().first().cloned().unwrap(), "_ambient_occlusion"));
                                                                ambient_occlusion.set_extension("tga");

                                                                if let Ok(source_img) =
                                                                image::open(&source_path) {
                                                                    let mut source_img =
                                                                        source_img.to_rgba();
                                                                    for pixel in source_img.pixels_mut() {
                                                                        let image::Rgba(data) = *pixel;
                                                                        *pixel = image::Rgba([
                                                                            data[3], data[3], data[3], 255,
                                                                        ]);
                                                                    }
                                                                    source_img
                                                                        .save(
                                                                            obj_folder_path.join(
                                                                                ambient_occlusion
                                                                                    .file_name()
                                                                                    .unwrap(),
                                                                            ),
                                                                        )
                                                                        .unwrap();
                                                                }
                                                            }
                                                        },
                                                        TextureType::Normal => {
                                                            let mut normal = PathBuf::from(format!("{}{}", texture.name.split('_').collect::<Vec<_>>().first().cloned().unwrap(), "_normal"));
                                                            normal.set_extension("tga");

                                                            if let Ok(source_img) =
                                                            image::open(&source_path) {
                                                                let mut source_img =
                                                                    source_img.to_rgba();
                                                                for pixel in source_img.pixels_mut() {
                                                                    let image::Rgba(data) = *pixel;
                                                                    *pixel = image::Rgba([
                                                                        data[3], data[1], 255, 255,
                                                                    ]);
                                                                }
                                                                source_img
                                                                    .save(
                                                                        obj_folder_path.join(
                                                                            normal
                                                                                .file_name()
                                                                                .unwrap(),
                                                                        ),
                                                                    )
                                                                    .unwrap();
                                                            }
                                                        },
                                                        _ => {
                                                            let mut target_path =
                                                                PathBuf::from(&texture.name);
                                                            target_path.set_extension("tga");

                                                            if let Ok(source_img) =
                                                                image::open(source_path) {

                                                                    source_img
                                                                        .save(
                                                                            obj_folder_path.join(
                                                                                target_path
                                                                                    .file_name()
                                                                                    .unwrap(),
                                                                            ),
                                                                        )
                                                                        .unwrap();
                                                                }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        Err(e) => {
                                            show_error_dialog(
                                                "Obj",
                                                &format!("Failed to save obj\n{}", e),
                                            );
                                        }
                                    }
                                }
                                Err(e) => {
                                    show_error_dialog(
                                        "Obj Folder",
                                        &format!("Failed to create obj folder\n{}", e),
                                    );
                                }
                            }
                        }
                    }
                }
                WindowEvent::Key(kiss3d::event::Key::W, kiss3d::event::Action::Press, modifers) => {
                    if modifers.contains(kiss3d::event::Modifiers::Shift) {
                        if options.wireframe {
                            for node in &mut scene_nodes {
                                node.set_points_size(0.0);
                                node.set_lines_width(0.0);
                                node.set_surface_rendering_activation(true);
                            }
                            options.wireframe = false;
                        } else {
                            for node in &mut scene_nodes {
                                node.set_points_size(4.0);
                                node.set_lines_width(1.0);
                                node.set_surface_rendering_activation(false);
                            }
                            options.wireframe = true;
                        }
                    }
                }
                WindowEvent::Scroll(_, y_shift, _) => {
                    camera.set_dist(camera.dist() - (y_shift as f32) * 0.1);
                    event.inhibited = true
                }
                _ => {}
            }
        }
    }
}
